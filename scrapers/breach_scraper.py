import logging
import requests
from datetime import datetime
from api import app
from models import BreachItem, ApiKey, db
from database import with_retry

def scrape_breach_data():
    """
    Scrape breach data from various sources and store it in the database.
    """
    with app.app_context():
        @with_retry
        def get_hibp_key():
            key_record = ApiKey.query.filter_by(service='haveibeenpwned').first()
            return key_record.key if key_record else None
        
        hibp_api_key = get_hibp_key()
        
        if not hibp_api_key:
            logging.error("HIBP API key not configured in database (service: 'haveibeenpwned'). Skipping breach scraping.")
            return

    # Only scrape from HaveIBeenPwned for now (DeHashed requires paid subscription and different API)
    breach_sources = [
        {
            "name": "HaveIBeenPwned",
            "url": "https://haveibeenpwned.com/api/v3/breaches"
        }
    ]
    
    for source in breach_sources:
        try:
            headers = {}
            if source["name"] == "HaveIBeenPwned":
                headers = {'hibp-api-key': hibp_api_key}
            
            response = requests.get(source["url"], headers=headers)
            response.raise_for_status()
            breaches = response.json()
            
            with app.app_context():
                for breach in breaches:
                    # Map HIBP fields to model
                    data_classes = ', '.join(breach.get('DataClasses', []))
                    breach_date = datetime.fromisoformat(breach['BreachDate'].replace('Z', '+00:00')) if 'BreachDate' in breach else None
                    
                    breach_item = BreachItem(
                        name=breach.get('Name'),
                        description=breach.get('Description'),
                        affected_organizations=breach.get('Domain'),
                        data_types_exposed=data_classes,
                        records_affected=breach.get('PwnCount'),
                        discovery_date=breach_date,
                        disclosure_date=None,  # HIBP doesn't have separate disclosure date
                        source_url=f"https://haveibeenpwned.com/{breach.get('Domain')}/{breach.get('Name')}",
                        created_at=datetime.utcnow()
                    )
                    
                    # Check if breach already exists to avoid duplicates
                    existing = BreachItem.query.filter_by(name=breach.get('Name')).first()
                    if not existing:
                        db.session.add(breach_item)
                
                db.session.commit()
                logging.info(f"Successfully scraped and stored {len(breaches)} breaches from {source['name']}")
        
        except Exception as e:
            logging.error(f"Error scraping {source['name']}: {e}")

if __name__ == "__main__":
    scrape_breach_data()
