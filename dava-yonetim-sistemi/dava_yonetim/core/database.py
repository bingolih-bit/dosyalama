"""
Dava Yönetim Sistemi - Veritabanı Modülü
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class Database:
    """SQLite veritabanı yönetimi"""

    def __init__(self, db_path: str = None):
        """
        Database sınıfı başlatıcı

        Args:
            db_path: Veritabanı dosya yolu
        """
        if db_path is None:
            db_dir = Path.home() / '.dava-yonetim'
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(db_dir / 'dava.db')
        else:
            self.db_path = db_path

        self.conn: Optional[sqlite3.Connection] = None
        self.init_database()

    def connect(self) -> sqlite3.Connection:
        """Veritabanına bağlan"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self) -> None:
        """Veritabanı bağlantısını kapat"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def init_database(self) -> None:
        """Veritabanı tablolarını oluştur"""
        conn = self.connect()
        cursor = conn.cursor()

        # Davalar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS davalar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                klasor_adi TEXT NOT NULL,
                klasor_yolu TEXT NOT NULL UNIQUE,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Dosyalar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dosyalar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dava_id INTEGER NOT NULL,
                dosya_adi TEXT NOT NULL,
                orijinal_adi TEXT NOT NULL,
                dosya_yolu TEXT NOT NULL,
                dosya_tipi TEXT,
                dosya_tarihi DATE,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ocr_metni TEXT,
                FOREIGN KEY (dava_id) REFERENCES davalar(id) ON DELETE CASCADE
            )
        ''')

        # Süreler tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sureler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dava_id INTEGER NOT NULL,
                dosya_id INTEGER,
                sure_tipi TEXT NOT NULL,
                sure_tarihi DATE NOT NULL,
                aciklama TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tamamlandi BOOLEAN DEFAULT 0,
                FOREIGN KEY (dava_id) REFERENCES davalar(id) ON DELETE CASCADE,
                FOREIGN KEY (dosya_id) REFERENCES dosyalar(id) ON DELETE SET NULL
            )
        ''')

        # Loglar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loglar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                islem_tipi TEXT NOT NULL,
                dosya_yolu TEXT,
                durum TEXT NOT NULL,
                detay TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # İndeksler
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_dosyalar_dava_id
            ON dosyalar(dava_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sureler_dava_id
            ON sureler(dava_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sureler_tarihi
            ON sureler(sure_tarihi)
        ''')

        conn.commit()

    def add_dava(self, klasor_adi: str, klasor_yolu: str) -> int:
        """
        Yeni dava ekle

        Args:
            klasor_adi: Dava klasör adı
            klasor_yolu: Dava klasör yolu

        Returns:
            Oluşturulan dava ID'si
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO davalar (klasor_adi, klasor_yolu)
                VALUES (?, ?)
            ''', (klasor_adi, klasor_yolu))

            conn.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            # Dava zaten var, ID'sini döndür
            cursor.execute('''
                SELECT id FROM davalar WHERE klasor_yolu = ?
            ''', (klasor_yolu,))

            result = cursor.fetchone()
            return result['id'] if result else 0

    def get_dava_by_path(self, klasor_yolu: str) -> Optional[Dict[str, Any]]:
        """
        Klasör yoluna göre dava bilgisini getir

        Args:
            klasor_yolu: Dava klasör yolu

        Returns:
            Dava bilgisi dictionary'si
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM davalar WHERE klasor_yolu = ?
        ''', (klasor_yolu,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def add_dosya(self, dava_id: int, dosya_adi: str, orijinal_adi: str,
                  dosya_yolu: str, dosya_tipi: str = None,
                  dosya_tarihi: str = None, ocr_metni: str = None) -> int:
        """
        Yeni dosya ekle

        Args:
            dava_id: Dava ID
            dosya_adi: Yeni dosya adı
            orijinal_adi: Orijinal dosya adı
            dosya_yolu: Dosya yolu
            dosya_tipi: Dosya tipi
            dosya_tarihi: Dosya tarihi
            ocr_metni: OCR metni

        Returns:
            Oluşturulan dosya ID'si
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO dosyalar (
                dava_id, dosya_adi, orijinal_adi, dosya_yolu,
                dosya_tipi, dosya_tarihi, ocr_metni
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (dava_id, dosya_adi, orijinal_adi, dosya_yolu,
              dosya_tipi, dosya_tarihi, ocr_metni))

        conn.commit()

        # Dava güncelleme tarihini güncelle
        cursor.execute('''
            UPDATE davalar
            SET guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (dava_id,))

        conn.commit()

        return cursor.lastrowid

    def get_dosyalar_by_dava(self, dava_id: int) -> List[Dict[str, Any]]:
        """
        Davaya ait dosyaları getir

        Args:
            dava_id: Dava ID

        Returns:
            Dosya listesi
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM dosyalar
            WHERE dava_id = ?
            ORDER BY dosya_tarihi DESC, olusturma_tarihi DESC
        ''', (dava_id,))

        return [dict(row) for row in cursor.fetchall()]

    def add_sure(self, dava_id: int, sure_tipi: str, sure_tarihi: str,
                 aciklama: str = None, dosya_id: int = None) -> int:
        """
        Yeni süre ekle

        Args:
            dava_id: Dava ID
            sure_tipi: Süre tipi
            sure_tarihi: Süre tarihi
            aciklama: Açıklama
            dosya_id: İlgili dosya ID

        Returns:
            Oluşturulan süre ID'si
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO sureler (
                dava_id, dosya_id, sure_tipi, sure_tarihi, aciklama
            )
            VALUES (?, ?, ?, ?, ?)
        ''', (dava_id, dosya_id, sure_tipi, sure_tarihi, aciklama))

        conn.commit()
        return cursor.lastrowid

    def get_sureler_by_dava(self, dava_id: int,
                           sadece_aktif: bool = True) -> List[Dict[str, Any]]:
        """
        Davaya ait süreleri getir

        Args:
            dava_id: Dava ID
            sadece_aktif: Sadece tamamlanmamış süreler

        Returns:
            Süre listesi
        """
        conn = self.connect()
        cursor = conn.cursor()

        query = '''
            SELECT * FROM sureler
            WHERE dava_id = ?
        '''

        if sadece_aktif:
            query += ' AND tamamlandi = 0'

        query += ' ORDER BY sure_tarihi ASC'

        cursor.execute(query, (dava_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_yaklasan_sureler(self, gun_sayisi: int = 30) -> List[Dict[str, Any]]:
        """
        Yaklaşan süreleri getir

        Args:
            gun_sayisi: Kaç gün içindeki süreler

        Returns:
            Süre listesi (dava bilgisi ile birlikte)
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                s.*,
                d.klasor_adi,
                d.klasor_yolu
            FROM sureler s
            JOIN davalar d ON s.dava_id = d.id
            WHERE s.tamamlandi = 0
            AND DATE(s.sure_tarihi) BETWEEN DATE('now') AND DATE('now', '+' || ? || ' days')
            ORDER BY s.sure_tarihi ASC
        ''', (gun_sayisi,))

        return [dict(row) for row in cursor.fetchall()]

    def mark_sure_tamamlandi(self, sure_id: int) -> None:
        """
        Süreyi tamamlandı olarak işaretle

        Args:
            sure_id: Süre ID
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE sureler
            SET tamamlandi = 1
            WHERE id = ?
        ''', (sure_id,))

        conn.commit()

    def add_log(self, islem_tipi: str, durum: str,
                dosya_yolu: str = None, detay: str = None) -> int:
        """
        Yeni log ekle

        Args:
            islem_tipi: İşlem tipi
            durum: İşlem durumu
            dosya_yolu: Dosya yolu
            detay: Detay bilgisi

        Returns:
            Oluşturulan log ID'si
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO loglar (islem_tipi, dosya_yolu, durum, detay)
            VALUES (?, ?, ?, ?)
        ''', (islem_tipi, dosya_yolu, durum, detay))

        conn.commit()
        return cursor.lastrowid

    def get_istatistikler(self) -> Dict[str, Any]:
        """
        Sistem istatistiklerini getir

        Returns:
            İstatistik dictionary'si
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Toplam dava sayısı
        cursor.execute('SELECT COUNT(*) as sayi FROM davalar')
        toplam_dava = cursor.fetchone()['sayi']

        # Toplam dosya sayısı
        cursor.execute('SELECT COUNT(*) as sayi FROM dosyalar')
        toplam_dosya = cursor.fetchone()['sayi']

        # Aktif süre sayısı
        cursor.execute('''
            SELECT COUNT(*) as sayi FROM sureler
            WHERE tamamlandi = 0 AND DATE(sure_tarihi) >= DATE('now')
        ''')
        aktif_sure = cursor.fetchone()['sayi']

        # Dosya tipi dağılımı
        cursor.execute('''
            SELECT dosya_tipi, COUNT(*) as sayi
            FROM dosyalar
            GROUP BY dosya_tipi
        ''')
        dosya_tipi_dagilim = {row['dosya_tipi']: row['sayi']
                             for row in cursor.fetchall()}

        return {
            'toplam_dava': toplam_dava,
            'toplam_dosya': toplam_dosya,
            'aktif_sure': aktif_sure,
            'dosya_tipi_dagilim': dosya_tipi_dagilim
        }
