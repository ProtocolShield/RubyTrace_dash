#!/usr/bin/env python3
"""
Debug script to test bot collection process
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, DataSource
from bots.surface_web_bot import SurfaceWebBot

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.getcwd(), 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

async def debug_collection():
    """Debug the collection process step by step"""
    with app.app_context():
        db.create_all()
        
        print("🔍 Debugging Bot Collection Process")
        print("=" * 50)
        
        # Check all sources
        all_sources = DataSource.query.all()
        print(f"Total sources in database: {len(all_sources)}")
        
        print("\nAll sources:")
        for source in all_sources:
            print(f"  - {source.name}: {source.url} (type: {source.source_type}, enabled: {source.enabled})")
        
        # Get surface web sources
        surface_sources = DataSource.query.filter(
            DataSource.source_type.in_(['surface', 'surface_web']),
            DataSource.enabled == True
        ).all()
        
        print(f"\nSurface web sources: {len(surface_sources)}")
        for source in surface_sources:
            print(f"  - {source.name}: {source.url}")
        
        # Get enabled sources regardless of type
        enabled_sources = DataSource.query.filter(DataSource.enabled == True).all()
        print(f"\nEnabled sources: {len(enabled_sources)}")
        for source in enabled_sources:
            print(f"  - {source.name}: {source.url} (type: {source.source_type})")
        
        if not enabled_sources:
            print("❌ No enabled sources found!")
            return
        
        # Test with first enabled source
        test_source = enabled_sources[0]
        print(f"\n🧪 Testing with source: {test_source.name}")
        print(f"URL: {test_source.url}")
        print(f"Type: {test_source.source_type}")
        
        # Create bot instance
        bot = SurfaceWebBot()
        print(f"Bot created: {bot.bot_name}")
        
        # Test session setup
        print("\n🔧 Testing session setup...")
        await bot._setup_session()
        print(f"Session created: {bot.session is not None}")
        
        # Test making a request
        print(f"\n🌐 Testing request to {test_source.url}...")
        try:
            response = await bot._make_request(test_source.url)
            if response:
                print(f"✅ Request successful: Status {response.status}")
                content = await response.text()
                print(f"Content length: {len(content)} characters")
                
                # Test content extraction
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                # Test title extraction
                title = soup.find('title')
                title_text = title.get_text().strip() if title else 'No title'
                print(f"Title: {title_text}")
                
                # Test main content extraction
                main_content = bot._extract_main_content(soup)
                print(f"Main content length: {len(main_content)} characters")
                print(f"Content preview: {main_content[:200]}...")
                
                # Test relevance check
                is_relevant = bot._is_content_relevant(main_content, title_text)
                print(f"Content relevant: {is_relevant}")
                
                # Test link extraction
                links = await bot._extract_links(test_source.url)
                print(f"Found {len(links)} links")
                if links:
                    print(f"First few links: {links[:3]}")
                
            else:
                print("❌ Request failed: No response")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        # Test full collection
        print(f"\n🔄 Testing full collection from {test_source.name}...")
        try:
            collected = await bot.collect_data(test_source)
            print(f"Collected {len(collected)} items")
            
            if collected:
                print("First collected item:")
                item = collected[0]
                print(f"  Title: {item.get('title', 'No title')}")
                print(f"  URL: {item.get('url', 'No URL')}")
                print(f"  Content length: {len(item.get('content', ''))}")
                print(f"  Risk score: {item.get('risk_score', 0)}")
            else:
                print("❌ No data collected!")
                
        except Exception as e:
            print(f"❌ Collection failed: {e}")
        
        # Clean up
        if bot.session and not bot.session.closed:
            await bot.session.close()
        print("\n✅ Debug completed")

if __name__ == "__main__":
    asyncio.run(debug_collection())
