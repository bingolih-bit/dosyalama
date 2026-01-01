"""
Dava Yönetim Sistemi - OCR Motoru
"""

import os
import subprocess
from pathlib import Path
from typing import Optional
import tempfile


class OCREngine:
    """PDF dosyalarından metin çıkarma (Tesseract OCR)"""

    def __init__(self, lang: str = 'tur'):
        """
        OCREngine sınıfı başlatıcı

        Args:
            lang: Tesseract dil kodu (varsayılan: tur - Türkçe)
        """
        self.lang = lang
        self._check_tesseract()

    def _check_tesseract(self) -> None:
        """Tesseract kurulu mu kontrol et"""
        try:
            result = subprocess.run(
                ['tesseract', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            # Tesseract kurulu
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "❌ Tesseract OCR kurulu değil!\n"
                "Kurulum için: brew install tesseract tesseract-lang"
            )

    def pdf_to_text(self, pdf_path: str) -> Optional[str]:
        """
        PDF dosyasından metin çıkar

        Args:
            pdf_path: PDF dosya yolu

        Returns:
            Çıkarılan metin veya None
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF dosyası bulunamadı: {pdf_path}")

        try:
            # PDF'i önce görsele çevir (pdftoppm kullanarak)
            # Eğer pdftoppm yoksa, sadece tesseract'i dene
            text = self._extract_with_tesseract(pdf_path)
            return text.strip() if text else None

        except Exception as e:
            raise RuntimeError(f"OCR hatası: {str(e)}")

    def _extract_with_tesseract(self, pdf_path: str) -> str:
        """
        Tesseract ile metin çıkar

        Args:
            pdf_path: PDF dosya yolu

        Returns:
            Çıkarılan metin
        """
        # Geçici klasör oluştur
        with tempfile.TemporaryDirectory() as temp_dir:
            # PDF'i görsellere çevir (poppler-utils gerekli)
            try:
                subprocess.run(
                    ['pdftoppm', '-png', pdf_path, f'{temp_dir}/page'],
                    capture_output=True,
                    check=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # pdftoppm yoksa, direkt PDF'i tesseract'e ver
                return self._tesseract_from_pdf(pdf_path)

            # Tüm görselleri OCR'dan geçir
            all_text = []
            temp_path = Path(temp_dir)

            for img_file in sorted(temp_path.glob('*.png')):
                text = self._tesseract_from_image(str(img_file))
                if text:
                    all_text.append(text)

            return '\n\n'.join(all_text)

    def _tesseract_from_image(self, image_path: str) -> str:
        """
        Görsel dosyadan Tesseract ile metin çıkar

        Args:
            image_path: Görsel dosya yolu

        Returns:
            Çıkarılan metin
        """
        try:
            result = subprocess.run(
                ['tesseract', image_path, 'stdout', '-l', self.lang],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            return result.stdout

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Tesseract OCR hatası: {e.stderr}")

    def _tesseract_from_pdf(self, pdf_path: str) -> str:
        """
        PDF dosyadan direkt Tesseract ile metin çıkar

        Args:
            pdf_path: PDF dosya yolu

        Returns:
            Çıkarılan metin
        """
        try:
            result = subprocess.run(
                ['tesseract', pdf_path, 'stdout', '-l', self.lang],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            return result.stdout

        except subprocess.CalledProcessError as e:
            # Tesseract direkt PDF okuyamıyorsa, boş string döndür
            return ""

    def extract_text_from_page(self, pdf_path: str, page_number: int = 1) -> Optional[str]:
        """
        PDF'in belirli bir sayfasından metin çıkar

        Args:
            pdf_path: PDF dosya yolu
            page_number: Sayfa numarası (1'den başlar)

        Returns:
            Çıkarılan metin veya None
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF dosyası bulunamadı: {pdf_path}")

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Sadece belirtilen sayfayı çıkar
                subprocess.run(
                    ['pdftoppm', '-png', '-f', str(page_number),
                     '-l', str(page_number), pdf_path, f'{temp_dir}/page'],
                    capture_output=True,
                    check=True
                )

                # OCR uygula
                temp_path = Path(temp_dir)
                png_files = list(temp_path.glob('*.png'))

                if png_files:
                    text = self._tesseract_from_image(str(png_files[0]))
                    return text.strip() if text else None

                return None

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Hata durumunda None döndür
            return None
