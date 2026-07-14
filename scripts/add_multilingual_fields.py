#!/usr/bin/env python3
import json
import time
from pathlib import Path

import requests

from sync_category_files import write_category_files


REPO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_DIR / "data"
PRODUCTS_JSON = DATA_DIR / "products.json"

LANGUAGES = [
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

TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
}


def chunks(items: list[str], max_items: int = 20, max_chars: int = 3500) -> list[list[str]]:
    batches = []
    current = []
    current_chars = 0
    for item in items:
        length = len(item) + 1
        if current and (len(current) >= max_items or current_chars + length > max_chars):
            batches.append(current)
            current = []
            current_chars = 0
        current.append(item)
        current_chars += length
    if current:
        batches.append(current)
    return batches


def request_translation(text: str, target_language: str) -> str:
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": target_language,
        "dt": "t",
        "q": text,
    }
    last_error = None
    for attempt in range(4):
        try:
            response = requests.get(TRANSLATE_URL, params=params, headers=HEADERS, timeout=30)
            response.raise_for_status()
            data = response.json()
            return "".join(part[0] for part in data[0] if part and part[0]).strip()
        except Exception as exc:  # noqa: BLE001 - keep batch job resilient
            last_error = exc
            time.sleep(0.8 * (attempt + 1))
    raise RuntimeError(f"Translation failed for {target_language}: {last_error}")


def translate_batch(texts: list[str], target_language: str) -> list[str]:
    if not texts:
        return []
    if len(texts) == 1:
        return [request_translation(texts[0], target_language)]

    joined = "\n".join(texts)
    translated = request_translation(joined, target_language)
    lines = [line.strip() for line in translated.splitlines()]
    if len(lines) == len(texts):
        return lines

    # Some languages occasionally merge newline segments. Fall back to exact one-by-one mapping.
    results = []
    for text in texts:
        results.append(request_translation(text, target_language))
        time.sleep(0.05)
    return results


def translate_many(texts: list[str], target_language: str) -> dict[str, str]:
    unique_texts = list(dict.fromkeys(text for text in texts if text))
    translations: dict[str, str] = {}
    batches = chunks(unique_texts)
    for index, batch in enumerate(batches, start=1):
        translated = translate_batch(batch, target_language)
        translations.update(dict(zip(batch, translated)))
        print(
            f"translated {target_language} batch {index}/{len(batches)} ({len(batch)} texts)",
            flush=True,
        )
        time.sleep(0.12)
    return translations


def main() -> None:
    payload = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    products = payload["products"]

    category_names = [
        product.get("category_name_en") or product.get("category_en", "")
        for product in products
    ]
    product_names = [
        product.get("product_name_en") or product.get("english_product_name", "")
        for product in products
    ]

    for language_code, language_name in LANGUAGES:
        print(f"Language {language_code} ({language_name})", flush=True)
        category_translations = translate_many(category_names, language_code)
        product_translations = translate_many(product_names, language_code)

        for product in products:
            category_en = product.get("category_name_en") or product.get("category_en", "")
            product_en = product.get("product_name_en") or product.get("english_product_name", "")
            category_value = category_translations.get(category_en, category_en)
            product_value = product_translations.get(product_en, product_en)

            product[f"category_name_{language_code}"] = category_value
            product[f"product_name_{language_code}"] = product_value
            product.setdefault("localized", {})[language_code] = {
                "category_name": category_value,
                "product_name": product_value,
                "supplier_name": product.get("supplier_name", ""),
                "supplier_country": product.get("supplier_country", ""),
            }

        PRODUCTS_JSON.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        write_category_files(payload)

    payload["metadata"]["additional_languages"] = [
        {"code": code, "name": name} for code, name in LANGUAGES
    ]
    payload["metadata"]["multilingual_fields"] = {
        "note": "Product and category display values are available under product.localized and as flat category_name_<lang>/product_name_<lang> fields.",
        "object": "localized",
        "languages": ["ko", "en", *[code for code, _name in LANGUAGES]],
    }

    PRODUCTS_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_category_files(payload)
    print(f"Updated multilingual fields for {len(products)} products")


if __name__ == "__main__":
    main()
