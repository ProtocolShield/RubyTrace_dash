#!/usr/bin/env python3
"""
Direct data storage test - bypass bot system to test database storage
"""

import asyncio
import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, DataSource, RawData, SearchIndex, Bot
from api import app

def test_direct_storage():
    """Test direct data storage without bot system"""
    
    with app.app_context():
        # Initialize database
        db.init_app(app)
        db.create_all()
        
        print("🧪 Testing Direct Data Storage")
        print("=" * 40)
        
        # 1. Get a data source
        source = DataSource.query.filter_by(source_type='surface_web').first()
        if not source:
            print("❌ No surface_web sources found")
            return
        
        print(f"📰 Testing with source: {source.name} ({source.url})")
        
        # 2. Fetch content directly
        try:
            print("🌐 Fetching content...")
            response = requests.get(source.url, timeout=10)
            response.raise_for_status()
            
            content = response.text
            print(f"✅ Content fetched: {len(content)} characters")
            
            # 3. Parse content
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.find('title')
            title_text = title.get_text() if title else "No title"
            
            # Extract main content
            for script in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
                script.decompose()
            
            main_content = soup.get_text(separator='\n', strip=True)
            print(f"✅ Content extracted: {len(main_content)} characters")
            print(f"✅ Title: {title_text[:100]}...")
            
            # 4. Create raw data record directly
            print("💾 Storing data directly...")
            
            raw_data = RawData(
                source_id=source.id,
                bot_id=None,  # No bot for direct test
                url=source.url,
                title=title_text,
                content=main_content,
                raw_html=content,
                content_type='text/html',
                metadata_json='{}',
                risk_score=0.5
            )
            
            db.session.add(raw_data)
            db.session.commit()
            
            print(f"✅ Data stored successfully! ID: {raw_data.id}")
            
            # 5. Create search index
            search_index = SearchIndex(
                raw_data_id=raw_data.id,
                search_text=f"{title_text} {main_content}",
                keywords='test,debug',
                tags='test',
                risk_keywords=''
            )
            
            db.session.add(search_index)
            db.session.commit()
            
            print("✅ Search index created!")
            
            # 6. Verify storage
            stored_count = RawData.query.count()
            print(f"✅ Total raw data in database: {stored_count}")
            
            if stored_count > 0:
                latest = RawData.query.order_by(RawData.created_at.desc()).first()
                print(f"✅ Latest record: {latest.title}")
                print(f"✅ Content length: {len(latest.content)}")
                print("🎉 Direct storage test SUCCESSFUL!")
            else:
                print("❌ No data found in database")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_direct_storage()
