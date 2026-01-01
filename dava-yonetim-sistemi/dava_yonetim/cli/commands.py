"""
Dava Yönetim Sistemi - CLI Komutları
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List

from ..config import Config
from ..core.database import Database
from ..core.logger import Logger
from ..core.watcher import FolderWatcher
from ..core.deadline_tracker import DeadlineTracker


class CLI:
    """Komut satırı arayüzü"""

    def __init__(self):
        """CLI sınıfı başlatıcı"""
        self.config = Config()
        self.db = Database(db_path=self.config.get('database_path'))
        self.logger = Logger(log_dir=self.config.get('log_folder'))

    def run(self, args: List[str] = None) -> None:
        """
        CLI'yi çalıştır

        Args:
            args: Komut satırı argümanları
        """
        parser = argparse.ArgumentParser(
            description='Dava Dosya Yönetim Sistemi',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        subparsers = parser.add_subparsers(dest='command', help='Komutlar')

        # dava-kur
        parser_kur = subparsers.add_parser('kur', help='Sistemi kur')

        # dava-config
        parser_config = subparsers.add_parser('config', help='Konfigürasyon')
        config_subparsers = parser_config.add_subparsers(dest='config_command')

        parser_config_add = config_subparsers.add_parser('add', help='Klasör ekle')
        parser_config_add.add_argument('folder', help='Eklenecek klasör yolu')

        parser_config_remove = config_subparsers.add_parser('remove', help='Klasör kaldır')
        parser_config_remove.add_argument('folder', help='Kaldırılacak klasör yolu')

        parser_config_list = config_subparsers.add_parser('list', help='Klasörleri listele')

        # dava-baslat
        parser_baslat = subparsers.add_parser('baslat', help='Sistemi başlat')

        # dava-durum
        parser_durum = subparsers.add_parser('durum', help='Sistem durumu')

        # dava-analiz
        parser_analiz = subparsers.add_parser('analiz', help='Klasörü analiz et')
        parser_analiz.add_argument('folder', help='Analiz edilecek klasör')

        # dava-sureler
        parser_sureler = subparsers.add_parser('sureler', help='Yaklaşan süreler')
        parser_sureler.add_argument('--days', type=int, default=30,
                                   help='Kaç gün içindeki süreler (varsayılan: 30)')

        # Parse arguments
        parsed_args = parser.parse_args(args)

        # Komut yok
        if not parsed_args.command:
            parser.print_help()
            return

        # Komutları çalıştır
        if parsed_args.command == 'kur':
            self.cmd_kur()
        elif parsed_args.command == 'config':
            if parsed_args.config_command == 'add':
                self.cmd_config_add(parsed_args.folder)
            elif parsed_args.config_command == 'remove':
                self.cmd_config_remove(parsed_args.folder)
            elif parsed_args.config_command == 'list':
                self.cmd_config_list()
            else:
                parser_config.print_help()
        elif parsed_args.command == 'baslat':
            self.cmd_baslat()
        elif parsed_args.command == 'durum':
            self.cmd_durum()
        elif parsed_args.command == 'analiz':
            self.cmd_analiz(parsed_args.folder)
        elif parsed_args.command == 'sureler':
            self.cmd_sureler(parsed_args.days)

    def cmd_kur(self) -> None:
        """Sistemi kur"""
        print("🚀 Dava Yönetim Sistemi Kurulumu")
        print("=" * 50)
        print()

        # Konfigürasyon klasörünü oluştur
        config_dir = Path.home() / '.dava-yonetim'
        config_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Konfigürasyon klasörü: {config_dir}")

        # Alt klasörleri oluştur
        (config_dir / 'logs').mkdir(exist_ok=True)
        (config_dir / 'backup').mkdir(exist_ok=True)
        print("✅ Alt klasörler oluşturuldu")

        # Veritabanını oluştur
        db = Database(db_path=str(config_dir / 'dava.db'))
        print("✅ Veritabanı oluşturuldu")

        # Konfigürasyon dosyasını oluştur
        config = Config()
        print("✅ Konfigürasyon dosyası oluşturuldu")

        print()
        print("✅ Kurulum tamamlandı!")
        print()
        print("📝 Sonraki adımlar:")
        print("  1. dava-yonetim config add <klasör-yolu>  # Klasör ekle")
        print("  2. dava-yonetim baslat                    # Sistemi başlat")
        print()

    def cmd_config_add(self, folder: str) -> None:
        """Klasör ekle"""
        folder = os.path.abspath(folder)

        if not os.path.isdir(folder):
            print(f"❌ Klasör bulunamadı: {folder}")
            sys.exit(1)

        self.config.add_watched_folder(folder)

        # Dava kaydını ekle
        self.db.add_dava(
            klasor_adi=Path(folder).name,
            klasor_yolu=folder
        )

        print()
        print("💡 İpucu: Mevcut PDF'leri işlemek için:")
        print(f"   dava-yonetim analiz {folder}")
        print()

    def cmd_config_remove(self, folder: str) -> None:
        """Klasör kaldır"""
        folder = os.path.abspath(folder)
        self.config.remove_watched_folder(folder)

    def cmd_config_list(self) -> None:
        """Klasörleri listele"""
        folders = self.config.get_watched_folders()

        if not folders:
            print("📁 Henüz klasör eklenmemiş")
            print()
            print("Klasör eklemek için:")
            print("  dava-yonetim config add <klasör-yolu>")
            return

        print("📁 İzlenen Klasörler:")
        print("=" * 50)
        for i, folder in enumerate(folders, 1):
            exists = "✅" if os.path.isdir(folder) else "❌"
            print(f"{i}. {exists} {folder}")

        print()

    def cmd_baslat(self) -> None:
        """Sistemi başlat"""
        watcher = FolderWatcher(config=self.config)
        watcher.start()

    def cmd_durum(self) -> None:
        """Sistem durumu"""
        print("📊 Dava Yönetim Sistemi - Durum Raporu")
        print("=" * 50)
        print()

        # İstatistikler
        stats = self.db.get_istatistikler()

        print(f"📂 Toplam Dava Sayısı: {stats['toplam_dava']}")
        print(f"📄 Toplam Dosya Sayısı: {stats['toplam_dosya']}")
        print(f"⏰ Aktif Süre Sayısı: {stats['aktif_sure']}")
        print()

        # Dosya tipi dağılımı
        if stats['dosya_tipi_dagilim']:
            print("📋 Dosya Tipi Dağılımı:")
            for tip, sayi in stats['dosya_tipi_dagilim'].items():
                tip_name = tip if tip else 'Diğer'
                print(f"  • {tip_name.capitalize()}: {sayi}")
            print()

        # Yaklaşan süreler
        tracker = DeadlineTracker(database=self.db, logger=self.logger,
                                 notification_enabled=False)
        summary = tracker.get_deadline_summary()

        print("📅 Süre Özeti:")
        print(f"  • Bugün: {summary['bugun']}")
        print(f"  • Bu hafta: {summary['bu_hafta']}")
        print(f"  • Bu ay: {summary['bu_ay']}")

        if summary['gecmis'] > 0:
            print(f"  ⚠️  Geçmiş süreler: {summary['gecmis']}")

        print()

        # İzlenen klasörler
        folders = self.config.get_watched_folders()
        print(f"📁 İzlenen Klasör Sayısı: {len(folders)}")
        print()

    def cmd_analiz(self, folder: str) -> None:
        """Klasörü analiz et"""
        folder = os.path.abspath(folder)

        if not os.path.isdir(folder):
            print(f"❌ Klasör bulunamadı: {folder}")
            sys.exit(1)

        print(f"🔍 Klasör analizi başlatılıyor: {folder}")
        print()

        watcher = FolderWatcher(config=self.config)
        watcher.process_existing_pdfs(folder)

    def cmd_sureler(self, days: int) -> None:
        """Yaklaşan süreleri göster"""
        tracker = DeadlineTracker(database=self.db, logger=self.logger,
                                 notification_enabled=False)

        sureler = self.db.get_yaklasan_sureler(gun_sayisi=days)

        if not sureler:
            print(f"✅ {days} gün içinde süre yok")
            return

        print(f"⏰ Yaklaşan Süreler ({days} gün içinde)")
        print("=" * 70)
        print()

        for i, sure in enumerate(sureler, 1):
            print(f"{i}. {sure['sure_tipi']} - {sure['sure_tarihi']}")
            print(f"   📁 Klasör: {sure['klasor_adi']}")

            if sure['aciklama']:
                aciklama = sure['aciklama'][:100]
                print(f"   📝 {aciklama}")

            print()
