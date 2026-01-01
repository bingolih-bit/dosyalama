"""
Dava Yönetim Sistemi - Süre Takip Modülü
"""

import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .database import Database
from .logger import Logger


class DeadlineTracker:
    """Süreleri takip eder ve hatırlatma gönderir"""

    def __init__(self, database: Database = None, logger: Logger = None,
                 notification_enabled: bool = True):
        """
        DeadlineTracker sınıfı başlatıcı

        Args:
            database: Database instance
            logger: Logger instance
            notification_enabled: Bildirim gönderilsin mi
        """
        self.db = database or Database()
        self.logger = logger or Logger()
        self.notification_enabled = notification_enabled

    def check_deadlines(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Yaklaşan süreleri kontrol et

        Args:
            days_ahead: Kaç gün öncesinden kontrol edilsin

        Returns:
            Yaklaşan süreler listesi
        """
        sureler = self.db.get_yaklasan_sureler(gun_sayisi=days_ahead)

        if sureler:
            self.logger.info(f"{len(sureler)} yaklaşan süre bulundu")

            # Bildirimleri gönder
            if self.notification_enabled:
                self._send_notifications(sureler)

        return sureler

    def add_deadline_from_analysis(self, dava_id: int, dosya_id: int,
                                   deadlines: List[Dict[str, str]]) -> int:
        """
        Dosya analizinden çıkan süreleri ekle

        Args:
            dava_id: Dava ID
            dosya_id: Dosya ID
            deadlines: Süre listesi [{'date': 'YYYY-MM-DD', 'context': '...'}]

        Returns:
            Eklenen süre sayısı
        """
        count = 0

        for deadline in deadlines:
            try:
                # Süre tipini context'ten çıkar
                sure_tipi = self._extract_deadline_type(deadline['context'])

                # Süreyi ekle
                self.db.add_sure(
                    dava_id=dava_id,
                    dosya_id=dosya_id,
                    sure_tipi=sure_tipi,
                    sure_tarihi=deadline['date'],
                    aciklama=deadline['context']
                )

                count += 1
                self.logger.info(f"Süre eklendi: {sure_tipi} - {deadline['date']}")

            except Exception as e:
                self.logger.error(f"Süre ekleme hatası: {str(e)}")

        return count

    def _extract_deadline_type(self, context: str) -> str:
        """
        Context'ten süre tipini çıkar

        Args:
            context: Süre açıklaması

        Returns:
            Süre tipi
        """
        context_lower = context.lower()

        if 'duruşma' in context_lower or 'celse' in context_lower:
            return 'Duruşma'
        elif 'rapor' in context_lower:
            return 'Rapor Süresi'
        elif 'süre' in context_lower:
            return 'Genel Süre'
        else:
            return 'Diğer'

    def _send_notifications(self, sureler: List[Dict[str, Any]]) -> None:
        """
        macOS bildirimleri gönder

        Args:
            sureler: Süre listesi
        """
        # Her süre için bildirim gönder
        for sure in sureler:
            try:
                # Tarihe kalan gün sayısını hesapla
                sure_date = datetime.strptime(sure['sure_tarihi'], '%Y-%m-%d')
                today = datetime.now()
                days_left = (sure_date - today).days

                # Bildirim mesajı
                if days_left == 0:
                    message = f"BUGÜN: {sure['sure_tipi']}"
                elif days_left == 1:
                    message = f"YARIN: {sure['sure_tipi']}"
                else:
                    message = f"{days_left} gün içinde: {sure['sure_tipi']}"

                # macOS bildirimi gönder
                self._send_macos_notification(
                    title="Dava Yönetim - Yaklaşan Süre",
                    message=message,
                    subtitle=sure['klasor_adi']
                )

            except Exception as e:
                self.logger.error(f"Bildirim gönderme hatası: {str(e)}")

    def _send_macos_notification(self, title: str, message: str,
                                 subtitle: str = None) -> None:
        """
        macOS bildirim gönder (osascript kullanarak)

        Args:
            title: Bildirim başlığı
            message: Bildirim mesajı
            subtitle: Bildirim alt başlığı
        """
        try:
            # AppleScript komutu
            script = f'display notification "{message}" with title "{title}"'

            if subtitle:
                script = f'display notification "{message}" with title "{title}" subtitle "{subtitle}"'

            subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                check=True
            )

            self.logger.debug(f"Bildirim gönderildi: {title}")

        except (subprocess.CalledProcessError, FileNotFoundError):
            # macOS değilse veya osascript yoksa, log'a yaz
            self.logger.warning(f"Bildirim gönderilemedi: {title} - {message}")

    def get_deadline_summary(self) -> Dict[str, Any]:
        """
        Süre özetini al

        Returns:
            Özet dictionary'si
        """
        # Bugün
        today = datetime.now().date()

        # Bu hafta (7 gün)
        week_sureler = self.db.get_yaklasan_sureler(gun_sayisi=7)

        # Bu ay (30 gün)
        month_sureler = self.db.get_yaklasan_sureler(gun_sayisi=30)

        # Bugün
        today_sureler = [s for s in week_sureler
                        if s['sure_tarihi'] == today.strftime('%Y-%m-%d')]

        # Geçmiş süreler
        all_sureler = self.db.get_yaklasan_sureler(gun_sayisi=365)
        past_sureler = [s for s in all_sureler
                       if datetime.strptime(s['sure_tarihi'], '%Y-%m-%d').date() < today]

        return {
            'bugun': len(today_sureler),
            'bu_hafta': len(week_sureler),
            'bu_ay': len(month_sureler),
            'gecmis': len(past_sureler),
            'bugun_sureler': today_sureler,
            'bu_hafta_sureler': week_sureler
        }

    def remind_today(self) -> None:
        """Bugünün sürelerini hatırlat"""
        today = datetime.now().strftime('%Y-%m-%d')

        # Bugünün sürelerini al
        all_sureler = self.db.get_yaklasan_sureler(gun_sayisi=1)
        today_sureler = [s for s in all_sureler if s['sure_tarihi'] == today]

        if today_sureler:
            self.logger.info(f"Bugün {len(today_sureler)} süre var")

            if self.notification_enabled:
                # Toplu bildirim gönder
                message = f"Bugün {len(today_sureler)} süre var!"
                self._send_macos_notification(
                    title="Dava Yönetim - Günlük Hatırlatma",
                    message=message
                )

                # Detaylı bildirimleri gönder
                self._send_notifications(today_sureler)
        else:
            self.logger.info("Bugün süre yok")
