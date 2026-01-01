"""
Dava Yönetim Sistemi - Setup
"""

from setuptools import setup, find_packages
from pathlib import Path

# README dosyasını oku
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

setup(
    name='dava-yonetim-sistemi',
    version='1.0.0',
    description='Akıllı PDF dava dosyası yönetimi, OCR ve otomatik isimlendirme',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Dava Yönetim Sistemi',
    python_requires='>=3.9',
    packages=find_packages(),
    install_requires=[
        'watchdog>=3.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'black>=22.0.0',
        ],
    },
    scripts=[
        'bin/dava-yonetim',
        'bin/dava-kur',
        'bin/dava-config',
        'bin/dava-baslat',
        'bin/dava-durum',
        'bin/dava-analiz',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Legal Industry',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: MacOS :: MacOS X',
    ],
)
