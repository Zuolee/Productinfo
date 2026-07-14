#!/usr/bin/env python3
import json
import re
import time
from pathlib import Path

import requests

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
from add_more_categories import download_image, fetch_supplier_fast, visible_certs
from sync_category_files import write_category_files


REPO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_DIR / "data"
PRODUCTS_JSON = DATA_DIR / "products.json"
SUPPLIERS_JSON = DATA_DIR / "suppliers.json"
TARGET_COUNT = 30


CATEGORIES = [
    {
        "category_id": "smart-watches",
        "category_zh": "智能手表",
        "category_ko": "스마트워치",
        "category_en": "Smart Watches",
        "queries": ["smart watch bluetooth calling wholesale", "smartwatch fitness tracker watch supplier", "android smart watch waterproof wholesale"],
        "tokens": ["smart watch", "smartwatch", "fitness tracker"],
        "image_prefix": "smart_watch",
    },
    {
        "category_id": "bluetooth-speakers",
        "category_zh": "蓝牙音箱",
        "category_ko": "블루투스 스피커",
        "category_en": "Bluetooth Speakers",
        "queries": ["bluetooth speaker portable waterproof wholesale", "wireless bluetooth speaker bass supplier", "mini bluetooth speaker custom logo"],
        "tokens": ["bluetooth speaker", "wireless speaker", "portable speaker"],
        "image_prefix": "bluetooth_speaker",
    },
    {
        "category_id": "air-purifiers",
        "category_zh": "空气净化器",
        "category_ko": "공기청정기",
        "category_en": "Air Purifiers",
        "queries": ["air purifier hepa filter home wholesale", "portable air purifier hepa supplier", "room air purifier negative ion wholesale"],
        "tokens": ["air purifier", "hepa", "purifier"],
        "image_prefix": "air_purifier",
    },
    {
        "category_id": "electric-toothbrushes",
        "category_zh": "电动牙刷",
        "category_ko": "전동 칫솔",
        "category_en": "Electric Toothbrushes",
        "queries": ["electric toothbrush sonic rechargeable wholesale", "sonic electric toothbrush adult supplier", "smart electric toothbrush waterproof"],
        "tokens": ["electric toothbrush", "sonic toothbrush", "toothbrush"],
        "image_prefix": "electric_toothbrush",
    },
    {
        "category_id": "yoga-mats",
        "category_zh": "瑜伽垫",
        "category_ko": "요가 매트",
        "category_en": "Yoga Mats",
        "queries": ["yoga mat tpe non slip wholesale", "custom logo yoga mat supplier", "eco friendly yoga mat cork rubber"],
        "tokens": ["yoga mat", "exercise mat", "pilates mat"],
        "image_prefix": "yoga_mat",
    },
    {
        "category_id": "pet-grooming-tools",
        "category_zh": "宠物美容工具",
        "category_ko": "반려동물 미용 도구",
        "category_en": "Pet Grooming Tools",
        "queries": ["pet grooming tools dog brush wholesale", "dog grooming kit pet clipper supplier", "pet grooming comb brush nail clipper"],
        "tokens": ["pet grooming", "dog grooming", "pet brush", "pet clipper"],
        "image_prefix": "pet_grooming_tool",
    },
    {
        "category_id": "coffee-machines",
        "category_zh": "咖啡机",
        "category_ko": "커피머신",
        "category_en": "Coffee Machines",
        "queries": ["coffee machine espresso maker wholesale", "automatic coffee machine supplier", "capsule coffee machine wholesale"],
        "tokens": ["coffee machine", "espresso", "coffee maker"],
        "image_prefix": "coffee_machine",
    },
    {
        "category_id": "solar-panels",
        "category_zh": "太阳能板",
        "category_ko": "태양광 패널",
        "category_en": "Solar Panels",
        "queries": ["solar panel monocrystalline wholesale", "portable solar panel supplier", "pv solar panel 400w 550w"],
        "tokens": ["solar panel", "pv panel", "monocrystalline"],
        "image_prefix": "solar_panel",
    },
    {
        "category_id": "led-strip-lights",
        "category_zh": "LED灯带",
        "category_ko": "LED 스트립 조명",
        "category_en": "LED Strip Lights",
        "queries": ["led strip light rgb wholesale", "waterproof led strip lights supplier", "cob led strip light 12v 24v"],
        "tokens": ["led strip", "strip light", "led tape"],
        "image_prefix": "led_strip_light",
    },
    {
        "category_id": "kitchen-knives",
        "category_zh": "厨房刀具",
        "category_ko": "주방 칼",
        "category_en": "Kitchen Knives",
        "queries": ["kitchen knife chef knife wholesale", "stainless steel kitchen knife set supplier", "damascus chef knife kitchen knives"],
        "tokens": ["kitchen knife", "chef knife", "knife set", "knives"],
        "image_prefix": "kitchen_knife",
    },
    {
        "category_id": "backpacks",
        "category_zh": "背包",
        "category_ko": "백팩",
        "category_en": "Backpacks",
        "queries": ["backpack school travel laptop wholesale", "custom backpack bag supplier", "waterproof laptop backpack wholesale"],
        "tokens": ["backpack", "school bag", "laptop bag"],
        "image_prefix": "backpack",
    },
    {
        "category_id": "car-phone-holders",
        "category_zh": "车载手机支架",
        "category_ko": "차량용 휴대폰 거치대",
        "category_en": "Car Phone Holders",
        "queries": ["car phone holder mount wholesale", "magnetic car phone holder supplier", "dashboard phone holder car mount"],
        "tokens": ["car phone holder", "phone holder", "car mount"],
        "image_prefix": "car_phone_holder",
    },
    {
        "category_id": "baby-strollers",
        "category_zh": "婴儿车",
        "category_ko": "유모차",
        "category_en": "Baby Strollers",
        "queries": ["baby stroller foldable wholesale", "lightweight baby stroller supplier", "baby pram stroller travel system"],
        "tokens": ["baby stroller", "stroller", "baby pram"],
        "image_prefix": "baby_stroller",
    },
    {
        "category_id": "office-chairs",
        "category_zh": "办公椅",
        "category_ko": "사무용 의자",
        "category_en": "Office Chairs",
        "queries": ["office chair ergonomic wholesale", "mesh office chair supplier", "ergonomic desk chair adjustable"],
        "tokens": ["office chair", "ergonomic chair", "desk chair"],
        "image_prefix": "office_chair",
    },
    {
        "category_id": "stainless-water-bottles",
        "category_zh": "不锈钢水杯",
        "category_ko": "스테인리스 물병",
        "category_en": "Stainless Steel Water Bottles",
        "queries": ["stainless steel water bottle wholesale", "insulated water bottle custom logo", "vacuum flask stainless bottle supplier"],
        "tokens": ["water bottle", "stainless", "vacuum flask", "insulated bottle"],
        "image_prefix": "stainless_water_bottle",
    },
    {
        "category_id": "wireless-earbuds",
        "category_zh": "无线耳机",
        "category_ko": "무선 이어버드",
        "category_en": "Wireless Earbuds",
        "queries": ["wireless earbuds bluetooth tws wholesale", "tws earbuds noise cancelling supplier", "bluetooth earphones wireless earbuds"],
        "tokens": ["wireless earbuds", "tws", "bluetooth earphones", "earbuds"],
        "image_prefix": "wireless_earbud",
    },
    {
        "category_id": "makeup-brushes",
        "category_zh": "化妆刷",
        "category_ko": "메이크업 브러시",
        "category_en": "Makeup Brushes",
        "queries": ["makeup brush set wholesale", "cosmetic makeup brushes custom logo", "professional makeup brush supplier"],
        "tokens": ["makeup brush", "cosmetic brush", "brush set"],
        "image_prefix": "makeup_brush",
    },
    {
        "category_id": "garden-tools",
        "category_zh": "园艺工具",
        "category_ko": "원예 도구",
        "category_en": "Garden Tools",
        "queries": ["garden tools set wholesale", "gardening hand tools supplier", "pruning shears garden tool set"],
        "tokens": ["garden tool", "gardening", "pruning", "shears"],
        "image_prefix": "garden_tool",
    },
    {
        "category_id": "electric-bicycles",
        "category_zh": "电动自行车",
        "category_ko": "전기 자전거",
        "category_en": "Electric Bicycles",
        "queries": ["electric bicycle e bike wholesale", "folding electric bike supplier", "fat tire electric bicycle"],
        "tokens": ["electric bicycle", "e bike", "ebike", "electric bike"],
        "image_prefix": "electric_bicycle",
    },
    {
        "category_id": "plastic-food-containers",
        "category_zh": "食品保鲜盒",
        "category_ko": "식품 보관용기",
        "category_en": "Plastic Food Containers",
        "queries": ["plastic food container lunch box wholesale", "food storage container plastic supplier", "meal prep food container wholesale"],
        "tokens": ["food container", "food storage", "lunch box", "meal prep"],
        "image_prefix": "plastic_food_container",
    },
]


