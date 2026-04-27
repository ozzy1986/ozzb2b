from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from xml.etree import ElementTree
import json
import zipfile

import pytest

from ozzb2b_scraper.http import PoliteFetcher
from ozzb2b_scraper.spiders.base import SpiderContext
import ozzb2b_scraper.spiders.ru_fns_sme_registry as fns_module
from ozzb2b_scraper.spiders.ru_fns_sme_registry import (
    FnsSmeRecord,
    RuFnsSmeRegistrySpider,
    iter_records,
    map_okved_to_categories,
    parse_document,
    record_to_provider,
)


def test_map_okved_to_existing_categories() -> None:
    assert map_okved_to_categories("62.01").category_slugs == (  # type: ignore[union-attr]
        "it",
        "software-development",
    )
    assert map_okved_to_categories("69.10").category_slugs == (  # type: ignore[union-attr]
        "legal",
        "corporate-law",
        "contracts",
    )
    assert map_okved_to_categories("73.11").category_slugs == (  # type: ignore[union-attr]
        "marketing",
        "paid-media",
    )
    assert map_okved_to_categories("69.20").category_slugs == (  # type: ignore[union-attr]
        "accounting",
        "bookkeeping",
        "tax-advisory",
    )
    assert map_okved_to_categories("78.10").category_slugs == (  # type: ignore[union-attr]
        "hr",
        "recruiting",
    )
    assert map_okved_to_categories("01.11") is None


def test_parse_fns_sme_organization_document() -> None:
    document = ElementTree.fromstring(
        """
        <Документ ИдДок="1" ДатаСост="10.05.2026" ДатаВклМСП="10.08.2016"
                  ВидСубМСП="1" КатСубМСП="1" ПризНовМСП="2" СведСоцПред="2" ССЧР="37">
          <ОргВклМСП НаимОрг="ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ РОМАШКА"
                     НаимОргСокр="ООО Ромашка" ИННЮЛ="7701000000" ОГРН="1027700000000" />
          <СведМН КодРегион="77"><Город Тип="г" Наим="Москва" /></СведМН>
          <СвОКВЭД>
            <СвОКВЭДОсн КодОКВЭД="62.01" НаимОКВЭД="Разработка компьютерного программного обеспечения" ВерсОКВЭД="2014" />
          </СвОКВЭД>
        </Документ>
        """
    )

    record = parse_document(document)

    assert record is not None
    assert record.source_id == "7701000000"
    assert record.display_name == "ООО Ромашка"
    assert record.legal_form_code == "OOO"
    assert record.city_name == "Москва"
    assert record.category_slugs == ("it", "software-development")
    assert record.employee_count == 37

    provider = record_to_provider(record, datetime(2026, 4, 27, tzinfo=UTC))
    assert provider.tax_id == "7701000000"
    assert provider.registration_number == "1027700000000"
    assert provider.employee_count_range == "11-50"
    assert provider.meta["fns_sme_okved_code"] == "62.01"


def test_parse_fns_sme_ip_document() -> None:
    document = ElementTree.fromstring(
        """
        <Документ ИдДок="1" ДатаСост="10.05.2026" ДатаВклМСП="10.08.2016"
                  ВидСубМСП="2" КатСубМСП="2" ПризНовМСП="2" СведСоцПред="2">
          <ИПВклМСП ИННФЛ="770100000001" ОГРНИП="304770000000001">
            <ФИОИП Фамилия="Иванов" Имя="Иван" Отчество="Иванович" />
          </ИПВклМСП>
          <СведМН КодРегион="78" />
          <СвОКВЭД>
            <СвОКВЭДОсн КодОКВЭД="69.10" НаимОКВЭД="Деятельность в области права" ВерсОКВЭД="2014" />
          </СвОКВЭД>
        </Документ>
        """
    )

    record = parse_document(document)

    assert record is not None
    assert record.display_name == "ИП Иванов Иван Иванович"
    assert record.legal_form_code == "IP"
    assert record.city_name == "Saint Petersburg"
    assert record.category_slugs == ("legal", "corporate-law", "contracts")


