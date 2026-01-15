#!/usr/bin/env python3
"""
Debug script to test data collection step by step
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bots.surface_web_bot import SurfaceWebBot
from models import db, DataSource, RawData
from api import app

async def debug_collection():
    """Debug the data collection process step by step"""
    
    with app.app_context():
        # Initialize database
        db.init_app(app)
        db.create_all()
        
        print("🔍 Debugging Data Collection Process")
        print("=" * 50)
        
        # 1. Check data sources
        print("\n1. Checking Data Sources:")
        sources = DataSource.query.filter_by(source_type='surface_web', enabled=True).all()
        print(f"   Found {len(sources)} enabled surface_web sources:")
        for source in sources:
            print(f"   - {source.name}: {source.url}")
        
        if not sources:
            print("   ❌ No sources found!")
            return
        
        # 2. Initialize bot
        print("\n2. Initializing Surface Web Bot:")
        bot = SurfaceWebBot()
        print(f"   Bot initialized: {bot.bot_name}")
        print(f"   Config: {bot.config}")
        
        # 3. Setup session
        print("\n3. Setting up HTTP session:")
        await bot._setup_session()
        print(f"   Session created: {bot.session is not None}")
        
        # 4. Test with first source
        print("\n4. Testing with first source:")
        source = sources[0]
        print(f"   Testing source: {source.name} ({source.url})")
        
        try:
            # Test basic request
            print("   Making test request...")
            response = await bot._make_request(source.url)
            if response:
                print(f"   ✅ Response status: {response.status}")
                content = await response.text()
                print(f"   ✅ Content length: {len(content)} characters")
                
                # Test content extraction
                print("   Extracting content...")
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                title = soup.find('title')
                title_text = title.get_text() if title else "No title"
                print(f"   ✅ Title: {title_text[:100]}...")
                
                main_content = bot._extract_main_content(soup)
                print(f"   ✅ Main content length: {len(main_content)} characters")
                print(f"   ✅ Content preview: {main_content[:200]}...")
                
                # Test if content is relevant
                is_relevant = bot._is_content_relevant(main_content, title_text)
                print(f"   ✅ Content relevant: {is_relevant}")
                
                if is_relevant and len(main_content) > 100:
                    print("   ✅ Content looks good for collection!")
                else:
                    print("   ❌ Content not suitable for collection")
                    
            else:
                print("   ❌ Failed to get response")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 5. Test full collection cycle
        print("\n5. Testing full collection cycle:")
        try:
            await bot.run_collection_cycle(sources)
            print("   ✅ Collection cycle completed")
            
            # Check if data was collected
            raw_data_count = RawData.query.count()
            print(f"   Raw data in database: {raw_data_count}")
            
            if raw_data_count > 0:
                print("   ✅ Data collection successful!")
                latest_data = RawData.query.order_by(RawData.created_at.desc()).first()
                print(f"   Latest item: {latest_data.title}")
                print(f"   Content length: {len(latest_data.content)}")
            else:
                print("   ❌ No data collected")
                
        except Exception as e:
            print(f"   ❌ Collection cycle error: {e}")
        
        # 6. Cleanup
        print("\n6. Cleanup:")
        await bot.cleanup()
        print("   ✅ Bot cleaned up")

if __name__ == "__main__":
    asyncio.run(debug_collection())
