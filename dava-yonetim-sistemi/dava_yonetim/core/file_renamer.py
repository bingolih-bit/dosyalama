"""
Dava Yönetim Sistemi - Dosya Yeniden Adlandırma Modülü
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from .logger import Logger


class FileRenamer:
    """Dosyaları akıllıca yeniden adlandırır ve yedekler"""

    def __init__(self, backup_folder: str = None, logger: Logger = None):
        """
        FileRenamer sınıfı başlatıcı

        Args:
            backup_folder: Yedekleme klasörü yolu
            logger: Logger instance
        """
        if backup_folder is None:
            backup_folder = str(Path.home() / '.dava-yonetim' / 'backup')

        self.backup_folder = Path(backup_folder)
        self.backup_folder.mkdir(parents=True, exist_ok=True)

        self.logger = logger or Logger()

    def rename_file(self, file_path: str, file_type: Optional[str],
                   document_date: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Dosyayı akıllıca yeniden adlandır

        Args:
            file_path: Orijinal dosya yolu
            file_type: Dosya tipi (durusma, bilirkisi, vb.)
            document_date: Belge tarihi (YYYY-MM-DD formatında)

        Returns:
            (başarılı mı, yeni dosya yolu)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            self.logger.error(f"Dosya bulunamadı: {file_path}")
            return False, None

        # Yeni dosya adını oluştur
        new_name = self._generate_new_name(
            file_path.name,
            file_type,
            document_date
        )

        # Yeni dosya yolu
        new_path = file_path.parent / new_name

        # Eğer aynı isimde dosya varsa, sayı ekle
        new_path = self._get_unique_path(new_path)

        try:
            # Orijinal dosyayı yedekle
            self._backup_file(file_path)

            # Dosyayı yeniden adlandır
            file_path.rename(new_path)

            self.logger.info(f"Dosya yeniden adlandırıldı: {file_path.name} → {new_path.name}")
            self.logger.log_file_operation('RENAME', str(new_path), 'SUCCESS')

            return True, str(new_path)

        except Exception as e:
            self.logger.error(f"Dosya yeniden adlandırma hatası: {str(e)}")
            self.logger.log_file_operation('RENAME', str(file_path), f'ERROR: {str(e)}')
            return False, None

    def _generate_new_name(self, original_name: str,
                          file_type: Optional[str],
                          document_date: Optional[str]) -> str:
        """
        Yeni dosya adını oluştur

        Args:
            original_name: Orijinal dosya adı
            file_type: Dosya tipi
            document_date: Belge tarihi

        Returns:
            Yeni dosya adı
        """
        # Dosya uzantısını al
        ext = Path(original_name).suffix

        # Tarih kısmı
        if document_date:
            date_part = document_date  # YYYY-MM-DD formatında
        else:
            # Tarih yoksa, bugünün tarihini kullan
            date_part = datetime.now().strftime('%Y-%m-%d')

        # Tip kısmı
        if file_type:
            type_part = file_type.capitalize()
        else:
            type_part = 'Belge'

        # Yeni isim: YYYY-MM-DD_Tip.pdf
        new_name = f"{date_part}_{type_part}{ext}"

        return new_name

    def _get_unique_path(self, path: Path) -> Path:
        """
        Eşsiz dosya yolu oluştur (aynı isimde dosya varsa sayı ekle)

        Args:
            path: İstenen dosya yolu

        Returns:
            Eşsiz dosya yolu
        """
        if not path.exists():
            return path

        # Dosya adı ve uzantı
        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        # Sayı ekle
        counter = 1
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    def _backup_file(self, file_path: Path) -> None:
        """
        Dosyayı yedekle

        Args:
            file_path: Yedeklenecek dosya yolu
        """
        # Yedek klasöründe tarih bazlı alt klasör oluştur
        today = datetime.now().strftime('%Y-%m-%d')
        backup_dir = self.backup_folder / today
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Yedek dosya yolu
        backup_path = backup_dir / file_path.name

        # Aynı isimde yedek varsa, sayı ekle
        backup_path = self._get_unique_path(backup_path)

        try:
            shutil.copy2(file_path, backup_path)
            self.logger.debug(f"Yedek oluşturuldu: {backup_path}")

        except Exception as e:
            self.logger.warning(f"Yedek oluşturma hatası: {str(e)}")

    def restore_from_backup(self, backup_file: str, target_dir: str) -> bool:
        """
        Yedekten dosyayı geri yükle

        Args:
            backup_file: Yedek dosya yolu
            target_dir: Hedef klasör

        Returns:
            Başarılı ise True
        """
        backup_path = Path(backup_file)
        target_dir = Path(target_dir)

        if not backup_path.exists():
            self.logger.error(f"Yedek dosya bulunamadı: {backup_path}")
            return False

        if not target_dir.exists():
            self.logger.error(f"Hedef klasör bulunamadı: {target_dir}")
            return False

        try:
            target_path = target_dir / backup_path.name
            target_path = self._get_unique_path(target_path)

            shutil.copy2(backup_path, target_path)
            self.logger.info(f"Yedekten geri yüklendi: {target_path}")

            return True

        except Exception as e:
            self.logger.error(f"Geri yükleme hatası: {str(e)}")
            return False

    def clean_old_backups(self, days: int = 30) -> None:
        """
        Eski yedekleri temizle

        Args:
            days: Kaç günden eski yedekleri sil
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        try:
            for backup_dir in self.backup_folder.iterdir():
                if backup_dir.is_dir():
                    # Klasör tarihi cutoff'tan eski mi?
                    if backup_dir.stat().st_mtime < cutoff_date:
                        shutil.rmtree(backup_dir)
                        deleted_count += 1

            if deleted_count > 0:
                self.logger.info(f"{deleted_count} eski yedek klasörü temizlendi")

        except Exception as e:
            self.logger.error(f"Yedek temizleme hatası: {str(e)}")
