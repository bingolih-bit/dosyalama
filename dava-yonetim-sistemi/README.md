# 🏛️ Dava Dosya Yönetim Sistemi

Akıllı PDF dava dosyası yönetimi, OCR ve otomatik isimlendirme sistemi.

## ✨ Özellikler

### 📁 Klasör İzleme
- Belirlediğiniz klasörleri sürekli izler (HUKUK, CEZA, İCRA, İDARE)
- Yeni PDF eklendiğinde otomatik olarak işler
- Watchdog ile gerçek zamanlı dosya takibi

### 🔍 OCR ve Akıllı İsimlendirme
- Tesseract OCR ile PDF → metin çevirisi
- Regex pattern matching ile dosya tipini otomatik tespit:
  - DURUŞMA içeriyorsa → duruşma tutanağı
  - BİLİRKİŞİ içeriyorsa → bilirkişi raporu
  - TEBLİGAT içeriyorsa → tebligat
  - KARAR içeriyorsa → mahkeme kararı
- Tarihleri otomatik yakalar (dd.mm.yyyy formatı)
- Dosyayı `YYYY-MM-DD_Dosya_Tipi.pdf` formatında yeniden adlandırır
- Orijinal dosyayı yedekleme klasöründe saklar

### 📊 Dosya Özeti
- Her dava klasöründe `_DOSYA_OZET.md` oluşturur ve günceller
- İçerik:
  - Dosya listesi (tip bazlı kategorize)
  - Kronolojik sıralama
  - Tespit edilen tarihler
  - Son güncelleme zamanı

### ⏰ Süre Takibi
- "Sonraki duruşma", "celse", "rapor süresi" gibi ifadeleri tespit eder
- Tarihleri `_YAPILACAKLAR.md` dosyasına kaydeder
- macOS notification ile hatırlatma (opsiyonel)
- SQLite veritabanında süre kayıtları

### 💾 Veri Saklama
- SQLite veritabanı kullanır
- Tablolar: davalar, dosyalar, sureler, loglar
- Tüm işlemler loglanır

## 🚀 Kurulum

### Gereksinimler

- Python 3.9+
- Tesseract OCR
- macOS (Linux/Windows için uyarlama gerekebilir)

### 1. Tesseract Kurulumu

```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-tur

# Poppler utils (PDF → görsel dönüşümü için)
brew install poppler  # macOS
sudo apt-get install poppler-utils  # Ubuntu/Debian
```

### 2. Python Paketlerini Kurma

```bash
cd ~/GitHub/dava-yonetim-sistemi
pip install -r requirements.txt
```

VEYA

```bash
pip install -e .
```

### 3. Script'lere Çalıştırma İzni Verme

```bash
chmod +x bin/*
```

### 4. Script'leri PATH'e Ekleme (Opsiyonel)

`.bashrc` veya `.zshrc` dosyanıza ekleyin:

```bash
export PATH="$HOME/GitHub/dava-yonetim-sistemi/bin:$PATH"
```

Ardından:

```bash
source ~/.bashrc  # veya source ~/.zshrc
```

## 📖 Kullanım

### İlk Kurulum

```bash
dava-kur
# veya
python bin/dava-kur
```

Bu komut:
- `~/.dava-yonetim` klasörünü oluşturur
- Veritabanını hazırlar
- Konfigürasyon dosyasını oluşturur

### Klasör Ekleme

```bash
dava-config add ~/Belgelerim/HUKUK_DAVALARI
dava-config add ~/Belgelerim/CEZA_DAVALARI
```

### Klasörleri Listeleme

```bash
dava-config list
```

### Klasör Kaldırma

```bash
dava-config remove ~/Belgelerim/HUKUK_DAVALARI
```

### Sistemi Başlatma (İzleme Modu)

```bash
dava-baslat
```

Bu komut:
- Tüm eklenen klasörleri izlemeye başlar
- Yeni PDF eklendiğinde otomatik işler
- Ctrl+C ile durdurulur

### Mevcut PDF'leri İşleme

```bash
dava-analiz ~/Belgelerim/HUKUK_DAVALARI
```

Bu komut:
- Klasördeki tüm PDF'leri bulur
- OCR uygular
- Analiz eder ve yeniden adlandırır
- Özet dosyalarını oluşturur

### Durum Raporu

```bash
dava-durum
```

Çıktı:
```
📊 Dava Yönetim Sistemi - Durum Raporu
==================================================

📂 Toplam Dava Sayısı: 5
📄 Toplam Dosya Sayısı: 23
⏰ Aktif Süre Sayısı: 8

📋 Dosya Tipi Dağılımı:
  • Durusma: 12
  • Bilirkisi: 5
  • Tebligat: 4
  • Karar: 2

📅 Süre Özeti:
  • Bugün: 0
  • Bu hafta: 3
  • Bu ay: 8

📁 İzlenen Klasör Sayısı: 2
```

