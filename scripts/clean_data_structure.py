#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path
from typing import Optional

from sync_category_files import write_category_files


REPO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_DIR / "data"
PRODUCTS_JSON = DATA_DIR / "products.json"
PRODUCTS_CSV = DATA_DIR / "products.csv"
SUPPLIERS_JSON = DATA_DIR / "suppliers.json"

INFO_MISSING_KO = "정보 없음"

ADDITIONAL_LANGUAGES = [
    ("es", "Spanish"),
    ("pt", "Portuguese"),
    ("fr", "French"),
    ("it", "Italian"),
    ("id", "Indonesian"),
    ("vi", "Vietnamese"),
    ("th", "Thai"),
    ("ms", "Malay"),
    ("tl", "Filipino"),
    ("km", "Khmer"),
    ("my", "Burmese"),
    ("lo", "Lao"),
    ("ar", "Arabic"),
]

CSV_FIELDS = [
    "id",
    "category_id",
    "category_zh",
    "category_ko",
    "category_en",
    "category_name_ko",
    "category_name_en",
    "category_index",
    "image_file",
    "image_alt",
    "korean_product_name",
    "english_product_name",
    "product_name_ko",
    "product_name_en",
    "category_name_es",
    "product_name_es",
    "category_name_pt",
    "product_name_pt",
    "category_name_fr",
    "product_name_fr",
    "category_name_it",
    "product_name_it",
    "category_name_id",
    "product_name_id",
    "category_name_vi",
    "product_name_vi",
    "category_name_th",
    "product_name_th",
    "category_name_ms",
    "product_name_ms",
    "category_name_tl",
    "product_name_tl",
    "category_name_km",
    "product_name_km",
    "category_name_my",
    "product_name_my",
    "category_name_lo",
    "product_name_lo",
    "category_name_ar",
    "product_name_ar",
    "price_krw",
    "price_krw_min",
    "price_krw_max",
    "price_krw_is_range",
    "price_currency",
    "moq",
    "certificates",
    "supplier_name",
    "supplier_name_ko",
    "supplier_name_en",
    "supplier_years",
    "supplier_years_text",
    "supplier_years_ko",
    "supplier_country",
    "supplier_country_ko",
    "supplier_profile_url",
    "supplier_home_url",
    "supplier_company_id",
    "supplier_business_type",
    "supplier_business_type_ko",
    "supplier_employee_count",
    "supplier_employee_count_ko",
    "supplier_response_time",
    "supplier_response_time_ko",
    "supplier_on_time_delivery_rate",
    "supplier_on_time_delivery_rate_ko",
    "supplier_rating",
    "supplier_rating_ko",
    "supplier_total_review_order_count",
    "supplier_total_review_order_count_ko",
    "supplier_verified",
    "supplier_verified_ko",
    "source_url",
]


def parse_krw_price(value: str) -> tuple[Optional[int], Optional[int], bool]:
    if not value or "specified" in value.lower():
        return None, None, False
    numbers = [
        int(match.replace(",", ""))
        for match in re.findall(r"\d[\d,]*", value)
    ]
    if not numbers:
        return None, None, False
    if len(numbers) == 1:
        return numbers[0], numbers[0], False
    low, high = min(numbers[:2]), max(numbers[:2])
    return low, high, low != high


