# Productinfo

Structured Alibaba.com product information for Korea-market research.

## Files

- `data/products.json` — canonical structured data for agents and scripts.
- `data/products.csv` — flat table version for spreadsheets or lightweight parsing.
- `data/memory_cards.json` — memory card category rows generated from the supplemental Alibaba search.
- `images/` — downloaded product main images referenced by `image_file`.
- `exports/alibaba_products_with_images.xlsx` — Excel workbook with embedded product images.

## Product counts

| Category ID | 中文品类 | 한국어 | English | Count |
|---|---|---|---|---:|
| `power-bank` | 移动电源 | 보조배터리 | Power Banks | 30 |
| `womens-dresses` | 女士连衣裙 | 여성 원피스 | Women's Dresses | 30 |
| `cooling-mattresses` | 凉感床垫 | 쿨링 매트리스 | Cooling Mattresses | 30 |
| `desktop-organizers` | 桌面整理柜 | 데스크 정리함 | Desktop Organizers | 30 |
| `memory-cards` | 存储卡 | 메모리 카드 | Memory Cards | 30 |

Total products: **150**

## Schema

Each product row contains:

- `id`: stable product ID within this dataset.
- `category_id`, `category_zh`, `category_ko`, `category_en`: category labels.
- `category_index`: product number inside its category.
- `image_file`: relative path to the downloaded main image.
- `image_alt`: image alt text from the source HTML or generated Korean product label.
- `korean_product_name`: Korean product title.
- `english_product_name`: English source/comparable product title.
- `price_krw`: KRW price string.
- `moq`: minimum order quantity.
- `certificates`: list of visible certificate labels.
- `supplier_name`: Alibaba supplier/company name shown on the product detail page.
- `supplier_years`, `supplier_years_text`: Alibaba join/supplier tenure.
- `supplier_country`: supplier registered country/region code.
- `supplier_profile_url`, `supplier_home_url`: Alibaba supplier profile/home links.
- `supplier_company_id`: Alibaba company ID when exposed by the detail page.
- `supplier_business_type`, `supplier_employee_count`: supplier profile attributes when exposed.
- `supplier_response_time`, `supplier_on_time_delivery_rate`, `supplier_rating`, `supplier_total_review_order_count`: public supplier performance fields when exposed.
- `supplier_verified`: whether the detail page exposes pass-assessment/verified signal.
- `source_url`: Alibaba.com source product URL.

## Notes

- Prices, MOQ, and product availability can change on Alibaba.com.
- Certificate values reflect public listing badges or explicit title text. `Listing not specified` means the list page did not expose a concrete certificate.
- KRW prices were converted in the source workbook or supplemental category script before this repository export.
- Supplier fields are collected from public Alibaba.com product detail pages and may change over time.
