"""
Dava Yönetim Sistemi - Klasör İzleme Modülü
"""

import os
import time
from pathlib import Path
from typing import List, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from .database import Database
from .logger import Logger
from .ocr_engine import OCREngine
from .file_analyzer import FileAnalyzer
from .file_renamer import FileRenamer
from .summary_generator import SummaryGenerator
from .deadline_tracker import DeadlineTracker
from ..config import Config


class PDFEventHandler(FileSystemEventHandler):
    """PDF dosyası ekleme olaylarını işle"""

    def __init__(self, watcher: 'FolderWatcher'):
        """
        PDFEventHandler sınıfı başlatıcı

        Args:
            watcher: FolderWatcher instance
        """
        super().__init__()
        self.watcher = watcher

    def on_created(self, event: FileCreatedEvent) -> None:
        """
        Yeni dosya oluşturulduğunda tetiklenir

        Args:
            event: Dosya sistemi olayı
        """
        # Klasörse veya PDF değilse işleme
        if event.is_directory:
            return

        file_path = event.src_path

        # PDF dosyası mı?
        if not file_path.lower().endswith('.pdf'):
            return

        # İşlenmiş dosyalar arasında mı? (çift işleme önleme)
        if file_path in self.watcher.processed_files:
            return

        # Geçici/sistem dosyası mı?
        if Path(file_path).name.startswith('.') or Path(file_path).name.startswith('~'):
            return

        # Özet dosyası mı?
        if '_DOSYA_OZET' in file_path or '_YAPILACAKLAR' in file_path:
            return

        self.watcher.logger.info(f"Yeni PDF tespit edildi: {file_path}")

        # Dosyanın tam yazılmasını bekle
        time.sleep(2)

        # Dosyayı işle
        self.watcher.process_pdf(file_path)


