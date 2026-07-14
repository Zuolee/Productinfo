# Productinfo

Structured Alibaba.com product information for Korea-market research.

## Files

- `data/products.json` — canonical structured data for agents and scripts.
- `data/products.csv` — flat table version with the same unified fields.
- `data/<category>.json` — one category subset per category, using the same `metadata` + `products` shape as `products.json`.
- `data/suppliers.json` — supplier cache keyed by Alibaba product detail URL.
- `images/` — downloaded product main images converted to PNG and grouped by category.
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
| `smart-watches` | 智能手表 | 스마트워치 | Smart Watches | 30 |
| `bluetooth-speakers` | 蓝牙音箱 | 블루투스 스피커 | Bluetooth Speakers | 30 |
| `air-purifiers` | 空气净化器 | 공기청정기 | Air Purifiers | 30 |
| `electric-toothbrushes` | 电动牙刷 | 전동 칫솔 | Electric Toothbrushes | 30 |
| `yoga-mats` | 瑜伽垫 | 요가 매트 | Yoga Mats | 30 |
| `pet-grooming-tools` | 宠物美容工具 | 반려동물 미용 도구 | Pet Grooming Tools | 30 |
| `coffee-machines` | 咖啡机 | 커피머신 | Coffee Machines | 30 |
| `solar-panels` | 太阳能板 | 태양광 패널 | Solar Panels | 30 |
| `led-strip-lights` | LED灯带 | LED 스트립 조명 | LED Strip Lights | 30 |
| `kitchen-knives` | 厨房刀具 | 주방 칼 | Kitchen Knives | 30 |
| `backpacks` | 背包 | 백팩 | Backpacks | 30 |
| `car-phone-holders` | 车载手机支架 | 차량용 휴대폰 거치대 | Car Phone Holders | 30 |
| `baby-strollers` | 婴儿车 | 유모차 | Baby Strollers | 30 |
| `office-chairs` | 办公椅 | 사무용 의자 | Office Chairs | 30 |
| `stainless-water-bottles` | 不锈钢水杯 | 스테인리스 물병 | Stainless Steel Water Bottles | 30 |
| `wireless-earbuds` | 无线耳机 | 무선 이어버드 | Wireless Earbuds | 30 |
| `makeup-brushes` | 化妆刷 | 메이크업 브러시 | Makeup Brushes | 30 |
| `garden-tools` | 园艺工具 | 원예 도구 | Garden Tools | 30 |
| `electric-bicycles` | 电动自行车 | 전기 자전거 | Electric Bicycles | 30 |
| `plastic-food-containers` | 食品保鲜盒 | 식품 보관용기 | Plastic Food Containers | 30 |

Total products: **870**

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
      "languages": ["ko", "en", "es", "pt", "fr", "it", "id", "vi", "th", "ms", "tl", "km", "my", "lo", "ar"]
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
- `localized`: separated display values by language. Current language codes are Korean (`ko`), English/source (`en`), Spanish (`es`), Portuguese (`pt`), French (`fr`), Italian (`it`), Indonesian (`id`), Vietnamese (`vi`), Thai (`th`), Malay (`ms`), Filipino (`tl`), Khmer (`km`), Burmese (`my`), Lao (`lo`), and Arabic (`ar`).
- `category_name_<lang>`, `product_name_<lang>`: flat multilingual category and product-title fields for spreadsheet/CSV use.
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
