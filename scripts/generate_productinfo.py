#!/usr/bin/env python3
import csv
import html
import json
import re
import shutil
from pathlib import Path

from sync_category_files import write_category_files


REPO_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_DIR.parent
HTML_PATH = SOURCE_DIR / "power_bank_products_krw.html"
SOURCE_XLSX = SOURCE_DIR / "outputs/product_table_workbook/alibaba_products_with_images.xlsx"

DATA_DIR = REPO_DIR / "data"
IMAGE_DIR = REPO_DIR / "images"
EXPORT_DIR = REPO_DIR / "exports"

CATEGORIES = {
    "panel-power-bank": {
        "category_id": "power-bank",
        "category_ko": "보조배터리",
        "category_en": "Power Banks",
        "category_zh": "移动电源",
    },
    "panel-womens-dresses": {
        "category_id": "womens-dresses",
        "category_ko": "여성 원피스",
        "category_en": "Women's Dresses",
        "category_zh": "女士连衣裙",
    },
    "panel-cooling-mattresses": {
        "category_id": "cooling-mattresses",
        "category_ko": "쿨링 매트리스",
        "category_en": "Cooling Mattresses",
        "category_zh": "凉感床垫",
    },
    "panel-desktop-organizers": {
        "category_id": "desktop-organizers",
        "category_ko": "데스크 정리함",
        "category_en": "Desktop Organizers",
        "category_zh": "桌面整理柜",
    },
}


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]*>", "", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def decode_attr(value: str) -> str:
    return html.unescape(value).strip()


def parse_products() -> list[dict]:
    source_html = HTML_PATH.read_text(encoding="utf-8")
    products: list[dict] = []

    for panel_id, category in CATEGORIES.items():
        section_match = re.search(
            rf'<section id="{panel_id}"[\s\S]*?</section>',
            source_html,
        )
        if not section_match:
            raise RuntimeError(f"Missing section: {panel_id}")

        rows = re.finditer(
            r'<tr data-product="([^"]+)" data-certificate="([^"]*)">([\s\S]*?)</tr>',
            section_match.group(0),
        )
        category_index = 0
        for row in rows:
            body = row.group(3)
            category_index += 1

            image_match = re.search(r'<img src="([^"]+)" alt="([^"]*)">', body)
            url_match = re.search(r'<a href="([^"]+)"', body)
            korean_match = re.search(r'<span class="name-ko" lang="ko">([\s\S]*?)</span>', body)
            english_match = re.search(r'<span class="name-en" lang="en">([\s\S]*?)</span>', body)
            price_match = re.search(r'<td class="price">([\s\S]*?)</td>', body)
            moq_match = re.search(r'<td class="moq">([\s\S]*?)</td>', body)
            certs = [
                strip_tags(match.group(1))
                for match in re.finditer(r'<span class="cert">([\s\S]*?)</span>', body)
            ]

            if not all([image_match, url_match, korean_match, english_match, price_match, moq_match]):
                raise RuntimeError(f"Unable to parse row {row.group(1)} in {panel_id}")

            src_image = SOURCE_DIR / decode_attr(image_match.group(1))
            image_name = src_image.name
            target_image = IMAGE_DIR / image_name

            products.append(
                {
                    "id": f"{category['category_id']}-{category_index:02d}",
                    "category_id": category["category_id"],
                    "category_zh": category["category_zh"],
                    "category_ko": category["category_ko"],
                    "category_en": category["category_en"],
                    "category_index": category_index,
                    "image_file": f"images/{image_name}",
                    "image_alt": decode_attr(image_match.group(2)),
                    "korean_product_name": strip_tags(korean_match.group(1)),
                    "english_product_name": strip_tags(english_match.group(1)),
                    "price_krw": strip_tags(price_match.group(1)),
                    "moq": strip_tags(moq_match.group(1)),
                    "certificates": certs or [decode_attr(row.group(2)) or "Listing not specified"],
                    "source_url": decode_attr(url_match.group(1)),
                    "_source_image": src_image,
                    "_target_image": target_image,
                }
            )

    return products


