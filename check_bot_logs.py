#!/usr/bin/env python3
"""
Check bot logs in database
"""

from api import app
from models import db, BotLog

# Initialize the database
db.init_app(app)

with app.app_context():
    logs = BotLog.query.order_by(BotLog.timestamp.desc()).limit(10).all()
    print(f"Bot logs count: {len(logs)}")
    for log in logs:
        print(f"{log.timestamp}: Bot {log.bot_id} - {log.status} - {log.message}")
