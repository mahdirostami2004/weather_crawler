"""
Iran Weather Intelligence — main entry point.

Usage:
    python main.py

Steps:
    1. Initialise the SQLite database.
    2. Run the Scrapy spider (fetches data from wttr.in).
    3. Run the analysis module (produces 5 PNG charts).
"""

import os
import sys

# Make sure sibling packages are importable when run as `python main.py`
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from database.db_manager import init_db
from analysis.analyze import run_analysis


def run_spider():
    """Configure and run the Scrapy spider inside the same Python process."""
    # Point Scrapy to our settings module
    os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "crawler.settings")
    settings = get_project_settings()

    process = CrawlerProcess(settings)
    process.crawl("wttr_spider")
    process.start()   # blocks until the spider finishes


def main():
    print("=" * 60)
    print("  Iran Weather Intelligence")
    print("=" * 60)

    print("\n[Step 1/3] Initialising database...")
    init_db()

    print("\n[Step 2/3] Starting Scrapy spider...")
    run_spider()

    print("\n[Step 3/3] Running data analysis & chart generation...")
    run_analysis()

    print("\n✅  Pipeline complete. Check the analysis/ folder for charts.")


if __name__ == "__main__":
    main()
