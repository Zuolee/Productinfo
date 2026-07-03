# Productinfo

Structured Alibaba.com product information for Korea-market research.

## Files

- `data/products.json` — canonical structured data for agents and scripts.
- `data/products.csv` — flat table version for spreadsheets or lightweight parsing.
- `data/power_bank.json` — power bank category subset using the same `metadata` + `products` structure as `products.json`.
- `data/womens_dresses.json` — women's dresses category subset using the same `metadata` + `products` structure as `products.json`.
- `data/cooling_mattresses.json` — cooling mattresses category subset using the same `metadata` + `products` structure as `products.json`.
- `data/desktop_organizers.json` — desktop organizers category subset using the same `metadata` + `products` structure as `products.json`.
- `data/memory_cards.json` — memory cards category subset using the same `metadata` + `products` structure as `products.json`.
- `data/nail_polish.json` — nail polish category subset using the same `metadata` + `products` structure as `products.json`.
- `data/safety_helmets.json` — safety helmets category subset using the same `metadata` + `products` structure as `products.json`.
- `data/pc_power_supplies.json` — PC power supplies category subset using the same `metadata` + `products` structure as `products.json`.
- `data/jewelry_accessories.json` — jewelry accessories category subset using the same `metadata` + `products` structure as `products.json`.
- `data/suppliers.json` — supplier cache keyed by Alibaba product detail URL.
- `images/` — downloaded product main images converted to PNG and grouped by category.
  - `images/power_bank/`
  - `images/womens_dresses/`
  - `images/cooling_mattresses/`
  - `images/desktop_organizers/`
  - `images/memory_cards/`
  - `images/nail_polish/`
  - `images/safety_helmets/`
  - `images/pc_power_supplies/`
  - `images/jewelry_accessories/`
- `exports/alibaba_products_with_images.xlsx` — Excel workbook with embedded product images.

## Product counts

| Category ID | 中文品类 | 한국어 | English | Count |
|---|---|---|---|---:|
| `power-bank` | 移动电源 | 보조배터리 | Power Banks | 30 |
| `womens-dresses` | 女士连衣裙 | 여성 원피스 | Women's Dresses | 30 |
| `cooling-mattresses` | 凉感床垫 | 쿨링 매트리스 | Cooling Mattresses | 30 |
| `desktop-organizers` | 桌面整理柜 | 데스크 정리함 | Desktop Organizers | 30 |
| `memory-cards` | 存储卡 | 메모리 카드 | Memory Cards | 30 |
| `nail-polish` | 指甲油 | 네일 폴리시 | Nail Polish | 30 |
| `safety-helmets` | 安全帽 | 안전모 | Safety Helmets | 30 |
| `pc-power-supplies` | 电脑(PC)电源 | PC 전원공급장치 | PC Power Supplies | 30 |
| `jewelry-accessories` | 珠宝配件 | 주얼리 액세서리 | Jewelry Accessories | 30 |

Total products: **270**

## Schema

All category JSON files use the same top-level shape:

```json
{
  "metadata": {
    "dataset_type": "category_subset",
    "category": {
      "category_id": "...",
      "category_zh": "...",
      "category_ko": "...",
      "category_en": "...",
      "count": 30
    },
    "total_products": 30,
    "price_currency": "KRW",
    "image_storage": {
      "format": "PNG",
      "directory": "images/<category>/"
    },
    "multilingual_fields": {
      "object": "localized",
      "languages": ["ko", "en"]
    },
    "price_fields": {
      "currency": "KRW",
      "numeric_fields": ["price_krw_min", "price_krw_max"]
    }
  },
  "products": []
}
```

Each product row contains:

- `id`: stable product ID within this dataset.
- `category_id`, `category_zh`, `category_ko`, `category_en`: category labels.
- `category_index`: product number inside its category.
- `image_file`: relative path to the downloaded PNG main image under the matching category folder.
- `image_alt`: image alt text from the source HTML or generated Korean product label.
- `korean_product_name`, `product_name_ko`: Korean product title.
- `english_product_name`, `product_name_en`: English source/comparable product title.
- `category_name_ko`, `category_name_en`: explicit Korean and English category names.
- `localized`: separated Korean (`localized.ko`) and English/source (`localized.en`) display values for category, product, and supplier fields.
- `price_krw`: original KRW price display string.
- `price_krw_min`, `price_krw_max`: numeric KRW minimum and maximum price. Single prices use the same value for both fields.
- `price_krw_is_range`: whether the original display price was a range.
- `price`: structured KRW price object with `currency`, `display`, `min`, `max`, and `is_range`.
- `moq`: minimum order quantity.
- `certificates`: list of visible certificate labels.
- `supplier_name`, `supplier_name_ko`: Alibaba supplier/company name and Korean display name.
- `supplier_years`, `supplier_years_text`, `supplier_years_ko`: Alibaba join/supplier tenure.
- `supplier_country`, `supplier_country_ko`: supplier registered country/region code and Korean label.
- `supplier_profile_url`, `supplier_home_url`: Alibaba supplier profile/home links.
- `supplier_company_id`: Alibaba company ID when exposed by the detail page.
- `supplier_business_type`, `supplier_business_type_ko`, `supplier_employee_count`, `supplier_employee_count_ko`: supplier profile attributes.
- `supplier_response_time`, `supplier_response_time_ko`, `supplier_on_time_delivery_rate`, `supplier_on_time_delivery_rate_ko`, `supplier_rating`, `supplier_rating_ko`, `supplier_total_review_order_count`, `supplier_total_review_order_count_ko`: public supplier performance fields.
- `supplier_verified`, `supplier_verified_ko`: whether the detail page exposes pass-assessment/verified signal.
- `source_url`: Alibaba.com source product URL.

## Notes

- Prices, MOQ, and product availability can change on Alibaba.com.
- Certificate values reflect public listing badges or explicit title text. `Listing not specified` means the list page did not expose a concrete certificate.
- KRW prices were converted in the source workbook or supplemental category script before this repository export.
- Supplier fields are collected from public Alibaba.com product detail pages and may change over time.
- Korean supplier fields are display translations/transliterations for Korean-facing review; original Alibaba supplier fields are preserved.
