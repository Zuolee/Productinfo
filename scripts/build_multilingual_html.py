#!/usr/bin/env python3
import json
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = REPO_DIR.parent
PRODUCTS_JSON = REPO_DIR / "data" / "products.json"
ROOT_HTML = ROOT_DIR / "power_bank_products_krw.html"
EXPORT_HTML = REPO_DIR / "exports" / "product_catalog_multilingual.html"

LANGUAGES = [
    ("ko", "한국어", "韩语"),
    ("en", "English", "英语"),
    ("es", "Español", "西班牙语"),
    ("pt", "Português", "葡萄牙语"),
    ("fr", "Français", "法语"),
    ("it", "Italiano", "意大利语"),
    ("id", "Bahasa Indonesia", "印尼语"),
    ("vi", "Tiếng Việt", "越南语"),
    ("th", "ไทย", "泰语"),
    ("ms", "Bahasa Melayu", "马来语"),
    ("tl", "Filipino", "菲律宾语"),
    ("km", "ភាសាខ្មែរ", "高棉语"),
    ("my", "မြန်မာ", "缅甸语"),
    ("lo", "ລາວ", "老挝语"),
    ("ar", "العربية", "阿拉伯语"),
]


def html_template(data: dict, image_prefix: str) -> str:
    products = data["products"]
    categories = data["metadata"]["categories"]
    minimal_products = []
    for product in products:
        minimal_products.append(
            {
                "id": product.get("id"),
                "category_id": product.get("category_id"),
                "category_index": product.get("category_index"),
                "image_file": f"{image_prefix}{product.get('image_file')}",
                "image_alt": product.get("image_alt"),
                "source_url": product.get("source_url"),
                "price_krw": product.get("price_krw"),
                "price_krw_min": product.get("price_krw_min"),
                "price_krw_max": product.get("price_krw_max"),
                "moq": product.get("moq"),
                "certificates": product.get("certificates", []),
                "supplier_name_ko": product.get("supplier_name_ko"),
                "supplier_name": product.get("supplier_name"),
                "supplier_years_ko": product.get("supplier_years_ko"),
                "supplier_years_text": product.get("supplier_years_text"),
                "localized": {
                    code: {
                        "category_name": product.get("localized", {}).get(code, {}).get("category_name")
                        or product.get(f"category_name_{code}")
                        or product.get("category_en"),
                        "product_name": product.get("localized", {}).get(code, {}).get("product_name")
                        or product.get(f"product_name_{code}")
                        or product.get("product_name_en"),
                    }
                    for code, _native, _zh in LANGUAGES
                },
            }
        )

    app_data = {
        "products": minimal_products,
        "categories": categories,
        "languages": [
            {"code": code, "native": native, "zh": zh}
            for code, native, zh in LANGUAGES
        ],
    }

    json_data = json.dumps(app_data, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Alibaba.com 多语言商品信息表（韩元）</title>
  <style>
    :root {{
      --orange: #ff6a00;
      --ink: #18212f;
      --muted: #667085;
      --line: #e7e9ee;
      --soft: #f7f8fa;
      --green: #087a55;
      --blue: #175cd3;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: var(--ink); background: #f3f4f6; font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif; }}
    .page {{ width: min(1500px, calc(100% - 32px)); margin: 28px auto; }}
    .hero {{ padding: 28px 30px; border-radius: 18px 18px 0 0; color: #fff; background: linear-gradient(135deg, #ff6a00, #ff8a34); }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .hero p {{ margin: 0; opacity: .94; }}
    .category-tabs {{ display: flex; flex-wrap: wrap; gap: 8px; max-height: 184px; overflow: auto; padding: 16px 22px 0; background: #fff; border-bottom: 1px solid var(--line); }}
    .category-tab {{ padding: 10px 14px; color: #475467; background: #f2f4f7; border: 1px solid transparent; border-radius: 10px 10px 0 0; cursor: pointer; font: inherit; font-weight: 700; }}
    .category-tab:hover {{ color: #b54708; background: #fff5ed; }}
    .category-tab[aria-selected="true"] {{ color: #d84f00; background: #fff; border-color: var(--line); border-bottom-color: #fff; box-shadow: inset 0 3px 0 var(--orange); }}
    .toolbar {{ display: grid; grid-template-columns: minmax(260px, 1fr) auto auto; gap: 14px; align-items: center; padding: 18px 22px; background: #fff; border-bottom: 1px solid var(--line); }}
    .search, .language-select {{ padding: 11px 14px; border: 1px solid #cfd4dc; border-radius: 10px; font: inherit; background: #fff; }}
    .count {{ color: var(--muted); white-space: nowrap; }}
    .language-note {{ grid-column: 1 / -1; color: var(--muted); font-size: 13px; }}
    .table-wrap {{ overflow-x: auto; background: #fff; }}
    table {{ width: 100%; min-width: 1180px; border-collapse: collapse; }}
    th {{ position: sticky; top: 0; z-index: 1; padding: 13px 14px; text-align: left; color: #344054; background: var(--soft); border-bottom: 1px solid var(--line); }}
    td {{ padding: 14px; vertical-align: middle; border-bottom: 1px solid var(--line); }}
    tbody tr:hover {{ background: #fffaf6; }}
    .no {{ width: 54px; text-align: center; color: var(--muted); }}
    .thumb {{ width: 104px; }}
    .thumb img {{ display: block; width: 88px; height: 88px; object-fit: contain; border: 1px solid var(--line); border-radius: 10px; background: #fff; }}
    .title {{ position: relative; min-width: 520px; padding-right: 90px; font-weight: 650; }}
    .title a {{ display: block; color: var(--ink); text-decoration: none; }}
    .title a:hover {{ color: var(--orange); text-decoration: underline; }}
    .name-line {{ display: block; margin: 4px 0; }}
    .name-ko {{ font-size: 15px; line-height: 1.45; }}
    .name-en {{ color: var(--muted); font-size: 13px; font-weight: 500; line-height: 1.4; }}
    .name-selected {{ margin-top: 8px; padding-top: 8px; color: var(--blue); border-top: 1px dashed var(--line); font-size: 13.5px; }}
    .lang-label {{ display: inline-block; min-width: 78px; color: #98a2b3; font-weight: 700; }}
    .copy-ko {{ position: absolute; top: 14px; right: 14px; padding: 5px 10px; color: #344054; background: #fff; border: 1px solid #cfd4dc; border-radius: 7px; cursor: pointer; font: inherit; font-size: 12px; font-weight: 600; line-height: 1.3; transition: .15s ease; }}
    .copy-ko:hover {{ color: #d84f00; border-color: #ff9b57; background: #fff8f3; }}
    .copy-ko.copied {{ color: #fff; border-color: var(--green); background: var(--green); }}
    .copy-ko.failed {{ color: #b42318; border-color: #fda29b; background: #fff1f0; }}
    .price {{ min-width: 150px; color: #d84f00; font-size: 16px; font-weight: 750; white-space: nowrap; }}
    .moq {{ min-width: 110px; white-space: nowrap; }}
    .certs {{ min-width: 150px; }}
    .cert {{ display: inline-block; margin: 2px 4px 2px 0; padding: 4px 9px; color: var(--green); background: #e9f8f2; border: 1px solid #bce8d7; border-radius: 999px; font-weight: 700; }}
    .supplier {{ min-width: 240px; color: #344054; }}
    .supplier small {{ display: block; color: var(--muted); }}
    .notes {{ padding: 18px 22px 24px; color: var(--muted); background: #fff; border-radius: 0 0 18px 18px; }}
    .notes p {{ margin: 5px 0; }}
    .hidden {{ display: none; }}
    @media (max-width: 820px) {{
      .page {{ width: 100%; margin: 0; }}
      .hero, .notes {{ border-radius: 0; }}
      .toolbar {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <h1>Alibaba.com 多语言商品信息采购表</h1>
      <p id="summary">共 {len(products)} 件 · {len(categories)} 个品类 · 韩元价格 · 韩/英 + 西葡法意、东南亚语言、阿语商品名</p>
    </header>
    <nav id="categoryTabs" class="category-tabs" role="tablist" aria-label="商品品类"></nav>
    <section class="toolbar" aria-label="表格工具">
      <input id="search" class="search" type="search" placeholder="搜索商品名、MOQ、证书、供应商…" aria-label="搜索商品">
      <select id="languageSelect" class="language-select" aria-label="选择额外展示语言"></select>
      <span id="count" class="count"></span>
      <div class="language-note">默认显示韩语和英语；右侧下拉可切换第 3 行展示语言。韩文旁的“복사”按钮只复制韩文商品标题。</div>
    </section>
    <section class="table-wrap">
      <table>
        <thead>
          <tr>
            <th class="no">#</th>
            <th>商品主图</th>
            <th>상품명 / Product Name / Selected Language</th>
            <th>价格（KRW）</th>
            <th>MOQ</th>
            <th>证书</th>
            <th>供应商</th>
          </tr>
        </thead>
        <tbody id="productRows"></tbody>
      </table>
    </section>
    <footer class="notes">
      <p><strong>数据源：</strong>当前页面由 <code>Productinfo/data/products.json</code> 生成，已同步到 GitHub。页面内嵌数据，直接用 file:// 打开也能看到完整多语言。</p>
      <p><strong>价格说明：</strong>所有价格字段均为 KRW，并已拆分为最低价/最高价；页面展示原始韩元价格区间。</p>
      <p><strong>证书说明：</strong>证书来自 Alibaba.com 列表公开徽章或标题明示信息；下单前仍需向供应商索取原件核验。</p>
    </footer>
  </main>
  <script type="application/json" id="appData">{json_data}</script>
  <script>
    const app = JSON.parse(document.querySelector('#appData').textContent);
    const products = app.products;
    const categories = app.categories;
    const languages = app.languages;
    const tabs = document.querySelector('#categoryTabs');
    const rows = document.querySelector('#productRows');
    const search = document.querySelector('#search');
    const count = document.querySelector('#count');
    const languageSelect = document.querySelector('#languageSelect');
    let activeCategory = categories[0]?.category_id || '';

    function escapeHtml(value) {{
      return String(value ?? '').replace(/[&<>"']/g, char => ({{
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      }}[char]));
    }}

    function languageLabel(code) {{
      const language = languages.find(item => item.code === code);
      return language ? `${{language.zh}} / ${{language.native}}` : code;
    }}

    function renderLanguageOptions() {{
      const options = languages
        .filter(language => !['ko', 'en'].includes(language.code))
        .map(language => `<option value="${{language.code}}">${{escapeHtml(language.zh)}} / ${{escapeHtml(language.native)}} (${{language.code}})</option>`)
        .join('');
      languageSelect.innerHTML = options;
      languageSelect.value = 'es';
    }}

    function renderTabs() {{
      tabs.innerHTML = categories.map((category, index) => `
        <button class="category-tab" type="button" role="tab" aria-selected="${{index === 0}}" data-category="${{escapeHtml(category.category_id)}}">
          ${{escapeHtml(category.category_ko)}} / ${{escapeHtml(category.category_en)}} <small>(${{category.count}})</small>
        </button>
      `).join('');
      tabs.querySelectorAll('.category-tab').forEach(button => {{
        button.addEventListener('click', () => {{
          activeCategory = button.dataset.category;
          tabs.querySelectorAll('.category-tab').forEach(item => item.setAttribute('aria-selected', String(item === button)));
          renderRows();
        }});
      }});
    }}

    async function copyText(text) {{
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        try {{
          await navigator.clipboard.writeText(text);
          return true;
        }} catch (error) {{}}
      }}
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      const copied = document.execCommand('copy');
      textarea.remove();
      return copied;
    }}

    function productMatches(product, query) {{
      if (!query) return true;
      const haystack = [
        product.id,
        product.price_krw,
        product.moq,
        product.certificates.join(' '),
        product.supplier_name_ko,
        product.supplier_name,
        ...languages.map(language => product.localized?.[language.code]?.product_name),
      ].join(' ').toLowerCase();
      return haystack.includes(query);
    }}

    function renderRows() {{
      const selectedLanguage = languageSelect.value || 'es';
      const query = search.value.trim().toLowerCase();
      const filtered = products.filter(product => product.category_id === activeCategory && productMatches(product, query));
      const categoryTotal = products.filter(product => product.category_id === activeCategory).length;
      rows.innerHTML = filtered.map(product => {{
        const koName = product.localized?.ko?.product_name || '';
        const enName = product.localized?.en?.product_name || '';
        const selectedName = product.localized?.[selectedLanguage]?.product_name || '';
        return `
          <tr>
            <td class="no">${{product.category_index}}</td>
            <td class="thumb"><img src="${{escapeHtml(product.image_file)}}" alt="${{escapeHtml(product.image_alt || koName)}}"></td>
            <td class="title">
              <a href="${{escapeHtml(product.source_url)}}" target="_blank" rel="noopener">
                <span class="name-line name-ko" lang="ko"><span class="lang-label">KO</span>${{escapeHtml(koName)}}</span>
                <span class="name-line name-en" lang="en"><span class="lang-label">EN</span>${{escapeHtml(enName)}}</span>
                <span class="name-line name-selected" lang="${{escapeHtml(selectedLanguage)}}"><span class="lang-label">${{escapeHtml(selectedLanguage.toUpperCase())}}</span>${{escapeHtml(selectedName)}}</span>
              </a>
              <button type="button" class="copy-ko" data-copy-text="${{escapeHtml(koName)}}" aria-label="한국어 상품명 복사">복사</button>
            </td>
            <td class="price">${{escapeHtml(product.price_krw || '')}}</td>
            <td class="moq">${{escapeHtml(product.moq || '')}}</td>
            <td class="certs">${{(product.certificates || []).map(cert => `<span class="cert">${{escapeHtml(cert)}}</span>`).join('')}}</td>
            <td class="supplier">${{escapeHtml(product.supplier_name_ko || '')}}<small>${{escapeHtml(product.supplier_name || '')}}</small><small>${{escapeHtml(product.supplier_years_ko || product.supplier_years_text || '')}}</small></td>
          </tr>
        `;
      }}).join('');
      count.textContent = `显示 ${{filtered.length}} / ${{categoryTotal}} 条 · 当前第 3 行语言：${{languageLabel(selectedLanguage)}}`;
      rows.querySelectorAll('.copy-ko').forEach(button => {{
        button.addEventListener('click', async event => {{
          event.preventDefault();
          event.stopPropagation();
          const copied = await copyText(button.dataset.copyText);
          button.textContent = copied ? '복사됨' : '복사 실패';
          button.classList.toggle('copied', copied);
          button.classList.toggle('failed', !copied);
          window.setTimeout(() => {{
            button.textContent = '복사';
            button.classList.remove('copied', 'failed');
          }}, 1400);
        }});
      }});
    }}

    renderLanguageOptions();
    renderTabs();
    search.addEventListener('input', renderRows);
    languageSelect.addEventListener('change', renderRows);
    renderRows();
  </script>
</body>
</html>
"""


def main() -> None:
    data = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    ROOT_HTML.write_text(html_template(data, "Productinfo/"), encoding="utf-8")
    EXPORT_HTML.write_text(html_template(data, "../"), encoding="utf-8")
    print(f"Wrote {ROOT_HTML}")
    print(f"Wrote {EXPORT_HTML}")


if __name__ == "__main__":
    main()