def test_iter_records_from_xml_file(tmp_path) -> None:
    path = tmp_path / "fns.xml"
    path.write_text(
        """
        <Файл ИдФайл="test" ВерсФорм="4.05" ТипИнф="РЕЕСТРМСП" КолДок="2">
          <Документ ИдДок="1" ДатаСост="10.05.2026" ДатаВклМСП="10.08.2016"
                    ВидСубМСП="1" КатСубМСП="1" ПризНовМСП="2" СведСоцПред="2">
            <ОргВклМСП НаимОрг="ООО АЙТИ" ИННЮЛ="7701000001" ОГРН="1027700000001" />
            <СведМН КодРегион="77" />
            <СвОКВЭД><СвОКВЭДОсн КодОКВЭД="62.02" НаимОКВЭД="Консультирование" ВерсОКВЭД="2014" /></СвОКВЭД>
          </Документ>
          <Документ ИдДок="2" ДатаСост="10.05.2026" ДатаВклМСП="10.08.2016"
                    ВидСубМСП="1" КатСубМСП="1" ПризНовМСП="2" СведСоцПред="2">
            <ОргВклМСП НаимОрг="ООО ФЕРМА" ИННЮЛ="7701000002" ОГРН="1027700000002" />
            <СведМН КодРегион="77" />
            <СвОКВЭД><СвОКВЭДОсн КодОКВЭД="01.11" НаимОКВЭД="Выращивание зерна" ВерсОКВЭД="2014" /></СвОКВЭД>
          </Документ>
        </Файл>
        """,
        encoding="utf-8",
    )

    records = list(iter_records(path))

    assert len(records) == 1
    assert records[0].source_id == "7701000001"
    assert records[0].city_name == "Moscow"


def test_iter_records_from_jsonl_file(tmp_path) -> None:
    record = FnsSmeRecord(
        source_id="7701000003",
        display_name="ООО JSON",
        legal_name="ООО JSON",
        legal_form_code="OOO",
        tax_id="7701000003",
        registration_number="1027700000003",
        region_code="77",
        city_name="Moscow",
        okved_code="62.01",
        okved_name="Разработка ПО",
        category_slugs=("it", "software-development"),
        included_at="10.08.2016",
        sme_subject_kind="1",
        sme_category="1",
        employee_count=7,
    )
    path = tmp_path / "batch.jsonl"
    path.write_text(json.dumps(record.__dict__, ensure_ascii=False) + "\n", encoding="utf-8")

    records = list(iter_records(path))

    assert records == [record]


def test_iter_records_from_zip_file(tmp_path) -> None:
    xml = """
    <Файл ИдФайл="test" ВерсФорм="4.05" ТипИнф="РЕЕСТРМСП" КолДок="1">
      <Документ ИдДок="1" ДатаСост="10.05.2026" ДатаВклМСП="10.08.2016"
                ВидСубМСП="1" КатСубМСП="1" ПризНовМСП="2" СведСоцПред="2">
        <ОргВклМСП НаимОрг="ООО МАРКЕТИНГ" ИННЮЛ="7701000004" ОГРН="1027700000004" />
        <СведМН КодРегион="77" />
        <СвОКВЭД><СвОКВЭДОсн КодОКВЭД="73.11" НаимОКВЭД="Рекламные агентства" ВерсОКВЭД="2014" /></СвОКВЭД>
      </Документ>
    </Файл>
    """
    path = tmp_path / "fns.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("data.xml", xml)

    records = list(iter_records(path))

    assert len(records) == 1
    assert records[0].category_slugs == ("marketing", "paid-media")


def test_iter_records_rejects_unsupported_file(tmp_path) -> None:
    path = tmp_path / "fns.txt"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported FNS SME input file"):
        list(iter_records(path))


@pytest.mark.asyncio
async def test_fns_spider_reads_configured_jsonl_path(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "batch.jsonl"
    path.write_text(
        json.dumps(
            {
                "source_id": "7701000005",
                "display_name": "ООО Spider",
                "legal_name": "ООО Spider",
                "legal_form_code": "OOO",
                "tax_id": "7701000005",
                "registration_number": "1027700000005",
                "region_code": "77",
                "city_name": "Moscow",
                "okved_code": "62.01",
                "okved_name": "Разработка ПО",
                "category_slugs": ["it", "software-development"],
                "included_at": "10.08.2016",
                "sme_subject_kind": "1",
                "sme_category": "1",
                "employee_count": 3,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(fns_module, "get_settings", lambda: SimpleNamespace(fns_sme_data_path=str(path)))
    fetcher = PoliteFetcher()
    try:
        ctx = SpiderContext(fetcher=fetcher)
        items = [item async for item in RuFnsSmeRegistrySpider().crawl(ctx)]
    finally:
        await fetcher.close()

    assert len(items) == 1
    assert items[0].source == "ru-fns-sme-registry"
