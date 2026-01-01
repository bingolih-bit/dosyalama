# 🚀 Hızlı Başlangıç Rehberi

## ⚡ 5 Dakikada Kurulum ve Kullanım

### 1️⃣ Tesseract Kurulumu (Bir Kez)

```bash
# macOS
brew install tesseract tesseract-lang poppler

# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-tur poppler-utils
```

### 2️⃣ Python Paketlerini Kurma

```bash
cd ~/GitHub/dava-yonetim-sistemi
pip install watchdog
```

### 3️⃣ Sistemi Kurma

```bash
python bin/dava-kur
```

Çıktı:
```
🚀 Dava Yönetim Sistemi Kurulumu
==================================================

✅ Konfigürasyon klasörü: /Users/kullanici/.dava-yonetim
✅ Alt klasörler oluşturuldu
✅ Veritabanı oluşturuldu
✅ Konfigürasyon dosyası oluşturuldu

✅ Kurulum tamamlandı!
```

### 4️⃣ Dava Klasörü Ekleme

```bash
# Örnek: Hukuk davaları klasörü
python bin/dava-config add ~/Belgelerim/HUKUK_DAVALARI

# Örnek: Ceza davaları klasörü
python bin/dava-config add ~/Belgelerim/CEZA_DAVALARI
```

### 5️⃣ Mevcut PDF'leri İşleme (İsteğe Bağlı)

```bash
# Klasördeki mevcut PDF'leri işle
python bin/dava-analiz ~/Belgelerim/HUKUK_DAVALARI
```

Çıktı:
```
📁 15 PDF dosyası bulundu
🔄 İşleniyor...

📄 İşleniyor: tebligat_001.pdf
  🔍 OCR yapılıyor...
  🔬 Analiz ediliyor...
  📋 Tip: tebligat
  📅 Tarih: 2024-05-15
  ✏️  Yeniden adlandırılıyor...
  ✅ Yeni ad: 2024-05-15_Tebligat.pdf
  📊 Özet dosyaları güncelleniyor...
  ✅ İşlem tamamlandı!

...

✅ 15/15 dosya başarıyla işlendi
```

### 6️⃣ Sistemi Başlatma (İzleme Modu)

```bash
python bin/dava-baslat
```

Çıktı:
```
✅ İzleniyor: /Users/kullanici/Belgelerim/HUKUK_DAVALARI
✅ İzleniyor: /Users/kullanici/Belgelerim/CEZA_DAVALARI

🚀 Dava Yönetim Sistemi çalışıyor...
📁 PDF dosyaları otomatik olarak işlenecek.
⏸  Durdurmak için Ctrl+C yapın.
```

Artık bu klasörlere yeni PDF eklediğinizde otomatik olarak:
- OCR yapılır
- Analiz edilir
- Yeniden adlandırılır
- Veritabanına kaydedilir
- Özet dosyaları güncellenir
- Süreler takibe alınır

---

## 📋 Günlük Kullanım

### Durum Kontrolü

```bash
python bin/dava-durum
```

### Yaklaşan Süreleri Görme

```bash
# Bu haftaki süreler
python bin/dava-yonetim sureler --days 7

# Bu ayki süreler
python bin/dava-yonetim sureler --days 30
```

### Klasör Listesi

```bash
python bin/dava-config list
```

---

## 📁 Klasör Yapısı (Otomatik Oluşturulur)

```
HUKUK_DAVALARI/
├── Dava_001/
│   ├── 2024-05-15_Tebligat.pdf
│   ├── 2024-06-20_Durusma.pdf
│   ├── 2024-07-10_Bilirkisi.pdf
│   ├── _DOSYA_OZET.md          ← Otomatik oluşturulur
│   └── _YAPILACAKLAR.md        ← Otomatik oluşturulur
├── Dava_002/
│   ├── 2024-03-12_Karar.pdf
│   ├── _DOSYA_OZET.md
│   └── _YAPILACAKLAR.md
...
```

---

## 🔥 İpuçları

### 1. PATH'e Ekleme (Opsiyonel ama Önerilen)

`.bashrc` veya `.zshrc` dosyanıza ekleyin:

```bash
export PATH="$HOME/GitHub/dava-yonetim-sistemi/bin:$PATH"
```

Ardından:

```bash
source ~/.bashrc  # veya source ~/.zshrc
```

Artık `dava-` komutlarını doğrudan kullanabilirsiniz:

```bash
dava-kur
dava-config add ~/Belgelerim/HUKUK
dava-baslat
dava-durum
```

### 2. Arka Planda Çalıştırma (Daemon)

```bash
# Arka planda başlat
nohup python bin/dava-baslat > /dev/null 2>&1 &

# Process ID'yi kaydet
echo $! > ~/.dava-yonetim/dava.pid

# Durdurmak için
kill $(cat ~/.dava-yonetim/dava.pid)
```

### 3. Sistem Başlangıcında Otomatik Başlatma (macOS)

LaunchAgent oluştur: `~/Library/LaunchAgents/com.dava-yonetim.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dava-yonetim</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/KULLANICI/GitHub/dava-yonetim-sistemi/bin/dava-baslat</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Yükle:

```bash
launchctl load ~/Library/LaunchAgents/com.dava-yonetim.plist
```

### 4. Log Dosyalarını İnceleme

```bash
# Bugünün log dosyası
tail -f ~/.dava-yonetim/logs/dava_yonetim_$(date +%Y%m%d).log

# Son 100 satır
tail -100 ~/.dava-yonetim/logs/dava_yonetim_$(date +%Y%m%d).log
```

### 5. Veritabanını İnceleme

```bash
sqlite3 ~/.dava-yonetim/dava.db

# SQL sorguları
SELECT * FROM davalar;
SELECT * FROM dosyalar;
SELECT * FROM sureler WHERE tamamlandi = 0;
```

---

## ❓ Sık Sorulan Sorular

### OCR çalışmıyor?

```bash
# Tesseract kurulu mu?
tesseract --version

# Türkçe dil paketi kurulu mu?
tesseract --list-langs | grep tur
```

### Bildirimler gelmiyor?

macOS için Sistem Tercihleri > Bildirimler'den Terminal/iTerm'e izin verin.

### Dosya yeniden adlandırılmıyor?

1. PDF'in gerçek metin içerip içermediğini kontrol edin
2. OCR kalitesi için yüksek çözünürlüklü tarama yapın
3. Log dosyalarını inceleyin

---

## 🎯 Sonuç

Artık sisteminiz hazır! Yeni PDF'ler eklendiğinde otomatik olarak işlenecek ve düzenlenecektir.

**Keyifli kullanımlar!** 🎉
