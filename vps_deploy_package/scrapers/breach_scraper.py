import logging
import requests
from datetime import datetime
from models import BreachItem

def scrape_breach_data():
    """
    Scrape breach data from various sources and store it in the database.
    """
    breach_sources = [
        {
            "name": "HaveIBeenPwned",
            "url": "https://haveibeenpwned.com/api/v3/breaches"
        },
        {
            "name": "DeHashed",
            "url": "https://dehashed.com/api/breach"
        }
    ]
    
    for source in breach_sources:
        try:
            response = requests.get(source["url"])
            response.raise_for_status()
            breaches = response.json()
            
            for breach in breaches:
                breach_item = BreachItem(
                    name=breach.get('name'),
                    description=breach.get('description'),
                    affected_organizations=breach.get('affected_organizations'),
                    data_types_exposed=breach.get('data_types_exposed'),
                    records_affected=breach.get('records_affected'),
                    discovery_date=datetime.fromisoformat(breach.get('discovery_date')) if breach.get('discovery_date') else None,
                    disclosure_date=datetime.fromisoformat(breach.get('disclosure_date')) if breach.get('disclosure_date') else None,
                    source_url=source["url"],
                    created_at=datetime.utcnow()
                )
                
                # Save to the database
                # Assuming a session is available for committing
                db.session.add(breach_item)
            db.session.commit()
            logging.info(f"Successfully scraped and stored breaches from {source['name']}")
        
        except Exception as e:
            logging.error(f"Error scraping {source['name']}: {e}")

if __name__ == "__main__":
    scrape_breach_data()
