import logging
import requests
from datetime import datetime
from models import CVEItem

def scrape_cve_data():
    """
    Scrape CVE data from NVD and other sources with detailed information.
    """
    cve_sources = [
        {
            "name": "NVD",
            "url": "https://services.nvd.nist.gov/rest/json/cves/2.0"
        },
        {
            "name": "CVE Details",
            "url": "https://cvedetails.com/json-feed.php"
        }
    ]
    
    for source in cve_sources:
        try:
            response = requests.get(source["url"])
            response.raise_for_status()
            cves = response.json()
            
            for cve in cves:
                cve_item = CVEItem(
                    cve_id=cve.get('id'),
                    title=cve.get('title'),
                    description=cve.get('description'),
                    severity=cve.get('severity'),
                    cvss=cve.get('cvss'),
                    cvss_vector=cve.get('cvss_vector'),
                    affected_products=cve.get('affected_products'),
                    affected_vendors=cve.get('affected_vendors'),
                    tags=cve.get('tags'),
                    source_url=source["url"],
                    references=cve.get('references'),
                    exploit_available=cve.get('exploit_available', False),
                    patch_available=cve.get('patch_available', False),
                    published_at=datetime.fromisoformat(cve.get('published_at')) if cve.get('published_at') else None,
                    last_modified_at=datetime.fromisoformat(cve.get('last_modified_at')) if cve.get('last_modified_at') else None,
                    created_at=datetime.utcnow()
                )
                
                # Save to the database
                # Assuming a session is available for committing
                db.session.add(cve_item)
            db.session.commit()
            logging.info(f"Successfully scraped and stored CVEs from {source['name']}")
        
        except Exception as e:
            logging.error(f"Error scraping {source['name']}: {e}")

if __name__ == "__main__":
    scrape_cve_data()
