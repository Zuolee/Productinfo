#!/usr/bin/env python3
import html
import json
import re
import sys
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image

from add_memory_cards import (
    HEADERS,
    clean_title,
    extract_products,
    fetch_rates,
    format_krw,
    format_moq,
    image_url,
    product_url,
)
from enrich_suppliers import (
    NUMBER_FIELDS,
    STRING_FIELDS,
    match_number,
    match_string,
)
from sync_category_files import write_category_files


REPO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_DIR / "data"
IMAGE_DIR = REPO_DIR / "images"
PRODUCTS_JSON = DATA_DIR / "products.json"
SUPPLIERS_JSON = DATA_DIR / "suppliers.json"

TARGET_COUNT = 30

CATEGORIES = {
    "nail-polish": {
        "category_id": "nail-polish",
        "category_zh": "指甲油",
        "category_ko": "네일 폴리시",
        "category_en": "Nail Polish",
        "image_dir": "nail_polish",
        "image_prefix": "nail_polish",
        "queries": [
            "nail polish gel polish msds wholesale",
            "uv gel nail polish private label",
            "nail polish gel lacquer supplier ce msds",
            "non toxic nail polish wholesale",
        ],
    },
    "safety-helmets": {
        "category_id": "safety-helmets",
        "category_zh": "安全帽",
        "category_ko": "안전모",
        "category_en": "Safety Helmets",
        "image_dir": "safety_helmets",
        "image_prefix": "safety_helmet",
        "queries": [
            "safety helmet construction hard hat ansi ce",
            "industrial safety helmet hard hat en397",
            "ppe safety helmet construction helmet wholesale",
            "abs safety hard hat helmet",
        ],
    },
    "pc-power-supplies": {
        "category_id": "pc-power-supplies",
        "category_zh": "电脑(PC)电源",
        "category_ko": "PC 전원공급장치",
        "category_en": "PC Power Supplies",
        "image_dir": "pc_power_supplies",
        "image_prefix": "pc_power_supply",
        "queries": [
            "pc power supply 80 plus atx psu",
            "computer power supply atx 500w 600w 80 plus",
            "gaming pc power supply unit psu",
            "switching power supply pc atx psu",
        ],
    },
    "bag-accessories": {
        "category_id": "bag-accessories",
        "category_zh": "主包配件",
        "category_ko": "가방 액세서리",
        "category_en": "Bag Accessories",
        "image_dir": "bag_accessories",
        "image_prefix": "bag_accessory",
        "queries": [
            "bag accessories handbag hardware wholesale",
            "handbag accessories metal buckle strap chain",
            "bag hardware accessories purse parts",
            "luggage bag accessories buckle handle strap",
        ],
    },
}


CERT_PATTERNS = [
    (r"\bCE\b", "CE"),
    (r"(?i)\brohs\b", "RoHS"),
    (r"(?i)\bfcc\b", "FCC"),
    (r"(?i)\bemc\b", "EMC"),
    (r"(?i)\bmsds\b", "MSDS"),
    (r"(?i)\bsgs\b", "SGS"),
    (r"(?i)\bfda\b", "FDA"),
    (r"(?i)\bgmp\b", "GMP"),
    (r"(?i)\biso ?9001\b", "ISO 9001"),
    (r"(?i)\biso\b", "ISO"),
    (r"(?i)\bansi\b", "ANSI"),
    (r"(?i)\ben ?397\b", "EN 397"),
    (r"(?i)\b80\\s*plus\b", "80 PLUS"),
    (r"(?i)\breach\b", "REACH"),
    (r"(?i)\bbsci\b", "BSCI"),
    (r"(?i)\boeko[- ]?tex\b", "OEKO-TEX"),
]


def visible_certs(product: dict) -> list[str]:
    values = []
    for cert in product.get("certifications", []) or []:
        if cert.get("text"):
            values.append(cert["text"])
        for icon in cert.get("prefixIcons", []) or []:
            if icon.get("name"):
                values.append(icon["name"])

    title = clean_title(product.get("title", ""))
    for pattern, label in CERT_PATTERNS:
        if re.search(pattern, title) and label not in values:
            values.append(label)

    normalized = []
    for value in values:
        value = html.unescape(str(value)).strip()
        value = value.replace("ROHS", "RoHS")
        if value and value not in normalized:
            normalized.append(value)
    return normalized or ["Listing not specified"]


def is_relevant(category_id: str, title: str) -> bool:
    lower = title.lower()
    if category_id == "nail-polish":
        return "nail" in lower and any(token in lower for token in ["polish", "gel", "varnish", "lacquer", "manicure"])
    if category_id == "safety-helmets":
        return any(token in lower for token in ["safety helmet", "hard hat", "construction helmet", "protective helmet"])
    if category_id == "pc-power-supplies":
        return any(token in lower for token in ["power supply", "psu"]) and any(
            token in lower for token in ["pc", "atx", "computer", "gaming", "server", "desktop"]
        )
    if category_id == "bag-accessories":
        return any(token in lower for token in ["bag", "handbag", "purse", "luggage"]) and any(
            token in lower for token in ["accessor", "hardware", "buckle", "strap", "chain", "handle", "tag", "logo", "parts"]
        )
    return True


