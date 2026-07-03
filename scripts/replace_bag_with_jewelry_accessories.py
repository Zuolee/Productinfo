#!/usr/bin/env python3
import json
from pathlib import Path

from add_korean_supplier_fields import main as add_korean_supplier_fields
from add_more_categories import (
    CATEGORIES,
    REPO_DIR,
    SUPPLIERS_JSON,
    build_products,
    enrich_new_products,
    fetch_rates,
    ordered_categories,
)
from clean_data_structure import main as clean_data_structure
from sync_category_files import write_category_files


PRODUCTS_JSON = REPO_DIR / "data/products.json"
OLD_CATEGORY_ID = "bag-accessories"
NEW_CATEGORY_ID = "jewelry-accessories"


def main() -> None:
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    rates, rate_date = fetch_rates()
    category = CATEGORIES[NEW_CATEGORY_ID]

    print(f"Replacing {OLD_CATEGORY_ID} with {NEW_CATEGORY_ID}")
    print(f"Rates: 1 CNY = ₩{rates['CNY']:,.2f}; 1 USD = ₩{rates['USD']:,.2f}; rate date {rate_date}")

    jewelry_products = build_products(category, rates)
    enrich_new_products(jewelry_products)

    products = [
        product
        for product in payload["products"]
        if product["category_id"] != OLD_CATEGORY_ID and product["category_id"] != NEW_CATEGORY_ID
    ] + jewelry_products

    payload["products"] = products
    payload["metadata"]["total_products"] = len(products)
    payload["metadata"]["categories"] = ordered_categories(products)
    payload["metadata"]["latest_jewelry_accessories_exchange_rate"] = (
        f"1 CNY = ₩{rates['CNY']:,.2f}; 1 USD = ₩{rates['USD']:,.2f}; rate date {rate_date}"
    )

    PRODUCTS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_category_files(payload)

    old_category_path = REPO_DIR / "data/bag_accessories.json"
    if old_category_path.exists():
        old_category_path.unlink()

    old_image_dir = REPO_DIR / "images/bag_accessories"
    if old_image_dir.exists():
        for image in old_image_dir.glob("*"):
            image.unlink()
        old_image_dir.rmdir()

    # Re-run the existing normalization passes so the new category has
    # Korean supplier fields, localized objects, CSV rows, and min/max prices.
    add_korean_supplier_fields()
    clean_data_structure()

    # Remove supplier cache entries that no longer belong to any product.
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    active_urls = {product["source_url"] for product in payload["products"]}
    suppliers = json.loads(SUPPLIERS_JSON.read_text(encoding="utf-8"))
    suppliers = {url: supplier for url, supplier in suppliers.items() if url in active_urls}
    SUPPLIERS_JSON.write_text(json.dumps(suppliers, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Dataset total: {len(payload['products'])}")
    print(f"{NEW_CATEGORY_ID}: {sum(1 for p in payload['products'] if p['category_id'] == NEW_CATEGORY_ID)}")
    print(f"{OLD_CATEGORY_ID}: {sum(1 for p in payload['products'] if p['category_id'] == OLD_CATEGORY_ID)}")


if __name__ == "__main__":
    main()
