#!/usr/bin/env python3
import csv
import html
import json
import re
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image

from sync_category_files import write_category_files


REPO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_DIR / "data"
IMAGE_DIR = REPO_DIR / "images"
PRODUCTS_JSON = DATA_DIR / "products.json"
PRODUCTS_CSV = DATA_DIR / "products.csv"
README = REPO_DIR / "README.md"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
QUERIES = [
    "memory card micro sd card ce rohs",
    "tf card memory card microsd wholesale",
    "sd memory card 128gb 256gb 512gb",
    "micro sd card class 10 memory card",
]

CATEGORY = {
    "category_id": "memory-cards",
    "category_zh": "存储卡",
    "category_ko": "메모리 카드",
    "category_en": "Memory Cards",
}

CATEGORY_ORDER = [
    "power-bank",
    "womens-dresses",
    "cooling-mattresses",
    "desktop-organizers",
    "memory-cards",
]

TAG_RE = re.compile(r"<[^>]+>")


def clean_title(value: str) -> str:
    value = html.unescape(TAG_RE.sub("", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def extract_products(search_html: str) -> list[dict]:
    products = []
    for match in re.finditer(r'"productId":"\d+"', search_html):
        position = match.start()
        start = max(
            search_html.rfind(marker, 0, position)
            for marker in ['{"badges"', '{"certifications"', '{"adInfo"']
        )
        if start < 0:
            start = search_html.rfind("{", 0, position)

        depth = 0
        in_string = False
        escaped = False
        end = None
        for index, char in enumerate(search_html[start:], start):
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            else:
                if char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        end = index + 1
                        break
        if not end:
            continue
        try:
            product = json.loads(search_html[start:end])
        except json.JSONDecodeError:
            continue
        if "productId" in product and "title" in product:
            products.append(product)

    unique = []
    seen = set()
    for product in products:
        product_id = str(product.get("productId"))
        if product_id not in seen:
            seen.add(product_id)
            unique.append(product)
    return unique


def visible_certs(product: dict) -> list[str]:
    values = []
    for cert in product.get("certifications", []) or []:
        if cert.get("text"):
            values.append(cert["text"])
        for icon in cert.get("prefixIcons", []) or []:
            if icon.get("name"):
                values.append(icon["name"])

    title = clean_title(product.get("title", ""))
    checks = [
        (r"\bCE\b", "CE"),
        (r"(?i)\brohs\b", "RoHS"),
        (r"(?i)\bfcc\b", "FCC"),
        (r"(?i)\bemc\b", "EMC"),
        (r"(?i)\bdeclaration of conformity\b", "Declaration of Conformity"),
    ]
    for pattern, label in checks:
        if re.search(pattern, title) and label not in values:
            values.append(label)

    normalized = []
    for value in values:
        value = value.strip()
        value = value.replace("ROHS", "RoHS")
        if value not in normalized:
            normalized.append(value)
    return normalized or ["Listing not specified"]


def product_url(product: dict) -> str:
    url = (product.get("productUrl") or "").replace("\\/", "/")
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = "https://www.alibaba.com" + url
    return url.split("?")[0]


def image_url(product: dict) -> str:
    url = (product.get("mainImage") or (product.get("multiImage") or [""])[0]).replace("\\/", "/")
    if url.startswith("//"):
        url = "https:" + url
    return url


def fetch_rates() -> tuple[dict[str, float], str]:
    rates = {}
    dates = set()
    for currency in ["CNY", "USD"]:
        response = requests.get(
            f"https://api.frankfurter.app/latest?from={currency}&to=KRW",
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        rates[currency] = float(data["rates"]["KRW"])
        dates.add(data["date"])
    return rates, ", ".join(sorted(dates))


def format_krw(price: str, rates: dict[str, float]) -> str:
    text = (price or "").replace("\xa0", "").replace(",", "").strip()
    currency = "USD" if "$" in text or "US$" in text else "CNY"
    numbers = [float(number) for number in re.findall(r"\d+(?:\.\d+)?", text)]
    if not numbers:
        return "Listing not specified"
    values = [round(number * rates[currency]) for number in numbers[:2]]
    if len(values) > 1 and values[0] != values[1]:
        return f"₩{values[0]:,}–{values[1]:,}"
    return f"₩{values[0]:,}"


def format_moq(moq: str) -> str:
    return (moq or "").replace("Min. order:", "").strip() or "Listing not specified"


def korean_name(title: str) -> str:
    lower = title.lower()
    capacity_matches = re.findall(r"\b(?:128mb|256mb|512mb|1gb|2gb|4gb|8gb|16gb|32gb|64gb|128gb|256gb|512gb|1tb|2tb)\b", title, flags=re.I)
    capacities = "/".join(dict.fromkeys(match.upper() for match in capacity_matches[:6]))

    parts = []
    if "sandisk" in lower:
        parts.append("SanDisk")
    elif "ceamere" in lower:
        parts.append("Ceamere")
    elif "microthink" in lower:
        parts.append("Microthink")
    elif "kissin" in lower:
        parts.append("KISSIN")

    if any(token in lower for token in ["micro", "tf", "mini sd"]):
        parts.append("마이크로 TF/SD")
    else:
        parts.append("SD")

    if capacities:
        parts.append(capacities)

    feature = []
    if "class 10" in lower or "c10" in lower:
        feature.append("Class 10")
    if "u3" in lower:
        feature.append("U3")
    if "a1" in lower:
        feature.append("A1")
    if "v30" in lower:
        feature.append("V30")
    if "v90" in lower:
        feature.append("V90")
    if "custom logo" in lower or "customization" in lower:
        feature.append("로고 맞춤")
    if "adapter" in lower:
        feature.append("어댑터 포함")
    if "industrial" in lower:
        feature.append("산업용")
    if "high speed" in lower or "high-speed" in lower:
        feature.append("고속")

    name = " ".join(parts) + " 메모리 카드"
    if feature:
        name += f" ({'·'.join(dict.fromkeys(feature[:4]))})"
    return name


def fetch_candidates() -> list[dict]:
    candidates = []
    seen = set()
    for query in QUERIES:
        url = "https://www.alibaba.com/trade/search?SearchText=" + quote(query)
        response = requests.get(url, headers=HEADERS, timeout=40)
        response.raise_for_status()
        for product in extract_products(response.text):
            product_id = str(product.get("productId"))
            if product_id not in seen:
                seen.add(product_id)
                candidates.append(product)
        time.sleep(0.2)
    return candidates


def select_products(candidates: list[dict]) -> list[dict]:
    filtered = []
    for product in candidates:
        title = clean_title(product.get("title", ""))
        lower = title.lower()
        if "card" not in lower:
            continue
        if not any(token in lower for token in ["memory", "sd", "tf", "microsd", "micro sd"]):
            continue
        filtered.append(product)

    filtered.sort(
        key=lambda product: (
            visible_certs(product) == ["Listing not specified"],
            "memory" not in clean_title(product.get("title", "")).lower(),
            product.get("productId"),
        )
    )
    return filtered[:30]


def download_image(url: str, target: Path) -> None:
    response = requests.get(url, headers=HEADERS, timeout=40)
    response.raise_for_status()
    if len(response.content) < 1000:
        raise RuntimeError(f"Image too small: {url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(BytesIO(response.content)) as image:
        image.load()
        if image.mode in {"RGBA", "LA"} or (
            image.mode == "P" and "transparency" in image.info
        ):
            converted = image.convert("RGBA")
        else:
            converted = image.convert("RGB")
        converted.save(target, format="PNG", optimize=True)


def build_memory_card_products() -> tuple[list[dict], str]:
    rates, rate_date = fetch_rates()
    selected = select_products(fetch_candidates())
    if len(selected) != 30:
        raise RuntimeError(f"Expected 30 memory card products, got {len(selected)}")

    products = []
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    for index, product in enumerate(selected, start=1):
        image_file = f"images/memory_cards/memory_card_{index:02d}.png"
        image_path = REPO_DIR / image_file
        download_image(image_url(product), image_path)
        title = clean_title(product.get("title", ""))
        products.append(
            {
                "id": f"memory-cards-{index:02d}",
                **CATEGORY,
                "category_index": index,
                "image_file": image_file,
                "image_alt": korean_name(title),
                "korean_product_name": korean_name(title),
                "english_product_name": title,
                "price_krw": format_krw(product.get("price", ""), rates),
                "moq": format_moq(product.get("moq", "")),
                "certificates": visible_certs(product),
                "source_url": product_url(product),
            }
        )

    return products, f"1 CNY = ₩{rates['CNY']:,.2f}; 1 USD = ₩{rates['USD']:,.2f}; rate date {rate_date}"


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
        "source_url",
    ]
    with PRODUCTS_CSV.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for product in products:
            row = dict(product)
            row["certificates"] = "; ".join(row["certificates"])
            writer.writerow(row)


def ordered_categories(products: list[dict]) -> list[dict]:
    categories = {}
    for product in products:
        categories[product["category_id"]] = {
            "category_id": product["category_id"],
            "category_zh": product["category_zh"],
            "category_ko": product["category_ko"],
            "category_en": product["category_en"],
            "count": 0,
        }
    for product in products:
        categories[product["category_id"]]["count"] += 1
    return [categories[key] for key in CATEGORY_ORDER if key in categories]


def write_json(products: list[dict], rate_note: str) -> None:
    payload = {
        "metadata": {
            "source": "Alibaba.com public product listings collected into local HTML/workbook and supplemental memory-card search results",
            "generated_from": "power_bank_products_krw.html plus scripts/add_memory_cards.py",
            "total_products": len(products),
            "categories": ordered_categories(products),
            "price_currency": "KRW",
            "latest_memory_card_exchange_rate": rate_note,
            "notes": [
                "source_url stores the Alibaba product detail page.",
                "image_file stores the relative path to the downloaded product main image.",
                "certificate values are taken from public listing badges or explicit title text; Listing not specified means the list page did not expose a concrete certificate.",
            ],
        },
        "products": products,
    }
    PRODUCTS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_category_files(payload)


def write_readme(products: list[dict]) -> None:
    lines = [
        "# Productinfo",
        "",
        "Structured Alibaba.com product information for Korea-market research.",
        "",
        "## Files",
        "",
        "- `data/products.json` — canonical structured data for agents and scripts.",
        "- `data/products.csv` — flat table version for spreadsheets or lightweight parsing.",
        "- `data/memory_cards.json` — memory card category rows generated from the supplemental Alibaba search.",
        "- `images/` — downloaded product main images referenced by `image_file`.",
        "- `exports/alibaba_products_with_images.xlsx` — Excel workbook with embedded product images.",
        "",
        "## Product counts",
        "",
        "| Category ID | 中文品类 | 한국어 | English | Count |",
        "|---|---|---|---|---:|",
    ]
    for category in ordered_categories(products):
        lines.append(
            f"| `{category['category_id']}` | {category['category_zh']} | {category['category_ko']} | {category['category_en']} | {category['count']} |"
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
            "- `image_alt`: image alt text from the source HTML or generated Korean product label.",
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
            "- KRW prices were converted in the source workbook or supplemental category script before this repository export.",
            "",
        ]
    )
    README.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    existing = [
        product
        for product in payload["products"]
        if product.get("category_id") != CATEGORY["category_id"]
    ]
    memory_cards, rate_note = build_memory_card_products()
    products = existing + memory_cards
    write_json(products, rate_note)
    write_csv(products)
    write_readme(products)
    print(f"Generated {len(memory_cards)} memory card products")
    print(f"Dataset total: {len(products)}")
    print(rate_note)


if __name__ == "__main__":
    main()