class FolderWatcher:
    """Klasörleri izler ve yeni PDF'leri otomatik işler"""

    def __init__(self, config: Config = None):
        """
        FolderWatcher sınıfı başlatıcı

        Args:
            config: Config instance
        """
        self.config = config or Config()
        self.logger = Logger(log_dir=self.config.get('log_folder'))
        self.db = Database(db_path=self.config.get('database_path'))

        # OCR ve analiz araçları
        self.ocr = OCREngine(lang=self.config.get('tesseract_lang', 'tur'))
        self.analyzer = FileAnalyzer(
            file_patterns=self.config.get('file_patterns'),
            date_patterns=self.config.get('date_patterns'),
            deadline_keywords=self.config.get('deadline_keywords')
        )
        self.renamer = FileRenamer(
            backup_folder=self.config.get('backup_folder'),
            logger=self.logger
        )
        self.summary = SummaryGenerator(database=self.db, logger=self.logger)
        self.tracker = DeadlineTracker(
            database=self.db,
            logger=self.logger,
            notification_enabled=self.config.get('notification_enabled', True)
        )

        # Watchdog observer
        self.observer = Observer()

        # İşlenmiş dosyalar (çift işleme önleme)
        self.processed_files: Set[str] = set()

    def start(self) -> None:
        """Klasör izlemeyi başlat"""
        watched_folders = self.config.get_watched_folders()

        if not watched_folders:
            self.logger.warning("İzlenecek klasör bulunamadı!")
            print("⚠️  İzlenecek klasör yok. Önce 'dava-config add <klasör>' ile klasör ekleyin.")
            return

        # Her klasör için event handler ekle
        event_handler = PDFEventHandler(self)

        for folder in watched_folders:
            if os.path.isdir(folder):
                self.observer.schedule(event_handler, folder, recursive=True)
                self.logger.info(f"İzleme başlatıldı: {folder}")
                print(f"✅ İzleniyor: {folder}")

                # Dava kaydını ekle (yoksa)
                self.db.add_dava(
                    klasor_adi=Path(folder).name,
                    klasor_yolu=folder
                )
            else:
                self.logger.warning(f"Klasör bulunamadı: {folder}")
                print(f"⚠️  Klasör bulunamadı: {folder}")

        # Observer'ı başlat
        self.observer.start()
        print("\n🚀 Dava Yönetim Sistemi çalışıyor...")
        print("📁 PDF dosyaları otomatik olarak işlenecek.")
        print("⏸  Durdurmak için Ctrl+C yapın.\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Klasör izlemeyi durdur"""
        self.observer.stop()
        self.observer.join()
        self.logger.info("İzleme durduruldu")
        print("\n✋ Dava Yönetim Sistemi durduruldu.")

    def process_pdf(self, file_path: str) -> bool:
        """
        PDF dosyasını işle (OCR, analiz, yeniden adlandırma)

        Args:
            file_path: PDF dosya yolu

        Returns:
            Başarılı ise True
        """
        try:
            self.logger.info(f"PDF işleniyor: {file_path}")
            print(f"\n📄 İşleniyor: {Path(file_path).name}")

            # İşlenmiş olarak işaretle
            self.processed_files.add(file_path)

            # 1. OCR ile metin çıkar
            print("  🔍 OCR yapılıyor...")
            text = self.ocr.pdf_to_text(file_path)

            if not text or len(text.strip()) < 50:
                self.logger.warning(f"OCR metni çok kısa veya boş: {file_path}")
                print("  ⚠️  OCR metni bulunamadı veya çok kısa")
                return False

            # 2. Metni analiz et
            print("  🔬 Analiz ediliyor...")
            analysis = self.analyzer.analyze_text(text)

            file_type = analysis['file_type']
            document_date = analysis['document_date']
            deadlines = analysis['deadlines']

            print(f"  📋 Tip: {file_type or 'Tespit edilemedi'}")
            print(f"  📅 Tarih: {document_date or 'Tespit edilemedi'}")
            print(f"  ⏰ Süre sayısı: {len(deadlines)}")

            # 3. Dosyayı yeniden adlandır
            print("  ✏️  Yeniden adlandırılıyor...")
            success, new_path = self.renamer.rename_file(
                file_path, file_type, document_date
            )

            if not success or not new_path:
                self.logger.error(f"Dosya yeniden adlandırılamadı: {file_path}")
                print("  ❌ Yeniden adlandırma başarısız")
                return False

            # Yeni yolu işlenmiş olarak işaretle
            self.processed_files.add(new_path)

            print(f"  ✅ Yeni ad: {Path(new_path).name}")

            # 4. Veritabanına ekle
            dava_folder = str(Path(new_path).parent)
            dava = self.db.get_dava_by_path(dava_folder)

            if not dava:
                # Dava kaydı oluştur
                dava_id = self.db.add_dava(
                    klasor_adi=Path(dava_folder).name,
                    klasor_yolu=dava_folder
                )
            else:
                dava_id = dava['id']

            # Dosya kaydı oluştur
            dosya_id = self.db.add_dosya(
                dava_id=dava_id,
                dosya_adi=Path(new_path).name,
                orijinal_adi=Path(file_path).name,
                dosya_yolu=new_path,
                dosya_tipi=file_type,
                dosya_tarihi=document_date,
                ocr_metni=text[:1000]  # İlk 1000 karakter
            )

            # 5. Süreleri ekle
            if deadlines:
                print(f"  ⏰ {len(deadlines)} süre ekleniyor...")
                added = self.tracker.add_deadline_from_analysis(
                    dava_id, dosya_id, deadlines
                )
                print(f"  ✅ {added} süre eklendi")

            # 6. Özet dosyalarını güncelle
            print("  📊 Özet dosyaları güncelleniyor...")
            self.summary.generate_summary(dava_folder)
            self.summary.generate_todo_file(dava_folder)

            # 7. Log ekle
            self.db.add_log(
                islem_tipi='PDF_PROCESS',
                durum='SUCCESS',
                dosya_yolu=new_path,
                detay=f"Tip: {file_type}, Tarih: {document_date}"
            )

            print("  ✅ İşlem tamamlandı!\n")
            return True

        except Exception as e:
            self.logger.error_with_exception(f"PDF işleme hatası: {file_path}", e)
            print(f"  ❌ Hata: {str(e)}\n")

            # Hata log'u
            self.db.add_log(
                islem_tipi='PDF_PROCESS',
                durum='ERROR',
                dosya_yolu=file_path,
                detay=str(e)
            )

            return False

    def process_existing_pdfs(self, folder_path: str) -> None:
        """
        Klasördeki mevcut PDF'leri işle

        Args:
            folder_path: Klasör yolu
        """
        folder = Path(folder_path)

        if not folder.exists() or not folder.is_dir():
            self.logger.error(f"Klasör bulunamadı: {folder_path}")
            print(f"❌ Klasör bulunamadı: {folder_path}")
            return

        # Tüm PDF'leri bul
        pdf_files = list(folder.rglob('*.pdf'))

        # Özet dosyalarını filtrele
        pdf_files = [f for f in pdf_files
                    if '_DOSYA_OZET' not in f.name and '_YAPILACAKLAR' not in f.name]

        if not pdf_files:
            print(f"📁 {folder_path} klasöründe PDF bulunamadı")
            return

        print(f"\n📁 {len(pdf_files)} PDF dosyası bulundu")
        print("🔄 İşleniyor...\n")

        success_count = 0
        for pdf_file in pdf_files:
            if self.process_pdf(str(pdf_file)):
                success_count += 1

        print(f"\n✅ {success_count}/{len(pdf_files)} dosya başarıyla işlendi")
