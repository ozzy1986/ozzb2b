#!/usr/bin/env python3
"""Quick verification that Russian UI is live."""

from __future__ import annotations

import requests


def check(url: str, expected: list[str]) -> None:
    html = requests.get(url, timeout=20).text
    print(url)
    for token in expected:
        print(f"  {token}: {'ok' if token in html else 'missing'}")
    print("---")


def main() -> None:
    check(
        "https://ozzb2b.com/",
        [
            "Найдите надежного B2B-подрядчика в России",
            "Категории услуг",
            "Рекомендуемые компании",
            '<html lang="ru"',
        ],
    )
    check(
        "https://ozzb2b.com/providers",
        [
            "Фильтры",
            "Поиск компаний",
            "Показано",
            "Искать",
        ],
    )
    check(
        "https://ozzb2b.com/providers?country=RU",
        [
            "Россия",
            "ООО",
            "АО",
            "Reksoft",
        ],
    )


if __name__ == "__main__":
    main()
