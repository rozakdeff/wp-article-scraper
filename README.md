# 🚀 WordPress Article Scraper

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**WP Article Scraper** adalah alat CLI (Command Line Interface) berbasis Python yang dirancang untuk mengekstraksi daftar artikel dari halaman kategori WordPress secara efisien dan aman.

## ✨ Fitur Utama

* **Smart Pagination**: Mendeteksi otomatis halaman selanjutnya dan berhenti jika menemukan konten duplikat atau redirect loop.
* **Connection Resilience**: Menggunakan `requests.Session` untuk efisiensi koneksi dan mekanisme *Exponential Backoff* (retry otomatis jika koneksi gagal).
* **Robust Filtering**: Menyaring link yang tidak relevan secara cerdas (mengabaikan tag, category, author, dan system files).
* **Professional Logging**: Output terminal yang informatif dan terstruktur untuk memantau proses scraping secara real-time.
* **Auto-Organized Outputs**: Hasil disimpan dalam CSV dengan folder yang dinamai otomatis berdasarkan domain dan timestamp.

## 🛠️ Instalasi

1.  **Clone repository:**
    ```bash
    git clone [https://github.com/username/wp-article-scraper.git](https://github.com/username/wp-article-scraper.git)
    cd wp-article-scraper
    ```

2.  **Buat virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # atau
    venv\Scripts\activate     # Windows
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Penggunaan

Jalankan script melalui modul Python dengan menyertakan satu atau lebih URL kategori WordPress:

```bash
python -m src.wp_article_scraper.cli <URL_KATEGORI> [OPTIONS]
