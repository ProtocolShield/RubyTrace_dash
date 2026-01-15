"""
Advanced file collection system for downloading and analyzing documents.
"""

import asyncio
import aiohttp
import os
import hashlib
try:
    import magic  # Optional; may be unavailable on Windows
except Exception:
    magic = None
import logging
import mimetypes
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path
import json
import PyPDF2
import docx
import zipfile
import tarfile
from models import db, ScrapeLog
from database import with_retry

class FileCollector:
    def __init__(self, download_dir='downloads'):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # File type configurations
        self.file_types = {
            'documents': {
                'extensions': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
                'max_size': 50 * 1024 * 1024,  # 50MB
                'priority': 'high'
            },
            'archives': {
                'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
                'max_size': 100 * 1024 * 1024,  # 100MB
                'priority': 'medium'
            },
            'data': {
                'extensions': ['.csv', '.json', '.xml', '.sql', '.db', '.xlsx', '.xls'],
                'max_size': 25 * 1024 * 1024,  # 25MB
                'priority': 'high'
            },
            'media': {
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
                'max_size': 10 * 1024 * 1024,  # 10MB
                'priority': 'low'
            }
        }
        
        # Privacy-related keywords for content filtering
        self.privacy_keywords = [
            'personal data', 'pii', 'personally identifiable',
            'social security', 'ssn', 'credit card', 'passport',
            'driver license', 'medical record', 'health data',
            'financial record', 'bank account', 'surveillance',
            'classified', 'confidential', 'secret', 'leak'
        ]

    async def scan_and_download(self, url, keywords, session=None):
        """Scan URL for files and download relevant ones"""
        if not session:
            async with aiohttp.ClientSession() as session:
                return await self._scan_url(url, keywords, session)
        else:
            return await self._scan_url(url, keywords, session)

    async def _scan_url(self, url, keywords, session):
        """Internal method to scan URL for downloadable files"""
        downloaded_files = []
        
        try:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    return downloaded_files
                
                content = await response.text()
                file_links = self._extract_file_links(content, url)
                
                # Filter and prioritize files
                prioritized_files = self._prioritize_files(file_links)
                
                # Download files with rate limiting
                for file_url, file_info in prioritized_files[:20]:  # Limit to 20 files per page
                    try:
                        downloaded_file = await self._download_file(file_url, file_info, session)
                        if downloaded_file:
                            # Analyze content for privacy keywords
                            content_analysis = await self._analyze_file_content(downloaded_file)
                            if self._contains_privacy_content(content_analysis, keywords):
                                downloaded_files.append({
                                    'file_path': downloaded_file,
                                    'url': file_url,
                                    'analysis': content_analysis,
                                    'relevance_score': self._calculate_relevance(content_analysis, keywords)
                                })
                            
                        await asyncio.sleep(1)  # Rate limiting
                        
                    except Exception as e:
                        logging.error(f"Error downloading {file_url}: {e}")
                        continue
        
        except Exception as e:
            logging.error(f"Error scanning {url}: {e}")
        
        return downloaded_files

    def _extract_file_links(self, content, base_url):
        """Extract downloadable file links from HTML content"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, 'html.parser')
        file_links = []
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Check if it's a downloadable file
            parsed_url = urlparse(full_url)
            path = parsed_url.path.lower()
            
            for file_type, config in self.file_types.items():
                for ext in config['extensions']:
                    if path.endswith(ext):
                        file_links.append((full_url, {
                            'type': file_type,
                            'extension': ext,
                            'text': link.get_text(strip=True),
                            'title': link.get('title', ''),
                            'max_size': config['max_size'],
                            'priority': config['priority']
                        }))
                        break
        
        return file_links

    def _prioritize_files(self, file_links):
        """Prioritize files based on type and relevance"""
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        
        return sorted(file_links, key=lambda x: (
            priority_order.get(x[1]['priority'], 4),
            -len(x[1]['text'])  # Longer descriptions might be more relevant
        ))

    async def _download_file(self, url, file_info, session):
        """Download a single file with size and type validation"""
        try:
            async with session.head(url) as response:
                if response.status != 200:
                    return None
                
                # Check file size
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > file_info['max_size']:
                    logging.info(f"Skipping large file: {url} ({content_length} bytes)")
                    return None
            
            # Download the file
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                content = await response.read()
                
                # Generate unique filename
                filename = self._generate_filename(url, file_info['extension'])
                file_path = self.download_dir / filename
                
                # Save file
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Verify file type
                if not self._verify_file_type(file_path, file_info['extension']):
                    os.remove(file_path)
                    return None
                
                await self._log_download(url, str(file_path), len(content))
                logging.info(f"Downloaded: {filename} ({len(content)} bytes)")
                
                return str(file_path)
        
        except Exception as e:
            logging.error(f"Download error for {url}: {e}")
            return None

    def _generate_filename(self, url, extension):
        """Generate unique filename for download"""
        # Create hash of URL for uniqueness
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract meaningful name from URL
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if path_parts and path_parts[-1]:
            base_name = path_parts[-1].replace(extension, '')[:50]
        else:
            base_name = "file"
        
        return f"{base_name}_{timestamp}_{url_hash}{extension}"

    def _verify_file_type(self, file_path, expected_extension):
        """Verify file type matches extension (best-effort; tolerant if unavailable)"""
        try:
            # Prefer magic if available
            if magic is not None:
                mime_type = magic.from_file(str(file_path), mime=True)
            else:
                # Fallback: guess from extension or file content
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if mime_type is None:
                    # Basic heuristic: treat unknown as acceptable
                    return True
            
            expected_mimes = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain',
                '.zip': 'application/zip',
                '.json': 'application/json',
                '.csv': 'text/csv'
            }
            expected_mime = expected_mimes.get(expected_extension)
            if expected_mime and mime_type and expected_mime in mime_type:
                return True
            if expected_extension == '.txt' and mime_type and 'text/' in mime_type:
                return True
            # If we can't strongly verify, allow
            return True
        except Exception:
            return True  # Allow if verification fails

    async def _analyze_file_content(self, file_path):
        """Analyze file content for privacy-related information"""
        try:
            file_path = Path(file_path)
            extension = file_path.suffix.lower()
            
            if extension == '.pdf':
                return await self._analyze_pdf(file_path)
            elif extension in ['.doc', '.docx']:
                return await self._analyze_word_doc(file_path)
            elif extension == '.txt':
                return await self._analyze_text_file(file_path)
            elif extension == '.json':
                return await self._analyze_json_file(file_path)
            elif extension in ['.zip', '.tar', '.gz']:
                return await self._analyze_archive(file_path)
            else:
                return {'content': '', 'metadata': {}}
        
        except Exception as e:
            logging.error(f"Error analyzing {file_path}: {e}")
            return {'content': '', 'metadata': {}}

    async def _analyze_pdf(self, file_path):
        """Analyze PDF content"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in reader.pages[:10]:  # Limit to first 10 pages
                    text += page.extract_text()
                
                metadata = {
                    'page_count': len(reader.pages),
                    'title': reader.metadata.get('/Title', '') if reader.metadata else '',
                    'author': reader.metadata.get('/Author', '') if reader.metadata else ''
                }
                
                return {'content': text[:5000], 'metadata': metadata}  # Limit content length
        except Exception as e:
            logging.error(f"PDF analysis error: {e}")
            return {'content': '', 'metadata': {}}

    async def _analyze_word_doc(self, file_path):
        """Analyze Word document content"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs[:50]])  # First 50 paragraphs
            
            metadata = {
                'paragraph_count': len(doc.paragraphs),
                'title': doc.core_properties.title or '',
                'author': doc.core_properties.author or ''
            }
            
            return {'content': text[:5000], 'metadata': metadata}
        except Exception as e:
            logging.error(f"Word doc analysis error: {e}")
            return {'content': '', 'metadata': {}}

    async def _analyze_text_file(self, file_path):
        """Analyze text file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read(5000)  # First 5000 characters
            
            metadata = {
                'line_count': content.count('\n'),
                'char_count': len(content)
            }
            
            return {'content': content, 'metadata': metadata}
        except Exception as e:
            logging.error(f"Text file analysis error: {e}")
            return {'content': '', 'metadata': {}}

    async def _analyze_json_file(self, file_path):
        """Analyze JSON file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Convert to string for keyword analysis
            content = json.dumps(data, indent=2)[:5000]
            
            metadata = {
                'type': type(data).__name__,
                'keys': list(data.keys()) if isinstance(data, dict) else [],
                'size': len(str(data))
            }
            
            return {'content': content, 'metadata': metadata}
        except Exception as e:
            logging.error(f"JSON analysis error: {e}")
            return {'content': '', 'metadata': {}}

    async def _analyze_archive(self, file_path):
        """Analyze archive file content"""
        try:
            extension = file_path.suffix.lower()
            file_list = []
            
            if extension == '.zip':
                with zipfile.ZipFile(file_path, 'r') as archive:
                    file_list = archive.namelist()[:100]  # First 100 files
            elif extension in ['.tar', '.gz']:
                with tarfile.open(file_path, 'r') as archive:
                    file_list = archive.getnames()[:100]
            
            content = "\n".join(file_list)
            metadata = {
                'file_count': len(file_list),
                'file_types': list(set([os.path.splitext(f)[1] for f in file_list if '.' in f]))
            }
            
            return {'content': content, 'metadata': metadata}
        except Exception as e:
            logging.error(f"Archive analysis error: {e}")
            return {'content': '', 'metadata': {}}

    def _contains_privacy_content(self, analysis, keywords):
        """Check if file contains privacy-related content"""
        content = analysis.get('content', '').lower()
        
        # Check provided keywords
        for keyword in keywords:
            if keyword.lower() in content:
                return True
        
        # Check privacy-specific keywords
        for keyword in self.privacy_keywords:
            if keyword in content:
                return True
        
        return False

    def _calculate_relevance(self, analysis, keywords):
        """Calculate relevance score for file content"""
        content = analysis.get('content', '').lower()
        score = 0
        
        # Score based on keyword matches
        for keyword in keywords + self.privacy_keywords:
            score += content.count(keyword.lower()) * 10
        
        # Bonus for metadata relevance
        metadata = analysis.get('metadata', {})
        title = str(metadata.get('title', '')).lower()
        author = str(metadata.get('author', '')).lower()
        
        for keyword in keywords:
            if keyword.lower() in title:
                score += 20
            if keyword.lower() in author:
                score += 15
        
        return min(score, 100)  # Cap at 100

    async def _log_download(self, url, file_path, file_size):
        """Log file download to database"""
        @with_retry
        def save_log():
            try:
                log_entry = ScrapeLog(
                    source_name="File Collector",
                    status="success",
                    items_found=1,
                    items_added=1,
                    error_message=f"Downloaded: {os.path.basename(file_path)} ({file_size} bytes) from {url}"
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                logging.error(f"Error logging download: {e}")
                db.session.rollback()
        
        save_log()

    def get_downloaded_files(self, limit=100):
        """Get list of downloaded files with metadata"""
        files = []
        
        try:
            for file_path in self.download_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'extension': file_path.suffix
                    })
            
            # Sort by modification time, newest first
            files.sort(key=lambda x: x['modified'], reverse=True)
            return files[:limit]
        
        except Exception as e:
            logging.error(f"Error listing files: {e}")
            return []

# Global file collector instance
file_collector = FileCollector()

async def collect_files_from_url(url, keywords):
    """Collect files from a specific URL"""
    return await file_collector.scan_and_download(url, keywords)

def get_download_summary():
    """Get summary of downloaded files"""
    return file_collector.get_downloaded_files()