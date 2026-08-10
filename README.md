# ASUM YEMEK — EYS Talimat Sistemi

## Yapı

```
asum-eys/
├── assets/css/talimat.css      Ortak tasarım (renk, font, düzen)
├── assets/img/                 Logo dosyaları
├── data/*.json                 Talimat İÇERİKLERİ (elle yazılan ya da Odoo'dan çekilen)
├── generate.py                 data/*.json → talimatlar/*.html üretir
├── fetch_from_odoo.py          Odoo Knowledge'dan data/*.json üretir
└── talimatlar/                 SONUÇ: GitHub Pages'e yüklenecek statik HTML'ler
    ├── index.html              Arama kutulu talimat listesi (otomatik üretilir)
    └── TLM-XXX.html
```

## İki çalışma şekli

### A) Odoo Knowledge'dan otomatik çekme

Bu adım **Odoo sunucusuna erişimi olan bir makinede** çalıştırılmalı
(Docker host, ya da Odoo ile aynı yerel ağdaki bir bilgisayar).

```bash
export ODOO_URL="http://localhost:8069"
export ODOO_DB="atu_db"
export ODOO_USER="admin"
export ODOO_PASSWORD="********"
export ODOO_PARENT_ARTICLE_ID="123"   # Talimatların bulunduğu üst maddenin ID'si

python3 fetch_from_odoo.py
python3 generate.py
```

`ODOO_PARENT_ARTICLE_ID` bulma: Odoo'da Knowledge > ilgili "Talimatlar" klasörüne
tıkla, adres çubuğunda `.../odoo/knowledge/article/123` görünür — 123 buradaki ID'dir.

Knowledge makale başlıkları **"TLM-014 - Başlık"** formatında olmalı (kod otomatik ayıklanır).

### B) Elle / düz metin ile ekleme

`data/` klasörüne örnek `TLM-001.json` gibi bir dosya ekle (bkz. şema aşağıda),
sonra:

```bash
python3 generate.py
```

## data/*.json şeması

**Yapılandırılmış (elle yazılan talimatlar için — 4 sabit bölüm):**

```json
{
  "kod": "TLM-002",
  "revizyon": "000",
  "tarih": "10.08.2026",
  "baslik": "Talimat başlığı",
  "bolumler": [
    {"baslik": "Amaç", "tip": "paragraf", "icerik": ["metin..."]},
    {"baslik": "Sorumluluk", "tip": "sorumluluk", "icerik": ["KGG Sorumlusu", "..."]},
    {"baslik": "Uygulama", "tip": "karma", "paragraf": "giriş cümlesi", "maddeler": ["madde 1", "madde 2"]},
    {"baslik": "İlgili Dokümanlar", "tip": "belge-listesi", "icerik": [{"kod": "LST-018", "ad": "Bölüm Listesi"}]}
  ],
  "hazirlayan": "Rafet Cihan Karakaş",
  "onaylayan": "Harun Aslan"
}
```

**Serbest (Odoo Knowledge'dan otomatik gelen — tek HTML bloğu):**

```json
{
  "kod": "TLM-014",
  "revizyon": "000",
  "tarih": "",
  "baslik": "Talimat başlığı",
  "ham_icerik": "<h2>Amaç</h2><p>...</p><ul><li>...</li></ul>",
  "hazirlayan": "Rafet Cihan Karakaş",
  "onaylayan": "Harun Aslan"
}
```

## GitHub Pages'e yayınlama

`generate.py` çalıştırıldıktan sonra oluşan **tüm klasörü** (assets/, talimatlar/,
data/, generate.py, fetch_from_odoo.py) repoya push et. GitHub Pages sadece
`talimatlar/*.html` (statik dosyalar) sunar — Python hiçbir zaman sunucuda çalışmaz,
sadece senin bilgisayarında HTML üretmek için kullanılır.

İstersen bunu her `data/` değişikliğinde otomatik çalıştıracak bir GitHub Actions
workflow'u da ekleyebiliriz (Claude'a "GitHub Actions kur" diyerek istenebilir).
