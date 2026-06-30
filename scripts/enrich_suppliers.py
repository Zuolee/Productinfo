#!/usr/bin/env python3
import csv
import json
import re
import time
from pathlib import Path

import requests


REPO_DIR = Path(__file__).resolve().parents[1]
PRODUCTS_JSON = REPO_DIR / "data/products.json"
PRODUCTS_CSV = REPO_DIR / "data/products.csv"
SUPPLIER_CACHE = REPO_DIR / "data/suppliers.json"
README = REPO_DIR / "README.md"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


STRING_FIELDS = {
    "supplier_name": "companyName",
    "supplier_profile_url": "companyProfileUrl",
    "supplier_home_url": "homeUrl",
    "supplier_country": "companyRegisterCountry",
    "supplier_years": "companyJoinYears",
    "supplier_years_text": "localCompanyJoinYears",
    "supplier_business_type": "companyBusinessType",
    "supplier_employee_count": "employeesCount",
    "supplier_response_time": "responseTimeText",
    "supplier_on_time_delivery_rate": "supplierOnTimeDeliveryRate",
    "supplier_rating": "averageStar",
}

NUMBER_FIELDS = {
    "supplier_company_id": "companyId",
    "supplier_owner_member_seq": "ownerMemberSeq",
    "supplier_total_review_order_count": "totalReviewOrderCount",
}


def decode_json_string(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value.replace("\\/", "/")


def match_string(source: str, key: str) -> str:
    match = re.search(rf'"{re.escape(key)}":"((?:\\.|[^"\\])*)"', source)
    return decode_json_string(match.group(1)).strip() if match else ""


def match_number(source: str, key: str):
    match = re.search(rf'"{re.escape(key)}":(-?\d+(?:\.\d+)?)', source)
    if not match:
        return ""
    raw = match.group(1)
    return float(raw) if "." in raw else int(raw)


def fetch_supplier(url: str) -> dict:
    last_error = ""
    for attempt in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=45)
            response.raise_for_status()
            source = response.text
            supplier = {}
            for output_key, page_key in STRING_FIELDS.items():
                supplier[output_key] = match_string(source, page_key)
            for output_key, page_key in NUMBER_FIELDS.items():
                supplier[output_key] = match_number(source, page_key)

            supplier["supplier_verified"] = bool(match_string(source, "companyHasPassAssessment") or re.search(r'"companyHasPassAssessment":true', source))
            supplier["supplier_source"] = "Alibaba product detail page"

            if not supplier["supplier_name"]:
                # Search-result cards and some detail variants use related names.
                supplier["supplier_name"] = match_string(source, "company_name") or match_string(source, "supplierName")
            if not supplier["supplier_years_text"] and supplier["supplier_years"]:
                supplier["supplier_years_text"] = f"{supplier['supplier_years']} yrs"
            if not supplier["supplier_profile_url"]:
                supplier["supplier_profile_url"] = match_string(source, "supplierHref")
            if not supplier["supplier_home_url"]:
                supplier["supplier_home_url"] = match_string(source, "supplierHomeHref")
            return supplier
        except Exception as exc:  # network pages can be flaky; retry then record.
            last_error = str(exc)
            time.sleep(1 + attempt)
    return {
        "supplier_name": "",
        "supplier_profile_url": "",
        "supplier_home_url": "",
        "supplier_country": "",
        "supplier_years": "",
        "supplier_years_text": "",
        "supplier_business_type": "",
        "supplier_employee_count": "",
        "supplier_response_time": "",
        "supplier_on_time_delivery_rate": "",
        "supplier_rating": "",
        "supplier_total_review_order_count": "",
        "supplier_company_id": "",
        "supplier_owner_member_seq": "",
        "supplier_verified": False,
        "supplier_source": f"Fetch failed: {last_error}",
    }


def write_csv(products: list[dict]) -> None:
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
        "supplier_name",
        "supplier_years",
        "supplier_years_text",
        "supplier_country",
        "supplier_profile_url",
        "supplier_home_url",
        "supplier_company_id",
        "supplier_business_type",
        "supplier_employee_count",
        "supplier_response_time",
        "supplier_on_time_delivery_rate",
        "supplier_rating",
        "supplier_total_review_order_count",
        "supplier_verified",
        "source_url",
    ]
    with PRODUCTS_CSV.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for product in products:
            row = {field: product.get(field, "") for field in fields}
            row["certificates"] = "; ".join(product.get("certificates", []))
            writer.writerow(row)


def update_readme(total_products: int) -> None:
    text = README.read_text(encoding="utf-8")
    schema_block = """- `certificates`: list of visible certificate labels.
- `supplier_name`: Alibaba supplier/company name shown on the product detail page.
- `supplier_years`, `supplier_years_text`: Alibaba join/supplier tenure.
- `supplier_country`: supplier registered country/region code.
- `supplier_profile_url`, `supplier_home_url`: Alibaba supplier profile/home links.
- `supplier_company_id`: Alibaba company ID when exposed by the detail page.
- `supplier_business_type`, `supplier_employee_count`: supplier profile attributes when exposed.
- `supplier_response_time`, `supplier_on_time_delivery_rate`, `supplier_rating`, `supplier_total_review_order_count`: public supplier performance fields when exposed.
- `supplier_verified`: whether the detail page exposes pass-assessment/verified signal.
- `source_url`: Alibaba.com source product URL."""
    text = re.sub(
        r"- `certificates`: list of visible certificate labels\.\n- `source_url`: Alibaba\.com source product URL\.",
        schema_block,
        text,
    )
    note = "- Supplier fields are collected from public Alibaba.com product detail pages and may change over time."
    if note not in text:
        text = text.replace(
            "- KRW prices were converted in the source workbook or supplemental category script before this repository export.\n",
            "- KRW prices were converted in the source workbook or supplemental category script before this repository export.\n"
            f"{note}\n",
        )
    text = re.sub(r"Total products: \*\*\d+\*\*", f"Total products: **{total_products}**", text)
    README.write_text(text, encoding="utf-8")


def main() -> None:
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    products = payload["products"]
    supplier_by_url = {}

    for index, product in enumerate(products, start=1):
        url = product["source_url"]
        print(f"[{index:03d}/{len(products)}] {product['id']} {url}")
        supplier = fetch_supplier(url)
        supplier_by_url[url] = supplier
        product.update(supplier)
        time.sleep(0.2)

    payload["metadata"]["supplier_fields"] = {
        "source": "Alibaba.com product detail pages",
        "collected_fields": list(STRING_FIELDS.keys()) + list(NUMBER_FIELDS.keys()) + ["supplier_verified"],
        "note": "Supplier fields are public page fields and may change over time.",
    }
    PRODUCTS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    SUPPLIER_CACHE.write_text(json.dumps(supplier_by_url, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(products)
    update_readme(len(products))

    missing = [product["id"] for product in products if not product.get("supplier_name")]
    print(f"Enriched products: {len(products)}")
    print(f"Missing supplier_name: {len(missing)}")
    if missing:
        print("Missing IDs:", ", ".join(missing[:20]))


if __name__ == "__main__":
    main()
