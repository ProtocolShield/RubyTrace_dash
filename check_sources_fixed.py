#!/usr/bin/env python3
"""
Check data sources in database
"""

from api import app
from models import db, DataSource

# Initialize the database
db.init_app(app)

with app.app_context():
    sources = DataSource.query.all()
    print(f"Found {len(sources)} data sources:")
    for source in sources:
        print(f"- {source.name} ({source.source_type}, {source.category}, {source.risk_level} risk)")
