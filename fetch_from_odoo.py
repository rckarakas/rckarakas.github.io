#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo Knowledge (Wiki) -> Talimat JSON Çekici
=============================================
BU SCRIPT ODOO SUNUCUSUNA ERİŞİMİ OLAN MAKİNEDE ÇALIŞTIRILMALI
(örn. Docker host'un kendisi, ya da aynı yerel ağdaki bir makine).
Claude'un sandbox'ı Odoo'nuza internet üzerinden ulaşamaz.

Ne yapar:
  1. Odoo'ya XML-RPC ile bağlanır (sadece Python standart kütüphanesi kullanılır, pip gerekmez)
  2. Belirtilen üst madde (parent article) altındaki tüm Knowledge makalelerini okur
  3. Her makaleyi data/TLM-XXX.json olarak yazar (generate.py bu dosyaları okuyup HTML üretir)

Kullanım:
    export ODOO_URL="http://localhost:8069"
    export ODOO_DB="atu_db"
    export ODOO_USER="admin"
    export ODOO_PASSWORD="********"
    export ODOO_PARENT_ARTICLE_ID="123"     # Talimatların bulunduğu üst maddenin ID'si
    python3 fetch_from_odoo.py

ODOO_PARENT_ARTICLE_ID nasıl bulunur:
    Odoo'da Knowledge > ilgili "Talimatlar" klasörüne/maddesine tıkla.
    Tarayıcı adres çubuğunda .../odoo/knowledge/article/123 gibi bir URL görürsün.
    Buradaki 123 sayısı ID'dir.

Makale başlıklarının "TLM-014 - Başlık" ya da "TLM-014 – Başlık" formatında
olması beklenir (kod otomatik ayıklanır). Farklı bir format kullanıyorsan
split_code_title() fonksiyonunu güncelle.
"""

import json
import os
import re
import sys
import xmlrpc.client

ODOO_URL = os.environ.get("ODOO_URL", "http://localhost:8069").rstrip("/")
ODOO_DB = os.environ.get("ODOO_DB", "")
ODOO_USER = os.environ.get("ODOO_USER", "")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD", "")
PARENT_ARTICLE_ID = os.environ.get("ODOO_PARENT_ARTICLE_ID", "").strip()

DEFAULT_HAZIRLAYAN = os.environ.get("TALIMAT_HAZIRLAYAN", "Rafet Cihan Karakaş")
DEFAULT_ONAYLAYAN = os.environ.get("TALIMAT_ONAYLAYAN", "Harun Aslan")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

TLM_CODE_RE = re.compile(r"^\s*(TLM-\d+)\s*[-–—:]?\s*(.*)$", re.IGNORECASE)


def die(msg):
    print(f"HATA: {msg}")
    sys.exit(1)


def connect():
    try:
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        version = common.version()
        print(f"Odoo sürümü: {version.get('server_version', '?')}")
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    except Exception as e:
        die(f"Odoo'ya bağlanılamadı ({ODOO_URL}). Adres/ağ erişimini kontrol et.\n  Detay: {e}")
    if not uid:
        die("Kimlik doğrulama başarısız. ODOO_DB / ODOO_USER / ODOO_PASSWORD değerlerini kontrol et.")
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return uid, models


def fetch_articles(uid, models):
    domain = []
    if PARENT_ARTICLE_ID:
        domain = [("parent_id", "=", int(PARENT_ARTICLE_ID))]
    else:
        print("Uyarı: ODOO_PARENT_ARTICLE_ID verilmedi, TÜM Knowledge makaleleri çekilecek.")

    try:
        ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            "knowledge.article", "search",
            [domain],
        )
    except xmlrpc.client.Fault as e:
        die(
            "knowledge.article modeline erişilemedi. Modül adı farklı olabilir "
            f"(örn. document.page, wiki.wiki). Detay: {e}"
        )

    if not ids:
        print("Bu üst madde altında hiç makale bulunamadı.")
        return []

    records = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        "knowledge.article", "read",
        [ids], {"fields": ["name", "body"]},
    )
    return records


def split_code_title(name):
    m = TLM_CODE_RE.match(name or "")
    if m and m.group(2):
        return m.group(1).upper(), m.group(2).strip()
    if m:
        return m.group(1).upper(), name.strip()
    return None, (name or "").strip()


def main():
    missing = [v for v in ("ODOO_DB", "ODOO_USER", "ODOO_PASSWORD") if not os.environ.get(v)]
    if missing:
        die(f"Şu ortam değişkenleri eksik: {', '.join(missing)}")

    os.makedirs(DATA_DIR, exist_ok=True)
    uid, models = connect()
    records = fetch_articles(uid, models)

    written, skipped = 0, []
    for rec in records:
        kod, baslik = split_code_title(rec["name"])
        if not kod:
            skipped.append(rec["name"])
            continue

        data = {
            "kod": kod,
            "revizyon": "000",
            "tarih": "",
            "baslik": baslik,
            "ham_icerik": rec.get("body") or "<p><em>(İçerik boş)</em></p>",
            "hazirlayan": DEFAULT_HAZIRLAYAN,
            "onaylayan": DEFAULT_ONAYLAYAN,
        }
        out_path = os.path.join(DATA_DIR, f"{kod}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {kod}.json yazıldı — {baslik}")
        written += 1

    print(f"\n{written} talimat data/ klasörüne yazıldı.")
    if skipped:
        print(f"{len(skipped)} makale atlandı (başlığında TLM-XXX kodu bulunamadı):")
        for s in skipped:
            print(f"  - {s}")
    print("\nSonraki adım:  python3 generate.py")


if __name__ == "__main__":
    main()
