"""
Dava Yönetim Sistemi - Konfigürasyon Ayarları
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any


class Config:
    """Sistem konfigürasyonu yönetimi"""

    def __init__(self, config_path: str = None):
        """
        Config sınıfı başlatıcı

        Args:
            config_path: Konfigürasyon dosyası yolu (None ise varsayılan kullanılır)
        """
        if config_path is None:
            self.config_dir = Path.home() / '.dava-yonetim'
            self.config_file = self.config_dir / 'config.json'
        else:
            self.config_file = Path(config_path)
            self.config_dir = self.config_file.parent

        # Varsayılan ayarlar
        self.default_config = {
            'watched_folders': [],
            'database_path': str(self.config_dir / 'dava.db'),
            'backup_folder': str(self.config_dir / 'backup'),
            'log_folder': str(self.config_dir / 'logs'),
            'tesseract_lang': 'tur',
            'notification_enabled': True,
            'file_patterns': {
                'duruşma': ['DURUŞMA', 'CELSE', 'TUTANAK'],
                'bilirkişi': ['BİLİRKİŞİ', 'RAPOR', 'EKSPERTIZ'],
                'tebligat': ['TEBLİGAT', 'İHBARNAME', 'İHTAR'],
                'karar': ['KARAR', 'HÜKÜM', 'İLAM']
            },
            'date_patterns': [
                r'\d{1,2}[./]\d{1,2}[./]\d{4}',
                r'\d{4}[./]\d{1,2}[./]\d{1,2}'
            ],
            'deadline_keywords': [
                'sonraki duruşma',
                'celse',
                'rapor süresi',
                'süre',
                'tarihinde'
            ]
        }

        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Konfigürasyon dosyasını yükler

        Returns:
            Konfigürasyon dictionary'si
        """
        # Klasör yoksa oluştur
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Config dosyası varsa yükle
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Varsayılan ayarları güncelle
                    config = self.default_config.copy()
                    config.update(loaded_config)
                    return config
            except json.JSONDecodeError:
                print(f"⚠️  Konfigürasyon dosyası okunamadı, varsayılan ayarlar kullanılıyor")
                return self.default_config.copy()
        else:
            # İlk kez kullanılıyor, varsayılan ayarları kaydet
            self.save_config(self.default_config)
            return self.default_config.copy()

    def save_config(self, config: Dict[str, Any] = None) -> None:
        """
        Konfigürasyonu dosyaya kaydeder

        Args:
            config: Kaydedilecek konfigürasyon (None ise mevcut config kullanılır)
        """
        if config is None:
            config = self.config

        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def add_watched_folder(self, folder_path: str) -> bool:
        """
        İzlenecek klasör ekler

        Args:
            folder_path: Eklenecek klasör yolu

        Returns:
            Başarılı ise True
        """
        folder_path = os.path.abspath(folder_path)

        if not os.path.isdir(folder_path):
            print(f"❌ Klasör bulunamadı: {folder_path}")
            return False

        if folder_path not in self.config['watched_folders']:
            self.config['watched_folders'].append(folder_path)
            self.save_config()
            print(f"✅ Klasör eklendi: {folder_path}")
            return True
        else:
            print(f"⚠️  Klasör zaten izleniyor: {folder_path}")
            return False

    def remove_watched_folder(self, folder_path: str) -> bool:
        """
        İzlenen klasörü kaldırır

        Args:
            folder_path: Kaldırılacak klasör yolu

        Returns:
            Başarılı ise True
        """
        folder_path = os.path.abspath(folder_path)

        if folder_path in self.config['watched_folders']:
            self.config['watched_folders'].remove(folder_path)
            self.save_config()
            print(f"✅ Klasör kaldırıldı: {folder_path}")
            return True
        else:
            print(f"⚠️  Klasör zaten izlenmiyor: {folder_path}")
            return False

    def get_watched_folders(self) -> List[str]:
        """
        İzlenen klasörleri döndürür

        Returns:
            İzlenen klasör listesi
        """
        return self.config.get('watched_folders', [])

    def get(self, key: str, default=None) -> Any:
        """
        Konfigürasyon değerini döndürür

        Args:
            key: Konfigürasyon anahtarı
            default: Varsayılan değer

        Returns:
            Konfigürasyon değeri
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Konfigürasyon değerini ayarlar

        Args:
            key: Konfigürasyon anahtarı
            value: Yeni değer
        """
        self.config[key] = value
        self.save_config()
