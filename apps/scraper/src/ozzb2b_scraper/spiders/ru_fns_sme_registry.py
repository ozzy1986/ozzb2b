"""Official FNS SME registry bulk importer.

The source is the Federal Tax Service open-data dataset:
https://www.nalog.gov.ru/opendata/7707329152-rsmp

It is a local-file spider by design. Download and prepare the official ZIP/XML
off the production VPS, then point ``OZZB2B_FNS_SME_DATA_PATH`` at the file.
This keeps production imports predictable and avoids live crawling pressure.
"""

from __future__ import annotations

import json
import zipfile
from collections.abc import AsyncIterator, Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from defusedxml import ElementTree
from ozzb2b_scraper.config import get_settings
from ozzb2b_scraper.models import ScrapedProvider
from ozzb2b_scraper.spiders.base import Spider, SpiderContext

SOURCE = "ru-fns-sme-registry"

FNS_SME_SOURCE_URL = "https://www.nalog.gov.ru/opendata/7707329152-rsmp"

REGION_TO_CITY: dict[str, str] = {
    "77": "Moscow",
    "78": "Saint Petersburg",
    "54": "Novosibirsk",
    "66": "Yekaterinburg",
    "16": "Kazan",
    "52": "Nizhny Novgorod",
    "63": "Samara",
    "73": "Ulyanovsk",
    "36": "Voronezh",
    "55": "Omsk",
    "43": "Kirov",
    "59": "Perm",
    "61": "Rostov-on-Don",
    "23": "Krasnodar",
}


@dataclass(frozen=True)
class OkvedMapping:
    category_slugs: tuple[str, ...]
    matched_code: str
    matched_name: str | None


@dataclass(frozen=True)
class FnsSmeRecord:
    source_id: str
    display_name: str
    legal_name: str | None
    legal_form_code: str
    tax_id: str
    registration_number: str
    region_code: str
    city_name: str | None
    okved_code: str
    okved_name: str | None
    category_slugs: tuple[str, ...]
    included_at: str | None
    sme_subject_kind: str | None
    sme_category: str | None
    employee_count: int | None


def map_okved_to_categories(code: str, name: str | None = None) -> OkvedMapping | None:
    """Map Russian OKVED codes to existing ozzb2b category slugs."""

    normalized = code.strip()
    if not normalized:
        return None

    slugs: tuple[str, ...] | None = None
    if normalized.startswith("62."):
        slugs = ("it", "software-development")
    elif normalized.startswith("63.1"):
        slugs = ("it", "data-analytics")
    elif normalized.startswith("58.2"):
        slugs = ("it", "software-development")
    elif normalized == "74.10":
        slugs = ("it", "ui-ux-design")
    elif normalized.startswith("69.20"):
        slugs = ("accounting", "bookkeeping", "tax-advisory")
    elif normalized.startswith("69.10"):
        slugs = ("legal", "corporate-law", "contracts")
    elif normalized.startswith("73.11") or normalized.startswith("73.12"):
        slugs = ("marketing", "paid-media")
    elif normalized.startswith("73."):
        slugs = ("marketing",)
    elif normalized.startswith("70.21"):
        slugs = ("marketing", "pr")
    elif normalized.startswith("78.10"):
        slugs = ("hr", "recruiting")
    elif normalized.startswith("78.20") or normalized.startswith("78.30"):
        slugs = ("hr", "staffing")
    elif normalized.startswith("85.42"):
        slugs = ("hr", "training")

    if slugs is None:
        return None
    return OkvedMapping(category_slugs=slugs, matched_code=normalized, matched_name=name)


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _full_name_from_ip(node: ElementTree.Element) -> str | None:
    fio = node.find("ФИОИП")
    if fio is None:
        return None
    parts = [
        _clean_text(fio.attrib.get("Фамилия")),
        _clean_text(fio.attrib.get("Имя")),
        _clean_text(fio.attrib.get("Отчество")),
    ]
    name = " ".join(part for part in parts if part)
    return f"ИП {name}" if name else None


def _infer_legal_form(name: str, *, is_ip: bool) -> str:
    if is_ip:
        return "IP"
    upper = name.upper()
    if "ПАО" in upper:
        return "PAO"
    if "АО" in upper or "АКЦИОНЕРНОЕ ОБЩЕСТВО" in upper:
        return "AO"
    if "ООО" in upper or "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ" in upper:
        return "OOO"
    return "UNK"


def _city_from_location(location: ElementTree.Element | None) -> tuple[str, str | None]:
    if location is None:
        return "", None
    region_code = location.attrib.get("КодРегион", "")
    for tag in ("Город", "НаселПункт"):
        node = location.find(tag)
        if node is not None:
            city = _clean_text(node.attrib.get("Наим"))
            if city:
                return region_code, city
    return region_code, REGION_TO_CITY.get(region_code)


def _okved_candidates(document: ElementTree.Element) -> Iterable[tuple[str, str | None]]:
    okved = document.find("СвОКВЭД")
    if okved is None:
        return ()
    nodes: list[ElementTree.Element] = []
    main = okved.find("СвОКВЭДОсн")
    if main is not None:
        nodes.append(main)
    nodes.extend(okved.findall("СвОКВЭДДоп"))
    return (
        (node.attrib.get("КодОКВЭД", ""), _clean_text(node.attrib.get("НаимОКВЭД")))
        for node in nodes
    )


