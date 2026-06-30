#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path

from sync_category_files import write_category_files


REPO_DIR = Path(__file__).resolve().parents[1]
PRODUCTS_JSON = REPO_DIR / "data/products.json"
PRODUCTS_CSV = REPO_DIR / "data/products.csv"
SUPPLIERS_JSON = REPO_DIR / "data/suppliers.json"
README = REPO_DIR / "README.md"
INFO_MISSING_KO = "정보 없음"

COUNTRY_KO = {
    "CN": "중국",
    "TR": "튀르키예",
    "TW": "대만",
    "KR": "대한민국",
    "US": "미국",
    "VN": "베트남",
    "IN": "인도",
}

BUSINESS_TYPE_KO = {
    "Manufacturer": "제조업체",
    "Trading Company": "무역회사",
    "Distributor/Wholesaler": "유통/도매업체",
    "Buying Office": "구매대행사",
    "Agent": "에이전트",
    "Business Service": "비즈니스 서비스",
}

CITY_WORDS = {
    "Shenzhen": "선전",
    "Guangdong": "광둥",
    "Guangzhou": "광저우",
    "Dongguan": "둥관",
    "Hangzhou": "항저우",
    "Yiwu": "이우",
    "Shanghai": "상하이",
    "Ningbo": "닝보",
    "Wenzhou": "원저우",
    "Quanzhou": "취안저우",
    "Xiamen": "샤먼",
    "Shantou": "산터우",
    "Zhongshan": "중산",
    "Qingdao": "칭다오",
    "Suzhou": "쑤저우",
    "Huzhou": "후저우",
    "Shaoxing": "사오싱",
    "Nantong": "난퉁",
    "Jiangsu": "장쑤",
    "Zhejiang": "저장",
    "Fujian": "푸젠",
    "Wuxi": "우시",
    "Foshan": "포산",
    "Xuzhou": "쉬저우",
    "Tianjin": "톈진",
    "Beijing": "베이징",
    "Taiwan": "대만",
}

COMPANY_WORDS = {
    "Technology": "테크놀로지",
    "Technologies": "테크놀로지",
    "Electronics": "전자",
    "Electronic": "전자",
    "Electrical": "전기",
    "Industrial": "산업",
    "Industry": "산업",
    "Industries": "산업",
    "International": "인터내셔널",
    "Import And Export": "수출입",
    "Import and Export": "수출입",
    "Import & Export": "수출입",
    "Trading": "무역",
    "Trade": "무역",
    "Textile": "섬유",
    "Textiles": "섬유",
    "Garment": "의류",
    "Fashion": "패션",
    "Apparel": "의류",
    "Clothing": "의류",
    "Furniture": "가구",
    "Household": "생활용품",
    "Home": "홈",
    "Plastic": "플라스틱",
    "Wood": "목재",
    "Wooden": "목재",
    "Bamboo": "대나무",
    "Storage": "수납",
    "Products": "제품",
    "Product": "제품",
    "New Materials": "신소재",
    "Materials": "소재",
    "Factory": "공장",
    "Manufacturing": "제조",
    "Development": "개발",
    "Design": "디자인",
}

LEGAL_SUFFIX_REPLACEMENTS = [
    (r"\bCo\.,?\s*Ltd\.?\b", "유한회사"),
    (r"\bCompany Limited\b", "유한회사"),
    (r"\bLimited\b", "유한회사"),
    (r"\bLLC\b", "유한책임회사"),
    (r"\bInc\.?\b", "주식회사"),
    (r"\bCorporation\b", "주식회사"),
    (r"\bCorp\.?\b", "주식회사"),
    (r"\bLTD\.?\b", "유한회사"),
]


