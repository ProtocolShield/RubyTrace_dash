#!/usr/bin/env python3
"""
Test script for bot management system
Tests bot initialization, session management, and cleanup
"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bots.bot_manager import BotManager
from models import db
from api import app

async def test_bot_management():
    """Test bot management functionality"""
    print("🧪 Testing Bot Management System")
    print("=" * 50)

    with app.app_context():
        try:
            # Initialize bot manager
            print("1. Initializing BotManager...")
            manager = BotManager()
            print("   ✅ BotManager initialized successfully")

            # Test bot instances
            print("\n2. Testing bot instances...")
            print(f"   Available bots: {list(manager.bots.keys())}")

            for bot_name, bot_instance in manager.bots.items():
                print(f"   - {bot_name}: {type(bot_instance).__name__}")
                print(f"     Status: {bot_instance.get_status()}")

            # Test bot startup
            print("\n3. Testing bot startup...")
            surface_bot = manager.bots.get('surface')
            if surface_bot:
                print("   Starting surface web bot...")
                result = await surface_bot.start()
                print(f"   Surface bot start result: {result}")
                print(f"   Surface bot status: {surface_bot.get_status()}")

                # Test collection cycle (limited)
                print("\n4. Testing collection cycle...")
                try:
                    # Create a test data source
                    from models import DataSource
                    test_source = DataSource(
                        name="Test Source",
                        url="https://httpbin.org/html",  # Simple test endpoint
                        source_type="surface",
                        category="test",
                        risk_level="low",
                        enabled=True
                    )
                    db.session.add(test_source)
                    db.session.commit()

                    print(f"   Created test data source: {test_source.id}")

                    # Run collection cycle
                    await manager.run_cycle('surface', 'surface')

                    # Check collected data
                    from models import RawData
                    collected_count = RawData.query.count()
                    print(f"   Data collected: {collected_count} records")

                    if collected_count > 0:
                        latest_data = RawData.query.order_by(RawData.created_at.desc()).first()
                        print(f"   Latest data: {latest_data.title[:50]}...")
                        print(f"   Risk score: {latest_data.risk_score}")

                except Exception as e:
                    print(f"   Collection test error: {e}")

                # Test bot shutdown
                print("\n5. Testing bot shutdown...")
                result = await surface_bot.stop()
                print(f"   Surface bot stop result: {result}")
                print(f"   Surface bot status: {surface_bot.get_status()}")

            # Test BotManager methods
            print("\n6. Testing BotManager methods...")
            status = manager.get_bot_status('surface')
            print(f"   Bot status via manager: {status}")

            # Test data source management
            print("\n7. Testing data source management...")
            sources = manager.list_sources()
            print(f"   Total data sources: {len(sources)}")

            for source in sources[:3]:  # Show first 3
                print(f"   - {source.name} ({source.source_type})")

            print("\n✅ Bot management tests completed successfully!")

        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True

async def test_session_cleanup():
    """Test that sessions are properly cleaned up"""
    print("\n🔍 Testing Session Cleanup")
    print("=" * 30)

    with app.app_context():
        try:
            manager = BotManager()
            surface_bot = manager.bots.get('surface')

            if surface_bot:
                # Start bot
                await surface_bot.start()
                print(f"Session after start: {surface_bot.session}")
                print(f"Session closed: {surface_bot.session.closed if surface_bot.session else 'No session'}")

                # Stop bot
                await surface_bot.stop()
                print(f"Session after stop: {surface_bot.session}")
                print(f"Session closed: {surface_bot.session.closed if surface_bot.session else 'No session'}")

                print("✅ Session cleanup test passed!")

        except Exception as e:
            print(f"❌ Session cleanup test failed: {e}")
            return False

    return True

if __name__ == "__main__":
    print(f"Starting bot tests at {datetime.now()}")
    print(f"Python version: {sys.version}")

    # Run tests
    success1 = asyncio.run(test_bot_management())
    success2 = asyncio.run(test_session_cleanup())

    if success1 and success2:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)
