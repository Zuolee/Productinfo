#!/usr/bin/env python3
import csv
import json
from pathlib import Path

from PIL import Image

from sync_category_files import write_category_files


REPO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_DIR / "data"
IMAGE_DIR = REPO_DIR / "images"
PRODUCTS_JSON = DATA_DIR / "products.json"
PRODUCTS_CSV = DATA_DIR / "products.csv"

CATEGORY_IMAGE_DIRS = {
    "power-bank": "power_bank",
    "womens-dresses": "womens_dresses",
    "cooling-mattresses": "cooling_mattresses",
    "desktop-organizers": "desktop_organizers",
    "memory-cards": "memory_cards",
}


def convert_to_png(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.load()
        if image.mode in {"RGBA", "LA"} or (
            image.mode == "P" and "transparency" in image.info
        ):
            converted = image.convert("RGBA")
        else:
            converted = image.convert("RGB")
        converted.save(target, format="PNG", optimize=True)


def write_csv(products: list[dict]) -> None:
    fieldnames = [
        "id",
        "category_id",
        "category_zh",
        "category_ko",
        "category_en",
        "category_index",
        "image_file",
        "image_alt",
        "korean_product_name",
        "english_product_name",
        "price_krw",
        "moq",
        "certificates",
        "supplier_name",
        "supplier_name_ko",
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
    with PRODUCTS_CSV.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for product in products:
            row = {field: product.get(field, "") for field in fieldnames}
            row["certificates"] = "; ".join(product.get("certificates", []))
            writer.writerow(row)


def main() -> None:
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    products = payload["products"]
    conversions: list[tuple[Path, Path]] = []

    for product in products:
        old_relative = product["image_file"]
        old_path = REPO_DIR / old_relative
        if not old_path.exists():
            raise FileNotFoundError(f"Missing source image for {product['id']}: {old_relative}")

        category_dir = CATEGORY_IMAGE_DIRS.get(
            product["category_id"],
            product["category_id"].replace("-", "_"),
        )
        new_name = f"{Path(old_relative).stem}.png"
        new_relative = f"images/{category_dir}/{new_name}"
        new_path = REPO_DIR / new_relative

        if old_path.resolve() != new_path.resolve():
            convert_to_png(old_path, new_path)
            conversions.append((old_path, new_path))
        elif new_path.suffix.lower() != ".png":
            raise ValueError(f"Unexpected non-PNG target path: {new_relative}")

        product["image_file"] = new_relative

    payload["metadata"]["image_storage"] = {
        "format": "PNG",
        "directory": "images/<category>/",
        "note": "Product main images are converted to PNG and grouped by category for Figma compatibility.",
    }
    PRODUCTS_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_category_files(payload)
    write_csv(products)

    for old_path, new_path in conversions:
        if old_path.exists() and old_path.resolve() != new_path.resolve():
            old_path.unlink()

    print(f"Converted images: {len(conversions)}")
    print("Updated data/products.json, category JSON files, and data/products.csv")


if __name__ == "__main__":
    main()