def translate_supplier_name(name: str, country: str = "") -> str:
    if not name:
        return INFO_MISSING_KO

    translated = name
    for pattern, replacement in LEGAL_SUFFIX_REPLACEMENTS:
        translated = re.sub(pattern, replacement, translated, flags=re.I)

    # Replace longer phrases first to avoid partial word collisions.
    word_map = {**CITY_WORDS, **COMPANY_WORDS}
    for english, korean in sorted(word_map.items(), key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(rf"\b{re.escape(english)}\b", korean, translated, flags=re.I)

    translated = re.sub(r"\s+", " ", translated).strip(" ,")
    translated = translated.replace(" ,", ",")

    if country and country in COUNTRY_KO and COUNTRY_KO[country] not in translated:
        translated = f"{translated} ({COUNTRY_KO[country]})"
    return translated


def translate_years(years, years_text: str = "") -> str:
    value = str(years or "").strip()
    if not value and years_text:
        match = re.search(r"\d+", years_text)
        value = match.group(0) if match else ""
    return f"{value}년" if value else INFO_MISSING_KO


def translate_country(country: str) -> str:
    return COUNTRY_KO.get(country or "", country or INFO_MISSING_KO)


def translate_business_type(value: str) -> str:
    if not value:
        return INFO_MISSING_KO
    parts = [part.strip() for part in value.split(",") if part.strip()]
    return ", ".join(BUSINESS_TYPE_KO.get(part, part) for part in parts)


def translate_employee_count(value: str) -> str:
    return f"{value}명" if value else INFO_MISSING_KO


def translate_response_time(value: str) -> str:
    if not value:
        return INFO_MISSING_KO
    return value.replace("h", "시간")


def translate_delivery_rate(value: str) -> str:
    return f"정시 배송률 {value}" if value else INFO_MISSING_KO


def translate_rating(value: str) -> str:
    return f"{value}/5점" if value else INFO_MISSING_KO


def translate_reviews(value) -> str:
    if value == "" or value is None:
        return INFO_MISSING_KO
    return f"{value}건"


def translate_verified(value) -> str:
    if value is True:
        return "인증됨"
    if value is False:
        return "미인증"
    return INFO_MISSING_KO


def enrich_product(product: dict) -> None:
    product["supplier_name_ko"] = translate_supplier_name(
        product.get("supplier_name", ""),
        product.get("supplier_country", ""),
    )
    product["supplier_years_ko"] = translate_years(
        product.get("supplier_years", ""),
        product.get("supplier_years_text", ""),
    )
    product["supplier_country_ko"] = translate_country(product.get("supplier_country", ""))
    product["supplier_business_type_ko"] = translate_business_type(product.get("supplier_business_type", ""))
    product["supplier_employee_count_ko"] = translate_employee_count(product.get("supplier_employee_count", ""))
    product["supplier_response_time_ko"] = translate_response_time(product.get("supplier_response_time", ""))
    product["supplier_on_time_delivery_rate_ko"] = translate_delivery_rate(product.get("supplier_on_time_delivery_rate", ""))
    product["supplier_rating_ko"] = translate_rating(product.get("supplier_rating", ""))
    product["supplier_total_review_order_count_ko"] = translate_reviews(product.get("supplier_total_review_order_count", ""))
    product["supplier_verified_ko"] = translate_verified(product.get("supplier_verified"))


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
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for product in products:
            row = {field: product.get(field, "") for field in fields}
            row["certificates"] = "; ".join(product.get("certificates", []))
            writer.writerow(row)


def update_suppliers_cache(products: list[dict]) -> None:
    if not SUPPLIERS_JSON.exists():
        return
    suppliers = json.loads(SUPPLIERS_JSON.read_text(encoding="utf-8"))
    product_by_url = {product["source_url"]: product for product in products}
    for url, supplier in suppliers.items():
        product = product_by_url.get(url)
        if not product:
            continue
        for key in [
            "supplier_name_ko",
            "supplier_years_ko",
            "supplier_country_ko",
            "supplier_business_type_ko",
            "supplier_employee_count_ko",
            "supplier_response_time_ko",
            "supplier_on_time_delivery_rate_ko",
            "supplier_rating_ko",
            "supplier_total_review_order_count_ko",
            "supplier_verified_ko",
        ]:
            supplier[key] = product.get(key, "")
    SUPPLIERS_JSON.write_text(json.dumps(suppliers, ensure_ascii=False, indent=2), encoding="utf-8")


def update_readme() -> None:
    text = README.read_text(encoding="utf-8")
    replacements = {
        "- `supplier_name`: Alibaba supplier/company name shown on the product detail page.": "- `supplier_name`, `supplier_name_ko`: Alibaba supplier/company name and Korean display name.",
        "- `supplier_years`, `supplier_years_text`: Alibaba join/supplier tenure.": "- `supplier_years`, `supplier_years_text`, `supplier_years_ko`: Alibaba join/supplier tenure.",
        "- `supplier_country`: supplier registered country/region code.": "- `supplier_country`, `supplier_country_ko`: supplier registered country/region code and Korean label.",
        "- `supplier_business_type`, `supplier_employee_count`: supplier profile attributes when exposed.": "- `supplier_business_type`, `supplier_business_type_ko`, `supplier_employee_count`, `supplier_employee_count_ko`: supplier profile attributes.",
        "- `supplier_response_time`, `supplier_on_time_delivery_rate`, `supplier_rating`, `supplier_total_review_order_count`: public supplier performance fields when exposed.": "- `supplier_response_time`, `supplier_response_time_ko`, `supplier_on_time_delivery_rate`, `supplier_on_time_delivery_rate_ko`, `supplier_rating`, `supplier_rating_ko`, `supplier_total_review_order_count`, `supplier_total_review_order_count_ko`: public supplier performance fields.",
        "- `supplier_verified`: whether the detail page exposes pass-assessment/verified signal.": "- `supplier_verified`, `supplier_verified_ko`: whether the detail page exposes pass-assessment/verified signal.",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    note = "- Korean supplier fields are display translations/transliterations for Korean-facing review; original Alibaba supplier fields are preserved."
    if note not in text:
        text = text.replace(
            "- Supplier fields are collected from public Alibaba.com product detail pages and may change over time.\n",
            "- Supplier fields are collected from public Alibaba.com product detail pages and may change over time.\n"
            f"{note}\n",
        )
    README.write_text(text, encoding="utf-8")


def main() -> None:
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    products = payload["products"]
    for product in products:
        enrich_product(product)

    payload["metadata"]["supplier_korean_fields"] = {
        "source": "Generated from supplier fields in data/products.json",
        "note": "Korean supplier values are display translations/transliterations. Original Alibaba supplier values are preserved.",
        "fields": [
            "supplier_name_ko",
            "supplier_years_ko",
            "supplier_country_ko",
            "supplier_business_type_ko",
            "supplier_employee_count_ko",
            "supplier_response_time_ko",
            "supplier_on_time_delivery_rate_ko",
            "supplier_rating_ko",
            "supplier_total_review_order_count_ko",
            "supplier_verified_ko",
        ],
    }

    PRODUCTS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_category_files(payload)
    update_suppliers_cache(products)
    write_csv(products)
    update_readme()

    missing = [product["id"] for product in products if not product.get("supplier_name_ko")]
    print(f"Korean supplier fields added to {len(products)} products")
    print(f"Missing supplier_name_ko: {len(missing)}")
    if missing:
        print(", ".join(missing[:20]))


if __name__ == "__main__":
    main()
