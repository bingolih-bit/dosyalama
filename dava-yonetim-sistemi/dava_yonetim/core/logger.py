"""
Dava Yönetim Sistemi - Loglama Modülü
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """Sistem loglama yönetimi"""

    _instance: Optional['Logger'] = None

    def __new__(cls, log_dir: str = None):
        """Singleton pattern ile tek instance oluştur"""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_dir: str = None):
        """
        Logger sınıfı başlatıcı

        Args:
            log_dir: Log klasörü yolu
        """
        if self._initialized:
            return

        if log_dir is None:
            self.log_dir = Path.home() / '.dava-yonetim' / 'logs'
        else:
            self.log_dir = Path(log_dir)

        # Log klasörünü oluştur
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Log dosyası
        log_file = self.log_dir / f"dava_yonetim_{datetime.now().strftime('%Y%m%d')}.log"

        # Logger konfigürasyonu
        self.logger = logging.getLogger('DavaYonetim')
        self.logger.setLevel(logging.DEBUG)

        # Önceki handler'ları temizle
        if self.logger.handlers:
            self.logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self._initialized = True

    def debug(self, message: str) -> None:
        """Debug seviyesinde log"""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Info seviyesinde log"""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Warning seviyesinde log"""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Error seviyesinde log"""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Critical seviyesinde log"""
        self.logger.critical(message)

    def log_file_operation(self, operation: str, file_path: str, status: str) -> None:
        """
        Dosya işlemi logu

        Args:
            operation: İşlem tipi (OCR, Rename, vb.)
            file_path: Dosya yolu
            status: İşlem durumu
        """
        self.info(f"{operation} | {file_path} | {status}")

    def log_error_with_exception(self, message: str, exc: Exception) -> None:
        """
        Hata logu (exception ile)

        Args:
            message: Hata mesajı
            exc: Exception nesnesi
        """
        self.error(f"{message}: {str(exc)}")
        self.logger.exception(exc)