def clean_product(product: dict) -> None:
    price_min, price_max, is_range = parse_krw_price(product.get("price_krw", ""))
    existing_localized = product.get("localized", {})

    product["category_name_ko"] = product.get("category_ko", "")
    product["category_name_en"] = product.get("category_en", "")
    product["product_name_ko"] = product.get("korean_product_name", "")
    product["product_name_en"] = product.get("english_product_name", "")
    product["supplier_name_en"] = product.get("supplier_name", "")

    product["price_currency"] = "KRW"
    product["price_krw_min"] = price_min
    product["price_krw_max"] = price_max
    product["price_krw_is_range"] = is_range

    product["price"] = {
        "currency": "KRW",
        "display": product.get("price_krw", ""),
        "min": price_min,
        "max": price_max,
        "is_range": is_range,
    }

    product["localized"] = {
        **existing_localized,
        "ko": {
            "category_name": product.get("category_ko", ""),
            "product_name": product.get("korean_product_name", ""),
            "supplier_name": product.get("supplier_name_ko", INFO_MISSING_KO),
            "supplier_country": product.get("supplier_country_ko", INFO_MISSING_KO),
            "supplier_business_type": product.get("supplier_business_type_ko", INFO_MISSING_KO),
            "supplier_employee_count": product.get("supplier_employee_count_ko", INFO_MISSING_KO),
            "supplier_response_time": product.get("supplier_response_time_ko", INFO_MISSING_KO),
            "supplier_on_time_delivery_rate": product.get("supplier_on_time_delivery_rate_ko", INFO_MISSING_KO),
            "supplier_rating": product.get("supplier_rating_ko", INFO_MISSING_KO),
            "supplier_total_review_order_count": product.get("supplier_total_review_order_count_ko", INFO_MISSING_KO),
            "supplier_verified": product.get("supplier_verified_ko", INFO_MISSING_KO),
        },
        "en": {
            "category_name": product.get("category_en", ""),
            "product_name": product.get("english_product_name", ""),
            "supplier_name": product.get("supplier_name", ""),
            "supplier_country": product.get("supplier_country", ""),
            "supplier_business_type": product.get("supplier_business_type", ""),
            "supplier_employee_count": product.get("supplier_employee_count", ""),
            "supplier_response_time": product.get("supplier_response_time", ""),
            "supplier_on_time_delivery_rate": product.get("supplier_on_time_delivery_rate", ""),
            "supplier_rating": product.get("supplier_rating", ""),
            "supplier_total_review_order_count": product.get("supplier_total_review_order_count", ""),
            "supplier_verified": product.get("supplier_verified", ""),
        },
    }


def clean_supplier_cache(products: list[dict]) -> None:
    if not SUPPLIERS_JSON.exists():
        return
    suppliers = json.loads(SUPPLIERS_JSON.read_text(encoding="utf-8"))
    by_url = {product["source_url"]: product for product in products}
    for url, supplier in suppliers.items():
        product = by_url.get(url)
        if not product:
            continue
        supplier["supplier_name_en"] = supplier.get("supplier_name", "")
        supplier["localized"] = {
            "ko": product["localized"]["ko"],
            "en": {
                key: value
                for key, value in product["localized"]["en"].items()
                if key != "category_name" and key != "product_name"
            },
        }
    SUPPLIERS_JSON.write_text(
        json.dumps(suppliers, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(products: list[dict]) -> None:
    with PRODUCTS_CSV.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for product in products:
            row = {field: product.get(field, "") for field in CSV_FIELDS}
            row["certificates"] = "; ".join(product.get("certificates", []))
            writer.writerow(row)


def main() -> None:
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    products = payload["products"]
    for product in products:
        clean_product(product)

    payload["metadata"]["data_structure_version"] = "2026-07-02.multilingual-price-v2"
    payload["metadata"]["multilingual_fields"] = {
        "note": "Display values are separated under product.localized. Legacy flat fields are preserved for compatibility.",
        "object": "localized",
        "languages": ["ko", "en", *[code for code, _name in ADDITIONAL_LANGUAGES]],
    }
    payload["metadata"]["price_fields"] = {
        "currency": "KRW",
        "display_field": "price_krw",
        "numeric_fields": ["price_krw_min", "price_krw_max"],
        "object": "price",
        "note": "Range prices are split into min and max integer KRW values. Single prices use the same value for min and max.",
    }

    PRODUCTS_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_category_files(payload)
    write_csv(products)
    clean_supplier_cache(products)

    print(f"Cleaned products: {len(products)}")
    print("Added localized language objects and numeric KRW min/max price fields")


if __name__ == "__main__":
    main()
