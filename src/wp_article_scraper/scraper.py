import logging
import time
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# --- Constants ---
# Kata kunci untuk mengabaikan link yang bukan artikel
EXCLUDED_PATH_KEYWORDS = [
    "/category/", "/tag/", "/page/", "/author/", 
    "/wp-content/", "/wp-json/", "/wp-includes/", 
    "/feed/", "/comments/", "#"
]

def create_session(headers: Dict[str, str]) -> requests.Session:
    """
    Membuat requests Session dengan headers default.
    Menggunakan Session meningkatkan performa karena connection pooling.
    """
    session = requests.Session()
    session.headers.update(headers)
    return session

def fetch_page(
    session: requests.Session, 
    url: str, 
    timeout: int, 
    retries: int = 3
) -> Optional[str]:
    """
    Mengambil HTML dari URL dengan mekanisme Retry otomatis.
    """
    attempt = 0
    while attempt < retries:
        try:
            response = session.get(url, timeout=timeout)
            
            # Handle specific status codes
            if response.status_code == 404:
                logging.warning(f"⚠️  Page not found (404): {url}")
                return None
            
            response.raise_for_status()
            return response.text
            
        except (requests.Timeout, requests.ConnectionError) as e:
            attempt += 1
            wait_time = 2 ** attempt # Exponential backoff: 2s, 4s, 8s
            logging.warning(f"⚠️  Connection error on {url}: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            
        except requests.RequestException as e:
            logging.error(f"❌ Critical error fetching {url}: {e}")
            return None
            
    logging.error(f"❌ Failed to fetch {url} after {retries} attempts.")
    return None

def is_valid_article_url(parsed_url, base_domain: str) -> bool:
    """
    Filter logika untuk menentukan apakah URL adalah kandidat artikel.
    """
    # 1. Harus domain yang sama
    if parsed_url.netloc != base_domain:
        return False
    
    # 2. Path tidak boleh kosong atau root saja
    path = parsed_url.path
    if not path or path == "/":
        return False
        
    # 3. Cek keyword terlarang
    if any(keyword in path for keyword in EXCLUDED_PATH_KEYWORDS):
        return False
        
    return True

def parse_articles(html: str, base_url: str) -> List[Dict[str, str]]:
    """
    Mengekstrak link artikel dari HTML.
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []
    base_domain = urlparse(base_url).netloc
    
    # Mencari semua tag <a>
    # Optimasi: Kita bisa membatasi pencarian ke elemen main/article jika strukturnya diketahui,
    # tapi untuk generic scraper, kita cari global namun filter dengan ketat.
    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a.get("href")

        if not title or not href:
            continue

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        if is_valid_article_url(parsed, base_domain):
            results.append({
                "title": title,
                "url": full_url
            })

    return results

def scrape_category(
    url: str, 
    headers: Dict[str, str], 
    delay: float = 1.0, 
    timeout: int = 10
) -> List[Dict[str, str]]:
    """
    Fungsi utama untuk scrape seluruh halaman kategori (pagination).
    """
    session = create_session(headers)
    
    # Normalisasi URL agar selalu berakhiran slash
    base_url = url.rstrip("/") + "/"
    
    page = 1
    articles: List[Dict] = []
    seen_urls: Set[str] = set()
    
    logging.info(f"🚀 Starting scraper for: {base_url}")

    while True:
        # Konstruksi URL Pagination WordPress Standard
        target_url = base_url if page == 1 else f"{base_url}page/{page}/"
        
        logging.info(f"📄 Scraping page {page}...")
        
        html = fetch_page(session, target_url, timeout)
        
        if not html:
            logging.info("⏹️  Stopping: Cannot fetch page (End of content or Error).")
            break

        page_articles = parse_articles(html, base_url)
        
        if not page_articles:
            logging.info("⏹️  Stopping: No articles found on this page.")
            break

        # Cek Duplikasi Halaman (Redirect Loop Check)
        # Kadang WP redirect page 999 ke page 1, ini cara mendeteksinya.
        current_urls = {a["url"] for a in page_articles}
        
        # Jika semua URL di halaman ini sudah pernah kita ambil sebelumnya,
        # berarti kita berputar di halaman yang sama.
        if current_urls.issubset(seen_urls):
            logging.info("🔄 Pagination loop detected (Duplicate content). Stopping.")
            break
        
        # Simpan hasil
        new_articles_count = 0
        for article in page_articles:
            if article["url"] not in seen_urls:
                articles.append(article)
                seen_urls.add(article["url"])
                new_articles_count += 1
                
        logging.info(f"   found {new_articles_count} new articles.")

        page += 1
        time.sleep(delay)

    # Return list of dicts
    return articles