def unique_features(values: list[str], limit: int = 4) -> str:
    unique = []
    for value in values:
        if value and value not in unique:
            unique.append(value)
    return "·".join(unique[:limit])


def extract_watts(title: str) -> str:
    values = re.findall(r"\b(?:[2-9]\d{2,3})\s*w\b", title, flags=re.I)
    return "/".join(dict.fromkeys(value.upper().replace(" ", "") for value in values[:4]))


def korean_name(category_id: str, title: str) -> str:
    lower = title.lower()
    brand_match = re.match(r"([A-Z][A-Za-z0-9+\\-]{2,})\\b", title)
    brand = brand_match.group(1) if brand_match else ""

    if category_id == "nail-polish":
        features = []
        if "uv" in lower:
            features.append("UV")
        if "gel" in lower:
            features.append("젤")
        if "poly" in lower or "acrygel" in lower:
            features.append("폴리젤")
        if "private label" in lower or "custom" in lower:
            features.append("맞춤 라벨")
        if "non toxic" in lower or "vegan" in lower:
            features.append("저자극")
        if "set" in lower or "kit" in lower:
            features.append("세트")
        prefix = f"{brand} " if brand else ""
        suffix = f" ({unique_features(features)})" if features else ""
        return f"{prefix}네일 폴리시{suffix}"

    if category_id == "safety-helmets":
        features = []
        for token, label in [("abs", "ABS"), ("hdpe", "HDPE"), ("ansi", "ANSI"), ("en 397", "EN397"), ("ce", "CE")]:
            if token in lower:
                features.append(label)
        if "full brim" in lower:
            features.append("풀브림")
        if "visor" in lower or "goggle" in lower:
            features.append("고글/바이저")
        prefix = f"{brand} " if brand else ""
        suffix = f" ({unique_features(features)})" if features else ""
        return f"{prefix}산업용 안전모{suffix}"

    if category_id == "pc-power-supplies":
        features = []
        watts = extract_watts(title)
        if watts:
            features.append(watts)
        if "80 plus" in lower:
            features.append("80 PLUS")
        if "atx" in lower:
            features.append("ATX")
        if "modular" in lower:
            features.append("모듈러")
        if "gaming" in lower:
            features.append("게이밍")
        prefix = f"{brand} " if brand else ""
        suffix = f" ({unique_features(features)})" if features else ""
        return f"{prefix}PC 전원공급장치{suffix}"

    if category_id == "bag-accessories":
        features = []
        for token, label in [
            ("strap", "스트랩"),
            ("chain", "체인"),
            ("buckle", "버클"),
            ("handle", "손잡이"),
            ("logo", "로고"),
            ("tag", "태그"),
            ("metal", "금속"),
            ("leather", "가죽"),
        ]:
            if token in lower:
                features.append(label)
        suffix = f" ({unique_features(features)})" if features else ""
        return f"가방 액세서리{suffix}"

    return title


def fetch_candidates(category: dict) -> list[dict]:
    candidates = []
    seen = set()
    for query in category["queries"]:
        url = "https://www.alibaba.com/trade/search?SearchText=" + quote(query)
        response = requests.get(url, headers=HEADERS, timeout=45)
        response.raise_for_status()
        found = extract_products(response.text)
        print(f"{category['category_id']} query='{query}' extracted={len(found)}", flush=True)
        for product in found:
            product_id = str(product.get("productId"))
            if product_id not in seen:
                seen.add(product_id)
                candidates.append(product)
        time.sleep(0.25)
    return candidates


def select_products(category: dict, candidates: list[dict]) -> list[dict]:
    filtered = []
    for product in candidates:
        title = clean_title(product.get("title", ""))
        if title and is_relevant(category["category_id"], title):
            filtered.append(product)

    filtered.sort(
        key=lambda product: (
            visible_certs(product) == ["Listing not specified"],
            not product.get("price"),
            product.get("productId"),
        )
    )
    return filtered[:TARGET_COUNT]


def download_image(url: str, target: Path) -> None:
    response = requests.get(url, headers=HEADERS, timeout=45)
    response.raise_for_status()
    if len(response.content) < 1000:
        raise RuntimeError(f"Image too small: {url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(BytesIO(response.content)) as image:
        image.load()
        converted = image.convert("RGBA") if image.mode in {"RGBA", "LA", "P"} else image.convert("RGB")
        converted.save(target, format="PNG", optimize=True)


def empty_supplier(source: str) -> dict:
    supplier = {key: "" for key in STRING_FIELDS}
    supplier.update({key: "" for key in NUMBER_FIELDS})
    supplier["supplier_verified"] = False
    supplier["supplier_source"] = source
    return supplier


def fetch_supplier_fast(url: str) -> dict:
    last_error = ""
    for attempt in range(2):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=(8, 12),
                stream=True,
            )
            response.raise_for_status()
            chunks = []
            total = 0
            for chunk in response.iter_content(chunk_size=65536, decode_unicode=True):
                if not chunk:
                    continue
                chunks.append(chunk)
                total += len(chunk)
                if total >= 3_000_000:
                    break
            source = "".join(chunks)
            supplier = {}
            for output_key, page_key in STRING_FIELDS.items():
                supplier[output_key] = match_string(source, page_key)
            for output_key, page_key in NUMBER_FIELDS.items():
                supplier[output_key] = match_number(source, page_key)
            supplier["supplier_verified"] = bool(
                match_string(source, "companyHasPassAssessment")
                or re.search(r'"companyHasPassAssessment":true', source)
            )
            supplier["supplier_source"] = "Alibaba product detail page"
            if not supplier["supplier_name"]:
                supplier["supplier_name"] = match_string(source, "company_name") or match_string(source, "supplierName")
            if not supplier["supplier_years_text"] and supplier["supplier_years"]:
                supplier["supplier_years_text"] = f"{supplier['supplier_years']} yrs"
            if not supplier["supplier_profile_url"]:
                supplier["supplier_profile_url"] = match_string(source, "supplierHref")
            if not supplier["supplier_home_url"]:
                supplier["supplier_home_url"] = match_string(source, "supplierHomeHref")
            return supplier
        except Exception as exc:
            last_error = str(exc)
            time.sleep(0.5 + attempt)
    return empty_supplier(f"Fetch failed: {last_error}")


def build_products(category: dict, rates: dict[str, float]) -> list[dict]:
    selected = select_products(category, fetch_candidates(category))
    if len(selected) != TARGET_COUNT:
        raise RuntimeError(f"Expected {TARGET_COUNT} {category['category_id']} products, got {len(selected)}")

    products = []
    for index, product in enumerate(selected, start=1):
        title = clean_title(product.get("title", ""))
        image_file = f"images/{category['image_dir']}/{category['image_prefix']}_{index:02d}.png"
        download_image(image_url(product), REPO_DIR / image_file)
        products.append(
            {
                "id": f"{category['category_id']}-{index:02d}",
                "category_id": category["category_id"],
                "category_zh": category["category_zh"],
                "category_ko": category["category_ko"],
                "category_en": category["category_en"],
                "category_index": index,
                "image_file": image_file,
                "image_alt": korean_name(category["category_id"], title),
                "korean_product_name": korean_name(category["category_id"], title),
                "english_product_name": title,
                "price_krw": format_krw(product.get("price", ""), rates),
                "moq": format_moq(product.get("moq", "")),
                "certificates": visible_certs(product),
                "source_url": product_url(product),
            }
        )
    return products


def ordered_categories(products: list[dict]) -> list[dict]:
    categories = {}
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
    return list(categories.values())


def enrich_new_products(products: list[dict]) -> None:
    supplier_cache = {}
    if SUPPLIERS_JSON.exists():
        supplier_cache = json.loads(SUPPLIERS_JSON.read_text(encoding="utf-8"))

    for index, product in enumerate(products, start=1):
        url = product["source_url"]
        print(f"supplier [{index:03d}/{len(products)}] {product['id']}", flush=True)
        supplier = supplier_cache.get(url) or fetch_supplier_fast(url)
        product.update(supplier)
        supplier_cache[url] = supplier
        SUPPLIERS_JSON.write_text(
            json.dumps(supplier_cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        time.sleep(0.2)

    SUPPLIERS_JSON.write_text(
        json.dumps(supplier_cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    existing = [
        product
        for product in payload["products"]
        if product["category_id"] not in CATEGORIES
    ]

    rates, rate_date = fetch_rates()
    print(f"Rates: 1 CNY = ₩{rates['CNY']:,.2f}; 1 USD = ₩{rates['USD']:,.2f}; rate date {rate_date}", flush=True)

    new_products = []
    for category in CATEGORIES.values():
        print(f"Building category: {category['category_id']}", flush=True)
        new_products.extend(build_products(category, rates))

    enrich_new_products(new_products)

    products = existing + new_products
    payload["products"] = products
    payload["metadata"]["total_products"] = len(products)
    payload["metadata"]["categories"] = ordered_categories(products)
    payload["metadata"]["latest_added_categories_exchange_rate"] = (
        f"1 CNY = ₩{rates['CNY']:,.2f}; 1 USD = ₩{rates['USD']:,.2f}; rate date {rate_date}"
    )
    payload["metadata"]["source"] = "Alibaba.com public product listings collected into local structured dataset"
    payload["metadata"]["generated_from"] = "local HTML workbook plus supplemental Alibaba search scripts"

    PRODUCTS_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_category_files(payload)

    print(f"Added products: {len(new_products)}", flush=True)
    print(f"Dataset total: {len(products)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
