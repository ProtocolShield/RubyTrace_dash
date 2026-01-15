"""
Scheduler for running the enhanced crawler automatically.
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime
from threading import Thread
from crawlers.enhanced_crawler import run_crawler
from models import db, KeywordAlert, Source
from database import with_retry

class CrawlerScheduler:
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        
    def start(self):
        """Start the crawler scheduler"""
        if self.running:
            return
            
        self.running = True
        
        # Schedule different crawling tasks
        schedule.every(15).minutes.do(self._run_surface_web_crawl)
        schedule.every(1).hours.do(self._run_tor_crawl)
        schedule.every(30).minutes.do(self._run_file_download)
        
        # Start scheduler in separate thread
        self.scheduler_thread = Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logging.info("Crawler scheduler started")
    
    def stop(self):
        """Stop the crawler scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logging.info("Crawler scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    @with_retry
    def _get_active_keywords(self):
        """Get active keywords from database"""
        try:
            alerts = db.session.query(KeywordAlert).filter_by(enabled=True).all()
            return [alert.keyword for alert in alerts]
        except Exception as e:
            logging.error(f"Error fetching keywords: {e}")
            return ['privacy', 'data breach', 'leak', 'personal information']
    
    @with_retry
    def _get_active_sources(self):
        """Get active sources from database"""
        try:
            sources = db.session.query(Source).filter_by(enabled=True).all()
            return [source.url for source in sources]
        except Exception as e:
            logging.error(f"Error fetching sources: {e}")
            return []
    
    def _run_surface_web_crawl(self):
        """Run surface web crawling"""
        try:
            keywords = self._get_active_keywords()
            sites = self._get_active_sources()
            
            # Filter out .onion sites for surface web crawl
            surface_sites = [site for site in sites if '.onion' not in site]
            
            logging.info(f"Starting surface web crawl with keywords: {keywords}")
            
            # Run crawler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                run_crawler(keywords, surface_sites, use_tor=False)
            )
            loop.close()
            
            logging.info(f"Surface web crawl completed: {len(results) if isinstance(results, list) else 'N/A'} results")
            
        except Exception as e:
            logging.error(f"Error in surface web crawl: {e}")
    
    def _run_tor_crawl(self):
        """Run dark web crawling with Tor"""
        try:
            keywords = self._get_active_keywords()
            sites = self._get_active_sources()
            
            # Filter .onion sites for Tor crawl
            onion_sites = [site for site in sites if '.onion' in site]
            
            logging.info(f"Starting Tor crawl with keywords: {keywords}")
            
            # Run Tor crawler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                run_crawler(keywords, onion_sites, use_tor=True)
            )
            loop.close()
            
            logging.info(f"Tor crawl completed: {len(results) if isinstance(results, list) else 'N/A'} results")
            
        except Exception as e:
            logging.error(f"Error in Tor crawl: {e}")
    
    def _run_file_download(self):
        """Run file downloading from discovered sources"""
        try:
            keywords = self._get_active_keywords()
            sites = self._get_active_sources()
            
            logging.info(f"Starting file download from {len(sites)} sources")
            
            # Run file download
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            from crawlers.enhanced_crawler import EnhancedCrawler
            crawler = EnhancedCrawler()
            
            async def download_from_sites():
                await crawler.init_session()
                try:
                    total_downloads = 0
                    for site in sites[:10]:  # Limit to 10 sites per run
                        downloads = await crawler.download_files(site)
                        total_downloads += len(downloads)
                    return total_downloads
                finally:
                    await crawler.close_session()
            
            total_downloads = loop.run_until_complete(download_from_sites())
            loop.close()
            
            logging.info(f"File download completed: {total_downloads} files downloaded")
            
        except Exception as e:
            logging.error(f"Error in file download: {e}")

# Global scheduler instance
crawler_scheduler = CrawlerScheduler()

def start_crawler_scheduler():
    """Start the global crawler scheduler"""
    crawler_scheduler.start()

def stop_crawler_scheduler():
    """Stop the global crawler scheduler"""
    crawler_scheduler.stop()