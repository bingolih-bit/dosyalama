"""
Dava Yönetim Sistemi - Dosya Analiz Motoru
"""

import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional


class FileAnalyzer:
    """PDF dosyalarını analiz ederek tip ve tarih bilgisi çıkarır"""

    def __init__(self, file_patterns: Dict[str, List[str]] = None,
                 date_patterns: List[str] = None,
                 deadline_keywords: List[str] = None):
        """
        FileAnalyzer sınıfı başlatıcı

        Args:
            file_patterns: Dosya tipi pattern'leri
            date_patterns: Tarih pattern'leri
            deadline_keywords: Süre anahtar kelimeleri
        """
        # Varsayılan dosya tipi pattern'leri
        self.file_patterns = file_patterns or {
            'durusma': ['DURUŞMA', 'CELSE', 'TUTANAK', 'MAHKEME'],
            'bilirkisi': ['BİLİRKİŞİ', 'RAPOR', 'EKSPERTIZ', 'MÜTALAA'],
            'tebligat': ['TEBLİGAT', 'İHBARNAME', 'İHTAR', 'TEBLIĞ'],
            'karar': ['KARAR', 'HÜKÜM', 'İLAM', 'GEREKÇELİ']
        }

        # Varsayılan tarih pattern'leri
        self.date_patterns = date_patterns or [
            r'\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b',  # DD.MM.YYYY veya DD/MM/YYYY
            r'\b(\d{4})[./](\d{1,2})[./](\d{1,2})\b',  # YYYY.MM.DD veya YYYY/MM/DD
            r'\b(\d{1,2})\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+(\d{4})\b'  # DD Ay YYYY
        ]

        # Süre anahtar kelimeleri
        self.deadline_keywords = deadline_keywords or [
            'sonraki duruşma',
            'duruşma günü',
            'celse',
            'rapor süresi',
            'süre',
            'tarihinde',
            'tarihine kadar',
            'gününe kadar'
        ]

        # Ay isimleri mapping
        self.ay_map = {
            'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4,
            'Mayıs': 5, 'Haziran': 6, 'Temmuz': 7, 'Ağustos': 8,
            'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12
        }

    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        Metni analiz ederek dosya tipi, tarih ve süre bilgilerini çıkarır

        Args:
            text: Analiz edilecek metin

        Returns:
            Analiz sonuçları dictionary'si
        """
        # Metni büyük harfe çevir (pattern matching için)
        text_upper = text.upper()

        # Dosya tipini tespit et
        file_type = self._detect_file_type(text_upper)

        # Tarihleri tespit et
        dates = self._extract_dates(text)

        # En olası belge tarihini bul
        document_date = self._find_document_date(dates, text)

        # Süreleri tespit et
        deadlines = self._extract_deadlines(text)

        return {
            'file_type': file_type,
            'document_date': document_date,
            'all_dates': dates,
            'deadlines': deadlines,
            'has_deadline': len(deadlines) > 0
        }

    def _detect_file_type(self, text: str) -> Optional[str]:
        """
        Dosya tipini tespit et

        Args:
            text: Analiz edilecek metin (büyük harf)

        Returns:
            Dosya tipi veya None
        """
        # Her dosya tipi için skor hesapla
        scores = {}

        for file_type, keywords in self.file_patterns.items():
            score = 0
            for keyword in keywords:
                # Anahtar kelime metinde kaç kez geçiyor
                count = text.count(keyword.upper())
                score += count

            if score > 0:
                scores[file_type] = score

        # En yüksek skora sahip tipi döndür
        if scores:
            return max(scores, key=scores.get)

        return None

    def _extract_dates(self, text: str) -> List[str]:
        """
        Metinden tüm tarihleri çıkar

        Args:
            text: Analiz edilecek metin

        Returns:
            Tarih listesi (YYYY-MM-DD formatında)
        """
        dates = []

        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                try:
                    date_str = self._parse_date_match(match)
                    if date_str and self._is_valid_date(date_str):
                        dates.append(date_str)
                except (ValueError, IndexError):
                    continue

        # Tarihleri benzersiz ve sıralı hale getir
        return sorted(list(set(dates)))

    def _parse_date_match(self, match: re.Match) -> Optional[str]:
        """
        Regex match'inden tarih string'i oluştur

        Args:
            match: Regex match objesi

        Returns:
            YYYY-MM-DD formatında tarih string'i
        """
        groups = match.groups()

        # DD.MM.YYYY formatı
        if len(groups) == 3 and groups[0].isdigit() and groups[1].isdigit():
            if len(groups[2]) == 4:  # Yıl
                day, month, year = groups
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif len(groups[0]) == 4:  # YYYY.MM.DD
                year, month, day = groups
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # DD Ay YYYY formatı
        if len(groups) == 3 and groups[1] in self.ay_map:
            day, month_name, year = groups
            month = self.ay_map[month_name]
            return f"{year}-{str(month).zfill(2)}-{day.zfill(2)}"

        return None

    def _is_valid_date(self, date_str: str) -> bool:
        """
        Tarih string'inin geçerli bir tarih olup olmadığını kontrol et

        Args:
            date_str: YYYY-MM-DD formatında tarih

        Returns:
            Geçerli ise True
        """
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            # Makul bir tarih aralığında mı?
            year = int(date_str.split('-')[0])
            return 1990 <= year <= 2050
        except ValueError:
            return False

    def _find_document_date(self, dates: List[str], text: str) -> Optional[str]:
        """
        Belgenin tarihini bul (genellikle en erken veya en yaygın tarih)

        Args:
            dates: Tespit edilen tarihler
            text: Orijinal metin

        Returns:
            Belge tarihi veya None
        """
        if not dates:
            return None

        # Eğer "tarih" kelimesine yakın bir tarih varsa, onu döndür
        text_lower = text.lower()

        for date in dates:
            # Tarihi farklı formatlarda ara
            date_parts = date.split('-')
            formatted_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"

            # "Tarih:" veya "Tarih :" kelimesinden sonraki 50 karakter içinde bu tarih var mı?
            tarih_idx = text_lower.find('tarih')
            if tarih_idx != -1:
                nearby_text = text[tarih_idx:tarih_idx + 100]
                if formatted_date in nearby_text or date in nearby_text:
                    return date

        # Bulunamazsa, ilk tarihi döndür
        return dates[0] if dates else None

    def _extract_deadlines(self, text: str) -> List[Dict[str, str]]:
        """
        Metinden süreleri çıkar

        Args:
            text: Analiz edilecek metin

        Returns:
            Süre listesi [{'date': 'YYYY-MM-DD', 'context': 'açıklama'}]
        """
        deadlines = []
        text_lower = text.lower()

        # Her anahtar kelime için ara
        for keyword in self.deadline_keywords:
            # Anahtar kelimenin geçtiği yerleri bul
            keyword_positions = []
            start = 0

            while True:
                pos = text_lower.find(keyword.lower(), start)
                if pos == -1:
                    break
                keyword_positions.append(pos)
                start = pos + 1

            # Her pozisyon için yakındaki tarihleri bul
            for pos in keyword_positions:
                # Anahtar kelimeden sonraki 200 karakter
                context = text[pos:pos + 200]

                # Bu context içindeki tarihleri bul
                context_dates = self._extract_dates(context)

                for date in context_dates:
                    # Tarih ve açıklama ekle
                    deadlines.append({
                        'date': date,
                        'context': keyword + ' - ' + context[:100].strip()
                    })

        # Benzersiz tarihleri döndür
        unique_deadlines = []
        seen_dates = set()

        for deadline in deadlines:
            if deadline['date'] not in seen_dates:
                unique_deadlines.append(deadline)
                seen_dates.add(deadline['date'])

        return sorted(unique_deadlines, key=lambda x: x['date'])

    def extract_case_number(self, text: str) -> Optional[str]:
        """
        Dosya numarasını çıkar (opsiyonel)

        Args:
            text: Analiz edilecek metin

        Returns:
            Dosya numarası veya None
        """
        # Dosya numarası pattern'leri (örnek)
        patterns = [
            r'Esas\s+No\s*:\s*(\d{4}/\d+)',
            r'Karar\s+No\s*:\s*(\d{4}/\d+)',
            r'Dosya\s+No\s*:\s*(\d{4}/\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None
