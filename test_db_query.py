import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import app
from models import db, BreachItem, CVEItem

if __name__ == "__main__":
    with app.app_context():
        print("DB Connection Test:")
        print(f"Breaches count: {BreachItem.query.count()}")
        print(f"CVEs count: {CVEItem.query.count()}")
        from models import Source, DataSource
        print(f"Sources count: {Source.query.count()}")
        print(f"DataSources count: {DataSource.query.count()}")
        print("Query successful.")
