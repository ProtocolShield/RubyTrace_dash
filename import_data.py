#!/usr/bin/env python3
"""
Script to import raw data from data.json into the database
"""

import json
import os
from datetime import datetime
from api import app
from models import db, DataSource, RawData

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"Data file {DATA_FILE} not found.")
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def get_or_create_source(source_name):
    source = DataSource.query.filter_by(name=source_name).first()
    if not source:
        source = DataSource(
            name=source_name,
            url="",
            source_type="surface",
            category="news",
            risk_level="low",
            enabled=True,
            scrape_interval=60,
            config_json="{}"
        )
        db.session.add(source)
        db.session.commit()
        print(f"Created new DataSource: {source_name}")
    return source

def import_data():
    data = load_data()
    if not data:
        print("No data to import.")
        return

    with app.app_context():
        # Initialize the database with the app
        db.init_app(app)

        imported_count = 0
        for item in data:
            source_name = item.get("source", "Unknown")
            source = get_or_create_source(source_name)

            # Check for duplicate by URL and title
            existing = RawData.query.filter_by(url=item.get("url"), title=item.get("title")).first()
            if existing:
                continue

            metadata = {
                "keywords": item.get("keywords", []),
                "sentiment": item.get("sentiment", {})
            }

            created_at = None
            timestamp_str = item.get("timestamp")
            if timestamp_str:
                try:
                    created_at = datetime.fromisoformat(timestamp_str)
                except Exception:
                    created_at = datetime.utcnow()

            raw_data = RawData(
                source_id=source.id,
                url=item.get("url"),
                title=item.get("title"),
                content=item.get("summary"),
                metadata_json=json.dumps(metadata),
                created_at=created_at or datetime.utcnow()
            )
            db.session.add(raw_data)
            imported_count += 1

        db.session.commit()
        print(f"Imported {imported_count} new RawData entries.")

if __name__ == "__main__":
    import_data()
