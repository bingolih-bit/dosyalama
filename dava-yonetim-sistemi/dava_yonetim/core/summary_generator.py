"""
Dava Yönetim Sistemi - Özet Oluşturma Modülü
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from .database import Database
from .logger import Logger


class SummaryGenerator:
    """Dava klasörleri için özet dosyaları oluşturur"""

    def __init__(self, database: Database = None, logger: Logger = None):
        """
        SummaryGenerator sınıfı başlatıcı

        Args:
            database: Database instance
            logger: Logger instance
        """
        self.db = database or Database()
        self.logger = logger or Logger()

    def generate_summary(self, dava_klasor_yolu: str) -> bool:
        """
        Dava klasörü için özet dosyası oluştur

        Args:
            dava_klasor_yolu: Dava klasör yolu

        Returns:
            Başarılı ise True
        """
        klasor_path = Path(dava_klasor_yolu)

        if not klasor_path.exists() or not klasor_path.is_dir():
            self.logger.error(f"Klasör bulunamadı: {dava_klasor_yolu}")
            return False

        # Veritabanından dava bilgisini al
        dava = self.db.get_dava_by_path(str(klasor_path))

        if not dava:
            self.logger.warning(f"Dava kaydı bulunamadı: {dava_klasor_yolu}")
            return False

        # Dosyaları al
        dosyalar = self.db.get_dosyalar_by_dava(dava['id'])

        # Süreleri al
        sureler = self.db.get_sureler_by_dava(dava['id'], sadece_aktif=True)

        # Özet içeriğini oluştur
        content = self._build_summary_content(dava, dosyalar, sureler)

        # Özet dosyasını yaz
        summary_file = klasor_path / '_DOSYA_OZET.md'

        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Özet dosyası oluşturuldu: {summary_file}")
            return True

        except Exception as e:
            self.logger.error(f"Özet dosyası oluşturma hatası: {str(e)}")
            return False

    def generate_todo_file(self, dava_klasor_yolu: str) -> bool:
        """
        Dava klasörü için yapılacaklar dosyası oluştur

        Args:
            dava_klasor_yolu: Dava klasör yolu

        Returns:
            Başarılı ise True
        """
        klasor_path = Path(dava_klasor_yolu)

        if not klasor_path.exists() or not klasor_path.is_dir():
            self.logger.error(f"Klasör bulunamadı: {dava_klasor_yolu}")
            return False

        # Veritabanından dava bilgisini al
        dava = self.db.get_dava_by_path(str(klasor_path))

        if not dava:
            return False

        # Aktif süreleri al
        sureler = self.db.get_sureler_by_dava(dava['id'], sadece_aktif=True)

        # Yapılacaklar içeriğini oluştur
        content = self._build_todo_content(dava, sureler)

        # Yapılacaklar dosyasını yaz
        todo_file = klasor_path / '_YAPILACAKLAR.md'

        try:
            with open(todo_file, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Yapılacaklar dosyası oluşturuldu: {todo_file}")
            return True

        except Exception as e:
            self.logger.error(f"Yapılacaklar dosyası oluşturma hatası: {str(e)}")
            return False

    def _build_summary_content(self, dava: Dict[str, Any],
                               dosyalar: List[Dict[str, Any]],
                               sureler: List[Dict[str, Any]]) -> str:
        """
        Özet dosyası içeriğini oluştur

        Args:
            dava: Dava bilgisi
            dosyalar: Dosya listesi
            sureler: Süre listesi

        Returns:
            Markdown formatında özet içeriği
        """
        lines = []

        # Başlık
        lines.append(f"# {dava['klasor_adi']}")
        lines.append("")
        lines.append(f"**Klasör Yolu:** `{dava['klasor_yolu']}`")
        lines.append(f"**Son Güncelleme:** {dava['guncelleme_tarihi']}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # İstatistikler
        lines.append("## 📊 İstatistikler")
        lines.append("")
        lines.append(f"- **Toplam Dosya Sayısı:** {len(dosyalar)}")
        lines.append(f"- **Aktif Süre Sayısı:** {len(sureler)}")
        lines.append("")

        # Dosya tipi dağılımı
        if dosyalar:
            tip_dagilim = {}
            for dosya in dosyalar:
                tip = dosya['dosya_tipi'] or 'Diğer'
                tip_dagilim[tip] = tip_dagilim.get(tip, 0) + 1

            lines.append("### Dosya Tipi Dağılımı")
            lines.append("")
            for tip, sayi in sorted(tip_dagilim.items()):
                lines.append(f"- **{tip.capitalize()}:** {sayi}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Dosyalar (Tip bazında)
        lines.append("## 📁 Dosyalar")
        lines.append("")

        if not dosyalar:
            lines.append("_Henüz dosya eklenmemiş._")
            lines.append("")
        else:
            # Dosyaları tipe göre grupla
            dosyalar_by_type = {}
            for dosya in dosyalar:
                tip = dosya['dosya_tipi'] or 'Diğer'
                if tip not in dosyalar_by_type:
                    dosyalar_by_type[tip] = []
                dosyalar_by_type[tip].append(dosya)

            # Her tip için dosyaları listele
            for tip in sorted(dosyalar_by_type.keys()):
                lines.append(f"### {tip.capitalize()}")
                lines.append("")

                for dosya in sorted(dosyalar_by_type[tip],
                                  key=lambda x: x['dosya_tarihi'] or '',
                                  reverse=True):
                    tarih = dosya['dosya_tarihi'] or 'Tarih yok'
                    lines.append(f"- **{dosya['dosya_adi']}** ({tarih})")

                lines.append("")

        lines.append("---")
        lines.append("")

        # Kronolojik sıralama
        lines.append("## 📅 Kronolojik Sıralama")
        lines.append("")

        dosyalar_with_dates = [d for d in dosyalar if d['dosya_tarihi']]

        if not dosyalar_with_dates:
            lines.append("_Tarihi belli olan dosya yok._")
            lines.append("")
        else:
            for dosya in sorted(dosyalar_with_dates,
                              key=lambda x: x['dosya_tarihi']):
                tip = dosya['dosya_tipi'] or 'Belge'
                lines.append(f"- **{dosya['dosya_tarihi']}** - {tip.capitalize()} - {dosya['dosya_adi']}")

            lines.append("")

        lines.append("---")
        lines.append("")

        # Yaklaşan süreler (ilk 5)
        if sureler:
            lines.append("## ⏰ Yaklaşan Süreler (İlk 5)")
            lines.append("")

            for sure in sureler[:5]:
                lines.append(f"- **{sure['sure_tarihi']}** - {sure['sure_tipi']}")
                if sure['aciklama']:
                    lines.append(f"  - _{sure['aciklama'][:100]}_")

            lines.append("")
            lines.append("_Tüm süreler için `_YAPILACAKLAR.md` dosyasına bakınız._")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"_Bu dosya otomatik olarak oluşturulmuştur - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")

        return '\n'.join(lines)

    def _build_todo_content(self, dava: Dict[str, Any],
                           sureler: List[Dict[str, Any]]) -> str:
        """
        Yapılacaklar dosyası içeriğini oluştur

        Args:
            dava: Dava bilgisi
            sureler: Süre listesi

        Returns:
            Markdown formatında yapılacaklar içeriği
        """
        lines = []

        # Başlık
        lines.append(f"# Yapılacaklar - {dava['klasor_adi']}")
        lines.append("")
        lines.append(f"**Son Güncelleme:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Süreler
        if not sureler:
            lines.append("## ✅ Tüm süreler tamamlandı!")
            lines.append("")
            lines.append("_Şu anda bekleyen süre bulunmamaktadır._")
        else:
            lines.append(f"## ⏰ Aktif Süreler ({len(sureler)})")
            lines.append("")

            # Tarihe göre sırala
            sureler_sorted = sorted(sureler, key=lambda x: x['sure_tarihi'])

            for i, sure in enumerate(sureler_sorted, 1):
                # Tarihe kalan gün sayısını hesapla
                try:
                    sure_date = datetime.strptime(sure['sure_tarihi'], '%Y-%m-%d')
                    today = datetime.now()
                    days_left = (sure_date - today).days

                    if days_left < 0:
                        status = "🔴 GEÇMİŞ"
                    elif days_left == 0:
                        status = "🔴 BUGÜN"
                    elif days_left <= 7:
                        status = f"🟡 {days_left} GÜN KALDI"
                    elif days_left <= 30:
                        status = f"🟢 {days_left} GÜN KALDI"
                    else:
                        status = f"⚪ {days_left} GÜN KALDI"

                except ValueError:
                    status = ""

                lines.append(f"### {i}. {sure['sure_tipi']} - {status}")
                lines.append("")
                lines.append(f"**Tarih:** {sure['sure_tarihi']}")
                lines.append("")

                if sure['aciklama']:
                    lines.append(f"**Açıklama:**")
                    lines.append(f"> {sure['aciklama']}")
                    lines.append("")

                lines.append("---")
                lines.append("")

        # Footer
        lines.append("")
        lines.append("_Bu dosya otomatik olarak oluşturulmuştur._")

        return '\n'.join(lines)
