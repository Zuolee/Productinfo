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
    "nail-polish": "nail_polish.json",
    "safety-helmets": "safety_helmets.json",
    "pc-power-supplies": "pc_power_supplies.json",
    "jewelry-accessories": "jewelry_accessories.json",
    "smart-watches": "smart_watches.json",
    "bluetooth-speakers": "bluetooth_speakers.json",
    "air-purifiers": "air_purifiers.json",
    "electric-toothbrushes": "electric_toothbrushes.json",
    "yoga-mats": "yoga_mats.json",
    "pet-grooming-tools": "pet_grooming_tools.json",
    "coffee-machines": "coffee_machines.json",
    "solar-panels": "solar_panels.json",
    "led-strip-lights": "led_strip_lights.json",
    "kitchen-knives": "kitchen_knives.json",
    "backpacks": "backpacks.json",
    "car-phone-holders": "car_phone_holders.json",
    "baby-strollers": "baby_strollers.json",
    "office-chairs": "office_chairs.json",
    "stainless-water-bottles": "stainless_water_bottles.json",
    "wireless-earbuds": "wireless_earbuds.json",
    "makeup-brushes": "makeup_brushes.json",
    "garden-tools": "garden_tools.json",
    "electric-bicycles": "electric_bicycles.json",
    "plastic-food-containers": "plastic_food_containers.json",
}

CATEGORY_ORDER = [
    "power-bank",
    "womens-dresses",
    "cooling-mattresses",
    "desktop-organizers",
    "memory-cards",
    "nail-polish",
    "safety-helmets",
    "pc-power-supplies",
    "jewelry-accessories",
    "smart-watches",
    "bluetooth-speakers",
    "air-purifiers",
    "electric-toothbrushes",
    "yoga-mats",
    "pet-grooming-tools",
    "coffee-machines",
    "solar-panels",
    "led-strip-lights",
    "kitchen-knives",
    "backpacks",
    "car-phone-holders",
    "baby-strollers",
    "office-chairs",
    "stainless-water-bottles",
    "wireless-earbuds",
    "makeup-brushes",
    "garden-tools",
    "electric-bicycles",
    "plastic-food-containers",
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
        "data_structure_version",
        "multilingual_fields",
        "price_fields",
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
    ordered = [
        categories[category_id]
        for category_id in CATEGORY_ORDER
        if category_id in categories
    ]
    known = {category["category_id"] for category in ordered}
    ordered.extend(
        categories[category_id]
        for category_id in sorted(categories)
        if category_id not in known
    )
    return ordered


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
