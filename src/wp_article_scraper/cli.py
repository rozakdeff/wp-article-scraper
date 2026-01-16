import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd

# Import internal modules
# Pastikan menggunakan relative import (.) jika dijalankan sebagai package
from .scraper import scrape_category
from .utils import create_output_dir

# --- Constants ---
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "Connection": "keep-alive",
}

def setup_logging(verbose: bool = False) -> None:
    """Konfigurasi logging global."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout) # Print ke stdout standard
        ]
    )

def parse_arguments() -> argparse.Namespace:
    """Mengatur argumen CLI."""
    parser = argparse.ArgumentParser(
        description="WordPress Article Scraper: Extract articles from category pages.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "urls", 
        nargs="+", 
        help="List of Category URLs to scrape"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("outputs"),
        help="Root directory for saving results"
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=1.0, 
        help="Delay between requests (seconds)"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=15, 
        help="Request timeout (seconds)"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable debug logging"
    )

    return parser.parse_args()

def save_data(articles: List[Dict], output_dir: Path) -> None:
    """Menyimpan data ke CSV dengan dedup."""
    if not articles:
        logging.warning("⚠️  No articles collected to save.")
        return

    try:
        df = pd.DataFrame(articles)
        
        # Data Cleaning dasar sebelum simpan
        if "url" in df.columns:
            initial_len = len(df)
            df.drop_duplicates(subset=["url"], keep="first", inplace=True)
            duplicates = initial_len - len(df)
            if duplicates > 0:
                logging.info(f"Removed {duplicates} duplicate articles.")
        
        output_file = output_dir / "articles.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig') # utf-8-sig untuk support Excel
        
        logging.info(f"✅ Success! Saved {len(df)} unique articles to:")
        logging.info(f"   -> {output_file.absolute()}")
        
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")
        raise

def main() -> int:
    args = parse_arguments()
    setup_logging(args.verbose)

    logging.info("🚀 WP Article Scraper initialized")
    
    # Validasi awal output dir
    try:
        # Kita gunakan URL pertama untuk penamaan folder (sesuai logic utils Anda)
        # Note: Pastikan create_output_dir mengembalikan Path object
        session_output_dir = create_output_dir(str(args.urls[0]), args.output_dir)
        logging.info(f"📂 Output directory set to: {session_output_dir}")
    except Exception as e:
        logging.critical(f"Failed to create output directory: {e}")
        return 1

    all_articles: List[Dict] = []
    has_error = False

    try:
        for url in args.urls:
            logging.info(f"🔍 Scraping category target: {url}")
            try:
                articles = scrape_category(
                    url=str(url),
                    headers=DEFAULT_HEADERS,
                    delay=args.delay,
                    timeout=args.timeout
                )
                
                count = len(articles)
                logging.info(f"   Fetched {count} articles from {url}")
                all_articles.extend(articles)
                
            except Exception as e:
                logging.error(f"❌ Error scraping {url}: {e}")
                has_error = True
                # Kita continue agar URL selanjutnya tetap diproses meski satu gagal
                continue

        save_data(all_articles, session_output_dir)

    except KeyboardInterrupt:
        logging.warning("\n⛔ Process interrupted by user (Ctrl+C). Exiting...")
        return 130 # Standard exit code for SIGINT
    except Exception as e:
        logging.critical(f"🔥 Unexpected fatal error: {e}", exc_info=True)
        return 1

    logging.info("🏁 Scraper finished execution.")
    return 1 if has_error and not all_articles else 0

if __name__ == "__main__":
    sys.exit(main())