def is_relevant(category: dict, title: str) -> bool:
    lower = title.lower()
    return any(token in lower for token in category["tokens"])


def korean_name(category: dict, title: str) -> str:
    lower = title.lower()
    features = []
    for token, label in [
        ("waterproof", "방수"),
        ("wireless", "무선"),
        ("portable", "휴대용"),
        ("custom", "맞춤형"),
        ("rechargeable", "충전식"),
        ("stainless", "스테인리스"),
        ("foldable", "접이식"),
        ("ergonomic", "인체공학"),
        ("smart", "스마트"),
        ("rgb", "RGB"),
        ("solar", "태양광"),
        ("eco", "친환경"),
        ("bluetooth", "블루투스"),
        ("automatic", "자동"),
    ]:
        if token in lower:
            features.append(label)
    suffix = f" ({'·'.join(dict.fromkeys(features[:4]))})" if features else ""
    return f"{category['category_ko']}{suffix}"


def fetch_candidates(category: dict) -> list[dict]:
    candidates = []
    seen = set()
    for query in category["queries"]:
        url = "https://www.alibaba.com/trade/search?SearchText=" + requests.utils.quote(query)
        response = requests.get(url, headers=HEADERS, timeout=45)
        response.raise_for_status()
        found = extract_products(response.text)
        print(f"{category['category_id']} query='{query}' extracted={len(found)}", flush=True)
        for product in found:
            product_id = str(product.get("productId"))
            if product_id not in seen:
                seen.add(product_id)
                candidates.append(product)
        time.sleep(0.2)
    return candidates


def select_products(category: dict, candidates: list[dict]) -> list[dict]:
    selected = []
    for product in candidates:
        title = clean_title(product.get("title", ""))
        if title and is_relevant(category, title):
            selected.append(product)
    selected.sort(
        key=lambda product: (
            visible_certs(product) == ["Listing not specified"],
            not product.get("price"),
            product.get("productId"),
        )
    )
    return selected[:TARGET_COUNT]


def build_products(category: dict, rates: dict[str, float]) -> list[dict]:
    selected = select_products(category, fetch_candidates(category))
    if len(selected) != TARGET_COUNT:
        raise RuntimeError(f"Expected {TARGET_COUNT} {category['category_id']} products, got {len(selected)}")

    products = []
    image_dir = category["category_id"].replace("-", "_")
    for index, product in enumerate(selected, start=1):
        title = clean_title(product.get("title", ""))
        image_file = f"images/{image_dir}/{category['image_prefix']}_{index:02d}.png"
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
                "image_alt": korean_name(category, title),
                "korean_product_name": korean_name(category, title),
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


def enrich_suppliers(products: list[dict]) -> None:
    supplier_cache = {}
    if SUPPLIERS_JSON.exists():
        supplier_cache = json.loads(SUPPLIERS_JSON.read_text(encoding="utf-8"))

    for index, product in enumerate(products, start=1):
        url = product["source_url"]
        print(f"supplier [{index:03d}/{len(products)}] {product['id']}", flush=True)
        supplier = supplier_cache.get(url) or fetch_supplier_fast(url)
        product.update(supplier)
        supplier_cache[url] = supplier
        if index % 10 == 0:
            SUPPLIERS_JSON.write_text(json.dumps(supplier_cache, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(0.12)

    SUPPLIERS_JSON.write_text(json.dumps(supplier_cache, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    new_category_ids = {category["category_id"] for category in CATEGORIES}
    existing = [product for product in payload["products"] if product["category_id"] not in new_category_ids]

    rates, rate_date = fetch_rates()
    print(f"Rates: 1 CNY = ₩{rates['CNY']:,.2f}; 1 USD = ₩{rates['USD']:,.2f}; rate date {rate_date}", flush=True)

    new_products = []
    for category in CATEGORIES:
        print(f"Building category: {category['category_id']}", flush=True)
        new_products.extend(build_products(category, rates))

    enrich_suppliers(new_products)

    products = existing + new_products
    payload["products"] = products
    payload["metadata"]["total_products"] = len(products)
    payload["metadata"]["categories"] = ordered_categories(products)
    payload["metadata"]["latest_twenty_categories_exchange_rate"] = (
        f"1 CNY = ₩{rates['CNY']:,.2f}; 1 USD = ₩{rates['USD']:,.2f}; rate date {rate_date}"
    )
    payload["metadata"]["source"] = "Alibaba.com public product listings collected into local structured dataset"
    payload["metadata"]["generated_from"] = "local HTML workbook plus supplemental Alibaba search scripts"

    PRODUCTS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_category_files(payload)
    print(f"Added products: {len(new_products)}", flush=True)
    print(f"Dataset total: {len(products)}", flush=True)


if __name__ == "__main__":
    main()
