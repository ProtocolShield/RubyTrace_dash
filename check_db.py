from api import app
from models import db, BreachItem, LeakItem, CVEItem

# Initialize the database with the app
db.init_app(app)

with app.app_context():
    print("Database check:")
    print(f"Breach records: {BreachItem.query.count()}")
    print(f"Leak records: {LeakItem.query.count()}")
    print(f"CVE records: {CVEItem.query.count()}")

    # List all tables
    print("\nDatabase tables:")
    inspector = db.inspect(db.engine)
    for table_name in inspector.get_table_names():
        print(f"  - {table_name}")