### Yaklaşan Süreleri Görüntüleme

```bash
# Varsayılan: 30 gün içindeki süreler
dava-yonetim sureler

# 7 gün içindeki süreler
dava-yonetim sureler --days 7

# 90 gün içindeki süreler
dava-yonetim sureler --days 90
```

## 📂 Proje Yapısı

```
dava-yonetim-sistemi/
├── dava_yonetim/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLite veritabanı yönetimi
│   │   ├── watcher.py            # Klasör izleme (watchdog)
│   │   ├── ocr_engine.py         # OCR motoru (Tesseract)
│   │   ├── file_analyzer.py      # Dosya analiz motoru
│   │   ├── file_renamer.py       # Dosya yeniden adlandırma
│   │   ├── summary_generator.py  # Özet dosyası oluşturma
│   │   ├── deadline_tracker.py   # Süre takip sistemi
│   │   └── logger.py             # Loglama
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py           # CLI komutları
│   └── config/
│       ├── __init__.py
│       └── settings.py           # Konfigürasyon
├── bin/
│   ├── dava-yonetim              # Ana CLI
│   ├── dava-kur                  # Kurulum
│   ├── dava-config               # Konfigürasyon
│   ├── dava-baslat               # Başlat
│   ├── dava-durum                # Durum
│   └── dava-analiz               # Analiz
├── requirements.txt
├── setup.py
└── README.md
```

## 🔧 Konfigürasyon

Konfigürasyon dosyası: `~/.dava-yonetim/config.json`

```json
{
  "watched_folders": [
    "/Users/kullanici/Belgelerim/HUKUK_DAVALARI"
  ],
  "database_path": "/Users/kullanici/.dava-yonetim/dava.db",
  "backup_folder": "/Users/kullanici/.dava-yonetim/backup",
  "log_folder": "/Users/kullanici/.dava-yonetim/logs",
  "tesseract_lang": "tur",
  "notification_enabled": true,
  "file_patterns": {
    "durusma": ["DURUŞMA", "CELSE", "TUTANAK"],
    "bilirkisi": ["BİLİRKİŞİ", "RAPOR", "EKSPERTIZ"],
    "tebligat": ["TEBLİGAT", "İHBARNAME", "İHTAR"],
    "karar": ["KARAR", "HÜKÜM", "İLAM"]
  }
}
```

## 📝 Örnekler

### Örnek 1: Yeni PDF Ekleme

1. `~/Belgelerim/HUKUK_DAVALARI/Dava_123/` klasörüne `tebligat_yeni.pdf` ekliyorsunuz
2. Sistem otomatik tespit eder
3. OCR uygular ve "TEBLİGAT" kelimesini bulur
4. Tarih tespit eder: `15.05.2024`
5. Dosyayı yeniden adlandırır: `2024-05-15_Tebligat.pdf`
6. Yedek oluşturur: `~/.dava-yonetim/backup/2024-05-15/tebligat_yeni.pdf`
7. Veritabanına kaydeder
8. `_DOSYA_OZET.md` dosyasını günceller

### Örnek 2: Duruşma Tutanağı

PDF içeriği:
```
DURUŞMA TUTANAĞI

Tarih: 20.06.2024
Sonraki duruşma: 15.09.2024

...
```

Sistem:
- Dosya tipi: `durusma`
- Belge tarihi: `2024-06-20`
- Yeni ad: `2024-06-20_Durusma.pdf`
- Süre ekler: `15.09.2024` - Duruşma
- `_YAPILACAKLAR.md` dosyasını günceller

## 🐛 Sorun Giderme

### Tesseract bulunamıyor

```bash
# Tesseract kurulu mu kontrol et
tesseract --version

# Kurulu değilse:
brew install tesseract tesseract-lang
```

### PDF işlenmiyor

1. PDF dosyasının gerçek metin içerip içermediğini kontrol edin
2. OCR kalitesi düşükse, daha yüksek çözünürlüklü tarama yapın
3. Log dosyalarını kontrol edin: `~/.dava-yonetim/logs/`

### Bildirimler çalışmıyor

macOS için `osascript` erişimi gereklidir. Sistem Tercihleri > Güvenlik ve Gizlilik > Gizlilik > Otomasyon bölümünden Terminal/iTerm'e izin verin.

## 📄 Lisans

MIT License

## 🤝 Katkıda Bulunma

Pull request'ler kabul edilir. Büyük değişiklikler için önce issue açarak tartışalım.

## 📧 İletişim

Sorularınız için issue açabilirsiniz.

---

**Not:** Bu sistem hassas hukuki belgelerle çalışır. Kullanmadan önce test ortamında denemenizi öneririz.
