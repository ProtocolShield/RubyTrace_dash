import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import app
from scrapers.cve_scraper import scrape_cve_data

if __name__ == "__main__":
    with app.app_context():
        scrape_cve_data()
