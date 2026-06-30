#!/usr/bin/env python3
import json
from copy import deepcopy
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_DIR / "data"
PRODUCTS_JSON = DATA_DIR / "products.json"

CATEGORY_FILE_NAMES = {
    "power-bank": "power_bank.json",
    "womens-dresses": "womens_dresses.json",
    "cooling-mattresses": "cooling_mattresses.json",
    "desktop-organizers": "desktop_organizers.json",
    "memory-cards": "memory_cards.json",
}

CATEGORY_ORDER = [
    "power-bank",
    "womens-dresses",
    "cooling-mattresses",
    "desktop-organizers",
    "memory-cards",
]


def category_metadata(source_payload: dict, category: dict, products: list[dict]) -> dict:
    source_metadata = deepcopy(source_payload.get("metadata", {}))
    metadata = {
        "source": source_metadata.get("source", ""),
        "generated_from": "data/products.json",
        "dataset_type": "category_subset",
        "category": {
            "category_id": category["category_id"],
            "category_zh": category["category_zh"],
            "category_ko": category["category_ko"],
            "category_en": category["category_en"],
            "count": len(products),
        },
        "total_products": len(products),
        "price_currency": source_metadata.get("price_currency", "KRW"),
        "notes": [
            "This category file uses the same top-level structure as data/products.json.",
            "Product row fields are identical to the canonical products array in data/products.json.",
            "source_url stores the Alibaba product detail page.",
            "image_file stores the relative path to the downloaded product main image.",
        ],
    }
    for key in [
        "supplier_fields",
        "supplier_korean_fields",
        "latest_memory_card_exchange_rate",
        "image_storage",
    ]:
        if key in source_metadata:
            metadata[key] = source_metadata[key]
    return metadata


def ordered_categories(products: list[dict]) -> list[dict]:
    categories: dict[str, dict] = {}
    for product in products:
        category_id = product["category_id"]
        categories.setdefault(
            category_id,
            {
                "category_id": category_id,
                "category_zh": product["category_zh"],
                "category_ko": product["category_ko"],
                "category_en": product["category_en"],
                "count": 0,
            },
        )
        categories[category_id]["count"] += 1
    return [
        categories[category_id]
        for category_id in CATEGORY_ORDER
        if category_id in categories
    ]


def write_category_files(payload: dict) -> list[Path]:
    products = payload["products"]
    written = []
    for category in ordered_categories(products):
        category_id = category["category_id"]
        category_products = [
            product for product in products if product["category_id"] == category_id
        ]
        category_payload = {
            "metadata": category_metadata(payload, category, category_products),
            "products": category_products,
        }
        filename = CATEGORY_FILE_NAMES.get(
            category_id,
            f"{category_id.replace('-', '_')}.json",
        )
        path = DATA_DIR / filename
        path.write_text(
            json.dumps(category_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        written.append(path)
    return written


def main() -> None:
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    written = write_category_files(payload)
    print(f"Wrote {len(written)} category files")
    for path in written:
        print(path.relative_to(REPO_DIR))


if __name__ == "__main__":
    main()