def _employee_range(value: int | None) -> str | None:
    if value is None:
        return None
    if value <= 10:
        return "1-10"
    if value <= 50:
        return "11-50"
    if value <= 200:
        return "51-200"
    if value <= 500:
        return "200-500"
    if value <= 1000:
        return "500-1000"
    return "1000+"


def parse_document(document: ElementTree.Element) -> FnsSmeRecord | None:
    org = document.find("ОргВклМСП")
    ip = document.find("ИПВклМСП")
    if org is None and ip is None:
        return None

    if org is not None:
        legal_name = _clean_text(org.attrib["НаимОрг"])
        display_name = _clean_text(org.attrib.get("НаимОргСокр")) or legal_name
        tax_id = org.attrib["ИННЮЛ"]
        registration_number = org.attrib["ОГРН"]
        is_ip = False
    else:
        if ip is None:
            return None
        display_name = _full_name_from_ip(ip)
        legal_name = display_name
        tax_id = ip.attrib["ИННФЛ"]
        registration_number = ip.attrib["ОГРНИП"]
        is_ip = True

    if not display_name or not legal_name:
        return None

    mapping = None
    for okved_code, okved_name in _okved_candidates(document):
        mapping = map_okved_to_categories(okved_code, okved_name)
        if mapping is not None:
            break
    if mapping is None:
        return None

    region_code, city_name = _city_from_location(document.find("СведМН"))
    employee_raw = document.attrib.get("ССЧР")
    employee_count = int(employee_raw) if employee_raw and employee_raw.isdigit() else None

    return FnsSmeRecord(
        source_id=tax_id,
        display_name=display_name,
        legal_name=legal_name,
        legal_form_code=_infer_legal_form(legal_name, is_ip=is_ip),
        tax_id=tax_id,
        registration_number=registration_number,
        region_code=region_code,
        city_name=city_name,
        okved_code=mapping.matched_code,
        okved_name=mapping.matched_name,
        category_slugs=mapping.category_slugs,
        included_at=document.attrib.get("ДатаВклМСП"),
        sme_subject_kind=document.attrib.get("ВидСубМСП"),
        sme_category=document.attrib.get("КатСубМСП"),
        employee_count=employee_count,
    )


def record_to_provider(record: FnsSmeRecord, now: datetime) -> ScrapedProvider:
    description = "Российская компания из единого реестра субъектов МСП ФНС."
    if record.okved_name:
        description = f"{description} Основной ОКВЭД: {record.okved_name}."
    return ScrapedProvider(
        source=SOURCE,
        source_id=record.source_id,
        source_url=FNS_SME_SOURCE_URL,
        display_name=record.display_name,
        legal_name=record.legal_name,
        description=description,
        country_code="RU",
        city_name=record.city_name,
        legal_form_code=record.legal_form_code,
        registration_number=record.registration_number,
        tax_id=record.tax_id,
        employee_count_range=_employee_range(record.employee_count),
        category_slugs=record.category_slugs,
        meta={
            "fns_sme_region_code": record.region_code,
            "fns_sme_okved_code": record.okved_code,
            "fns_sme_okved_name": record.okved_name,
            "fns_sme_included_at": record.included_at,
            "fns_sme_subject_kind": record.sme_subject_kind,
            "fns_sme_category": record.sme_category,
            "fns_sme_employee_count": record.employee_count,
        },
        fetched_at=now,
    )


def _iter_xml_documents(file_obj) -> Iterator[ElementTree.Element]:
    for _event, elem in ElementTree.iterparse(file_obj, events=("end",)):
        if elem.tag == "Документ":
            yield elem
            elem.clear()


def _iter_records_from_xml(file_obj) -> Iterator[FnsSmeRecord]:
    for document in _iter_xml_documents(file_obj):
        record = parse_document(document)
        if record is not None:
            yield record


def iter_records(path: Path) -> Iterator[FnsSmeRecord]:
    """Yield mapped records from an official XML/ZIP dump or prepared JSONL."""

    suffixes = "".join(path.suffixes).lower()
    if suffixes.endswith(".jsonl"):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                payload = json.loads(line)
                payload["category_slugs"] = tuple(payload["category_slugs"])
                yield FnsSmeRecord(**payload)
        return

    if suffixes.endswith(".xml"):
        with path.open("rb") as f:
            yield from _iter_records_from_xml(f)
        return

    if suffixes.endswith(".zip"):
        with zipfile.ZipFile(path) as zf:
            xml_names = sorted(name for name in zf.namelist() if name.lower().endswith(".xml"))
            for name in xml_names:
                with zf.open(name) as f:
                    yield from _iter_records_from_xml(f)
        return

    raise ValueError(f"unsupported FNS SME input file: {path}")


class RuFnsSmeRegistrySpider(Spider):
    source = SOURCE

    async def crawl(self, ctx: SpiderContext) -> AsyncIterator[ScrapedProvider]:
        data_path = get_settings().fns_sme_data_path
        if not data_path:
            raise RuntimeError("OZZB2B_FNS_SME_DATA_PATH must point to XML, ZIP, or JSONL data")

        now = datetime.now(tz=UTC)
        yielded = 0
        for record in iter_records(Path(data_path)):
            if ctx.limit is not None and yielded >= ctx.limit:
                break
            yield record_to_provider(record, now)
            yielded += 1


__all__ = [
    "FNS_SME_SOURCE_URL",
    "SOURCE",
    "FnsSmeRecord",
    "OkvedMapping",
    "RuFnsSmeRegistrySpider",
    "iter_records",
    "map_okved_to_categories",
    "parse_document",
    "record_to_provider",
]