def write_json(products: list[dict]) -> None:
    public_products = [
        {key: value for key, value in product.items() if not key.startswith("_")}
        for product in products
    ]
    payload = {
        "metadata": {
            "source": "Alibaba.com public product listings collected into local HTML workbook",
            "generated_from": "power_bank_products_krw.html",
            "total_products": len(public_products),
            "categories": [
                {
                    "category_id": data["category_id"],
                    "category_zh": data["category_zh"],
                    "category_ko": data["category_ko"],
                    "category_en": data["category_en"],
                    "count": sum(1 for p in public_products if p["category_id"] == data["category_id"]),
                }
                for data in CATEGORIES.values()
            ],
            "price_currency": "KRW",
            "notes": [
                "source_url stores the Alibaba product detail page.",
                "image_file stores the relative path to the downloaded product main image.",
                "certificate values are taken from public listing badges or explicit title text; Listing not specified means the list page did not expose a concrete certificate.",
            ],
        },
        "products": public_products,
    }
    (DATA_DIR / "products.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_category_files(payload)


def write_csv(products: list[dict]) -> None:
    public_products = [
        {key: value for key, value in product.items() if not key.startswith("_")}
        for product in products
    ]
    fields = [
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
        "source_url",
    ]
    with (DATA_DIR / "products.csv").open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for product in public_products:
            row = dict(product)
            row["certificates"] = "; ".join(row["certificates"])
            writer.writerow(row)


def copy_assets(products: list[dict]) -> None:
    for product in products:
        src = product["_source_image"]
        target = product["_target_image"]
        if not src.exists():
            raise RuntimeError(f"Missing image: {src}")
        shutil.copy2(src, target)
    if SOURCE_XLSX.exists():
        shutil.copy2(SOURCE_XLSX, EXPORT_DIR / "alibaba_products_with_images.xlsx")


def write_readme(products: list[dict]) -> None:
    counts = {
        data["category_id"]: sum(1 for product in products if product["category_id"] == data["category_id"])
        for data in CATEGORIES.values()
    }
    lines = [
        "# Productinfo",
        "",
        "Structured Alibaba.com product information for Korea-market research.",
        "",
        "## Files",
        "",
        "- `data/products.json` — canonical structured data for agents and scripts.",
        "- `data/products.csv` — flat table version for spreadsheets or lightweight parsing.",
        "- `images/` — downloaded product main images referenced by `image_file`.",
        "- `exports/alibaba_products_with_images.xlsx` — Excel workbook with embedded product images.",
        "",
        "## Product counts",
        "",
        "| Category ID | 中文品类 | 한국어 | English | Count |",
        "|---|---|---|---|---:|",
    ]
    for data in CATEGORIES.values():
        lines.append(
            f"| `{data['category_id']}` | {data['category_zh']} | {data['category_ko']} | {data['category_en']} | {counts[data['category_id']]} |"
        )
    lines.extend(
        [
            "",
            f"Total products: **{len(products)}**",
            "",
            "## Schema",
            "",
            "Each product row contains:",
            "",
            "- `id`: stable product ID within this dataset.",
            "- `category_id`, `category_zh`, `category_ko`, `category_en`: category labels.",
            "- `category_index`: product number inside its category.",
            "- `image_file`: relative path to the downloaded main image.",
            "- `image_alt`: image alt text from the source HTML.",
            "- `korean_product_name`: Korean product title.",
            "- `english_product_name`: English source/comparable product title.",
            "- `price_krw`: KRW price string.",
            "- `moq`: minimum order quantity.",
            "- `certificates`: list of visible certificate labels.",
            "- `source_url`: Alibaba.com source product URL.",
            "",
            "## Notes",
            "",
            "- Prices, MOQ, and product availability can change on Alibaba.com.",
            "- Certificate values reflect public listing badges or explicit title text. `Listing not specified` means the list page did not expose a concrete certificate.",
            "- KRW prices were converted in the source workbook before this repository export.",
            "",
        ]
    )
    (REPO_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    products = parse_products()
    if len(products) != 120:
        raise RuntimeError(f"Expected 120 products, got {len(products)}")

    copy_assets(products)
    write_json(products)
    write_csv(products)
    write_readme(products)

    print(f"Generated {len(products)} products")
    for data in CATEGORIES.values():
        count = sum(1 for product in products if product["category_id"] == data["category_id"])
        print(f"{data['category_id']}: {count}")


if __name__ == "__main__":
    main()
