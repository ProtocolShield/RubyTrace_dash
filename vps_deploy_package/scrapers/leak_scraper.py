import logging
import requests
from datetime import datetime
from models import LeakItem

def scrape_leak_data():
    """
    Scrape leak data from various sources and store it in the database.
    """
    leak_sources = [
        {
            "name": "Pastebin",
            "url": "https://pastebin.com/archive"
        },
        {
            "name": "Dark Web Forums",
            "url": "http://example-dark-web-forum.com/leaks"  # Placeholder URL
        }
    ]
    
    for source in leak_sources:
        try:
            response = requests.get(source["url"])
            response.raise_for_status()
            leaks = response.json()
            
            for leak in leaks:
                leak_item = LeakItem(
                    source=source["name"],
                    data_content=leak.get('data_content'),
                    verification_status=leak.get('verification_status', 'unverified'),
                    associated_breach_id=leak.get('associated_breach_id'),
                    created_at=datetime.utcnow()
                )
                
                # Save to the database
                # Assuming a session is available for committing
                db.session.add(leak_item)
            db.session.commit()
            logging.info(f"Successfully scraped and stored leaks from {source['name']}")
        
        except Exception as e:
            logging.error(f"Error scraping {source['name']}: {e}")

if __name__ == "__main__":
    scrape_leak_data()
