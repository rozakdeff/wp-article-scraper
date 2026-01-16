import re
import logging
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from typing import Union

def slugify_domain(url: str) -> str:
    """
    Mengubah domain menjadi format yang aman untuk nama folder.
    Contoh: https://blog.detik.com/makan -> blog_detik_com
    """
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path  # fallback jika URL tidak diawali http
    
    # Hanya ambil karakter alphanumeric dan ganti titik/simbol lain dengan underscore
    clean_domain = re.sub(r'[^\w\s-]', '_', domain).strip().lower()
    return clean_domain

def create_output_dir(base_url: str, base_dir: Union[str, Path] = "outputs") -> Path:
    """
    Membuat direktori output berdasarkan domain dan timestamp.
    Menjamin safety pada berbagai sistem operasi (Windows/Linux/Mac).
    """
    try:
        domain_slug = slugify_domain(base_url)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Gunakan Path object untuk penggabungan yang aman
        root_dir = Path(base_dir)
        folder_name = f"{domain_slug}_{timestamp}"
        output_path = root_dir / folder_name
        
        # parents=True: buat folder 'outputs' jika belum ada
        # exist_ok=True: tidak error jika folder sudah ada (aman untuk concurrency)
        output_path.mkdir(parents=True, exist_ok=True)
        
        return output_path
        
    except Exception as e:
        logging.error(f"Failed to create directory: {e}")
        # Fallback ke folder 'outputs' standar jika gagal
        fallback = Path("outputs") / "default_session"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback