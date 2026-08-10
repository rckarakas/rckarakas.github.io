#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASUM YEMEK EYS Talimat Üretici
data/TLM-XXX.json dosyalarını okuyup talimatlar/TLM-XXX.html üretir.
Ayrıca talimatlar/index.html (arama/filtreli liste sayfası) üretir.

Kullanım:
    python3 generate.py
"""

import json
import os
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUT_DIR = os.path.join(BASE_DIR, "talimatlar")

PAGE_TEMPLATE = '''<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{kod} — {baslik}</title>
  <link rel="stylesheet" href="../assets/css/talimat.css">
</head>
<body>
<div class="page">
  <div class="header-top">
    <img src="../assets/img/logo-light.svg" class="logo-svg" alt="ASUM YEMEK">
    <div class="header-right">
      <div class="header-badge">ENTEGRE YÖNETİM SİSTEMİ</div>
      <a href="../talimatlar.html" class="header-back-link">&larr; Tüm Talimatlar</a>
    </div>
  </div>
  <div class="doc-meta">
    <div class="meta-item"><label>Doküman No</label><span>{kod}</span></div>
    <div class="meta-item"><label>Revizyon No</label><span>{revizyon}</span></div>
    <div class="meta-item"><label>Yayın Tarihi</label><span>{tarih}</span></div>
  </div>
  <div class="doc-title-bar">
    <div class="doc-code">TALİMAT</div>
    <div class="doc-title">{baslik}</div>
  </div>
  <div class="content">
{sections}
  </div>
  <div class="footer">
    <div class="footer-left">
      <div>ASUM YEMEK A.Ş. — Nurdağı, Gaziantep</div>
      <div style="margin-top:4px;">Hazırlayan: {hazirlayan} &nbsp;·&nbsp; Onaylayan: {onaylayan}</div>
    </div>
    <div class="footer-right">{kod} · <span class="footer-page">Rev. {revizyon}</span></div>
  </div>
</div>
</body>
</html>
'''


def render_section(no, bolum):
    baslik = bolum["baslik"]
    tip = bolum["tip"]
    head = (
        '    <div class="section">\n'
        '      <div class="section-head">\n'
        f'        <div class="section-num">{no}</div>\n'
        f'        <div class="section-title">{baslik}</div>\n'
        '      </div>\n'
    )
    body = ""

    if tip == "paragraf":
        body += '      <div class="section-body">\n'
        for p in bolum["icerik"]:
            body += f'        <p>{p}</p>\n'
        body += '      </div>\n'

    elif tip == "sorumluluk":
        for item in bolum["icerik"]:
            body += f'      <div class="resp-row"><span class="resp-label">—</span><span>{item}</span></div>\n'

    elif tip == "madde-listesi":
        body += '      <ul class="bullet-list">\n'
        for item in bolum["icerik"]:
            body += f'        <li><div class="bullet-dot"></div><div>{item}</div></li>\n'
        body += '      </ul>\n'

    elif tip == "karma":
        if bolum.get("paragraf"):
            body += f'      <div class="section-body"><p>{bolum["paragraf"]}</p></div>\n'
        if bolum.get("maddeler"):
            body += '      <ul class="bullet-list">\n'
            for item in bolum["maddeler"]:
                body += f'        <li><div class="bullet-dot"></div><div>{item}</div></li>\n'
            body += '      </ul>\n'

    elif tip == "belge-listesi":
        body += '      <ul class="doc-link-list">\n'
        for item in bolum["icerik"]:
            body += f'        <li><span class="doc-tag">{item["kod"]}</span><span>{item["ad"]}</span></li>\n'
        body += '      </ul>\n'

    elif tip == "ham":
        body += f'      <div class="section-body-raw">{bolum["icerik_html"]}</div>\n'

    else:
        raise ValueError(f"Bilinmeyen bölüm tipi: {tip}")

    return head + body + '    </div>\n'


def build_page(data):
    if data.get("bolumler"):
        sections_html = "\n".join(
            render_section(i + 1, bolum) for i, bolum in enumerate(data["bolumler"])
        )
    elif data.get("ham_icerik"):
        # Odoo Knowledge'dan gelen serbest biçimli HTML içerik
        sections_html = f'    <div class="section-body-raw">\n{data["ham_icerik"]}\n    </div>\n'
    else:
        sections_html = ""

    return PAGE_TEMPLATE.format(
        kod=data["kod"],
        revizyon=data.get("revizyon", "000"),
        tarih=data.get("tarih") or "—",
        baslik=data["baslik"],
        sections=sections_html,
        hazirlayan=data.get("hazirlayan", ""),
        onaylayan=data.get("onaylayan", ""),
    )


INDEX_TEMPLATE = '''<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Talimatlar — ASUM YEMEK A.Ş. EYS</title>
  <link rel="stylesheet" href="assets/css/talimat.css">
  <style>
    .index-wrap {{ max-width: 860px; margin: 32px auto; }}
    .index-search {{
      width: 100%; padding: 12px 16px; margin-bottom: 16px;
      border: 1px solid var(--border); border-radius: 6px; font-size: 14px;
      font-family: "Open Sans", sans-serif;
    }}
    .index-list {{ list-style: none; margin: 0; padding: 0; background: #fff; border-radius: 6px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,.08); }}
    .index-list li a {{
      display: flex; align-items: center; gap: 16px; padding: 14px 20px;
      text-decoration: none; color: var(--dark); border-bottom: 1px solid var(--border);
    }}
    .index-list li:last-child a {{ border-bottom: none; }}
    .index-list li a:hover {{ background: var(--light); }}
    .index-code {{
      flex-shrink: 0; font-family: "Poppins", sans-serif; font-weight: 700; font-size: 12px;
      background: var(--primary); color: #fff; padding: 5px 10px; border-radius: 4px; min-width: 70px; text-align: center;
    }}
    .index-title {{ font-size: 14.5px; }}
  </style>
</head>
<body>
  <div class="index-wrap">
    <div class="header-top" style="border-radius:6px 6px 0 0;">
      <img src="assets/img/logo-light.svg" class="logo-svg" alt="ASUM YEMEK">
      <div class="header-badge">TALİMATLAR</div>
    </div>
    <div style="padding: 16px 0;">
      <input class="index-search" type="text" placeholder="Talimat kodu veya başlıkta ara..." oninput="filterList(this.value)">
    </div>
    <ul class="index-list" id="list">
{items}
    </ul>
  </div>
  <script>
    function filterList(q) {{
      q = q.toLocaleLowerCase('tr');
      document.querySelectorAll('#list li').forEach(function(li) {{
        var text = li.getAttribute('data-search');
        li.style.display = text.includes(q) ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>
'''


def build_index(entries):
    items = "\n".join(
        f'      <li data-search="{(e["kod"] + " " + e["baslik"]).lower()}">'
        f'<a href="talimatlar/{e["kod"]}.html"><span class="index-code">{e["kod"]}</span>'
        f'<span class="index-title">{e["baslik"]}</span></a></li>'
        for e in sorted(entries, key=lambda x: x["kod"])
    )
    return INDEX_TEMPLATE.format(items=items)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    json_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")))
    if not json_files:
        print(f"Uyarı: {DATA_DIR} içinde .json dosyası bulunamadı.")
        return

    entries = []
    for jf in json_files:
        with open(jf, encoding="utf-8") as f:
            data = json.load(f)
        html = build_page(data)
        out_path = os.path.join(OUT_DIR, f'{data["kod"]}.html')
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        entries.append({"kod": data["kod"], "baslik": data["baslik"]})
        print(f'  ✓ {data["kod"]}.html oluşturuldu')

    index_html = build_index(entries)
    index_path = os.path.join(BASE_DIR, "talimatlar.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"\n{len(entries)} talimat üretildi. talimatlar.html güncellendi.")


if __name__ == "__main__":
    main()
