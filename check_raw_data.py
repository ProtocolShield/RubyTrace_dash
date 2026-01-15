from api import app
from models import db, RawData, DataSource

# Initialize the database with the app
db.init_app(app)

with app.app_context():
    print("RawData check:")
    print(f"RawData count: {RawData.query.count()}")

    data = RawData.query.limit(5).all()
    print("Sample RawData entries:")
    for d in data:
        source = DataSource.query.get(d.source_id) if d.source_id else None
        print(f"ID: {d.id}")
        print(f"  Title: {d.title[:50]}...")
        print(f"  URL: {d.url}")
        print(f"  Source: {source.name if source else 'Unknown'}")
        print(f"  Content length: {len(d.content)}")
        print(f"  Created: {d.created_at}")
        print()
