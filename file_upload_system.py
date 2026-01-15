"""
Advanced File Upload System with Malware Scanning and Risk Assessment
"""

import os
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)

# Try to import magic, fallback if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available, using fallback MIME detection")

class FileUploadManager:
    """Manages file uploads with security scanning and risk assessment"""

    def __init__(self, upload_folder: str = 'uploads', quarantine_folder: str = 'quarantine'):
        self.upload_folder = upload_folder
        self.quarantine_folder = quarantine_folder
        self.allowed_extensions = {
            'csv', 'json', 'zip', '7z', 'sql', 'txt', 'pdf', 'doc', 'docx',
            'xls', 'xlsx', 'xml', 'html', 'htm', 'log', 'conf', 'cfg'
        }
        self.risk_patterns = {
            'high': [
                'password', 'credential', 'secret', 'key', 'token',
                'private', 'confidential', 'sensitive'
            ],
            'medium': [
                'email', 'phone', 'address', 'ssn', 'credit',
                'financial', 'personal', 'user', 'admin'
            ],
            'low': [
                'public', 'readme', 'license', 'changelog', 'version'
            ]
        }

        # Create directories
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(quarantine_folder, exist_ok=True)

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan file for malware and assess risk"""
        try:
            # Get file info
            file_size = os.path.getsize(file_path)
            file_hash = self._calculate_hash(file_path)

            # Detect MIME type
            if MAGIC_AVAILABLE:
                mime_type = magic.from_file(file_path, mime=True)
            else:
                # Fallback MIME detection based on extension
                _, ext = os.path.splitext(file_path)
                extension = ext.lower().lstrip('.') if ext else ''
                mime_type = self._get_expected_mime(extension) or 'application/octet-stream'

            # Extract file extension
            _, ext = os.path.splitext(file_path)
            extension = ext.lower().lstrip('.') if ext else ''

            # Risk assessment
            risk_assessment = self._assess_risk(file_path, mime_type, extension)

            # Malware scan (placeholder - integrate with actual scanner)
            malware_scan = self._scan_malware(file_path)

            return {
                'file_size': file_size,
                'file_hash': file_hash,
                'mime_type': mime_type,
                'extension': extension,
                'risk_assessment': risk_assessment,
                'malware_scan': malware_scan,
                'scan_timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
            return {
                'error': str(e),
                'risk_assessment': {'level': 'critical', 'score': 100}
            }

    def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _assess_risk(self, file_path: str, mime_type: str, extension: str) -> Dict[str, Any]:
        """Assess risk level of the file"""
        risk_score = 0
        risk_factors = []

        # Check file extension
        if extension not in self.allowed_extensions:
            risk_score += 30
            risk_factors.append(f'Extension {extension} not in allowed list')

        # Check file size (very large files are suspicious)
        file_size = os.path.getsize(file_path)
        if file_size > 100 * 1024 * 1024:  # 100MB
            risk_score += 20
            risk_factors.append('File size exceeds 100MB')

        # Check MIME type consistency
        expected_mime = self._get_expected_mime(extension)
        if expected_mime and mime_type != expected_mime:
            risk_score += 25
            risk_factors.append(f'MIME type mismatch: expected {expected_mime}, got {mime_type}')

        # Content analysis (sample content for risk patterns)
        try:
            content_sample = self._extract_content_sample(file_path, mime_type)
            content_risks = self._analyze_content_risk(content_sample)
            risk_score += content_risks['score']
            risk_factors.extend(content_risks['factors'])
        except Exception as e:
            risk_score += 10
            risk_factors.append(f'Content analysis failed: {str(e)}')

        # Determine risk level
        if risk_score >= 70:
            risk_level = 'critical'
        elif risk_score >= 40:
            risk_level = 'high'
        elif risk_score >= 20:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return {
            'level': risk_level,
            'score': risk_score,
            'factors': risk_factors,
            'recommendations': self._get_risk_recommendations(risk_level)
        }

    def _get_expected_mime(self, extension: str) -> Optional[str]:
        """Get expected MIME type for file extension"""
        mime_map = {
            'csv': 'text/csv',
            'json': 'application/json',
            'zip': 'application/zip',
            '7z': 'application/x-7z-compressed',
            'sql': 'application/sql',
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xml': 'application/xml',
            'html': 'text/html',
            'htm': 'text/html'
        }
        return mime_map.get(extension)

    def _extract_content_sample(self, file_path: str, mime_type: str) -> str:
        """Extract sample content from file for analysis"""
        try:
            if mime_type.startswith('text/'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(1024)  # First 1KB
            elif mime_type == 'application/json':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1024)
                    # Try to parse as JSON to see structure
                    try:
                        json.loads(content)
                        return content
                    except:
                        return content
            else:
                # For binary files, just return file info
                return f"Binary file: {mime_type}"
        except Exception:
            return "Content extraction failed"

    def _analyze_content_risk(self, content: str) -> Dict[str, Any]:
        """Analyze content for risk patterns"""
        score = 0
        factors = []

        content_lower = content.lower()

        # Check for high-risk patterns
        for pattern in self.risk_patterns['high']:
            if pattern in content_lower:
                score += 15
                factors.append(f'Contains high-risk pattern: {pattern}')

        # Check for medium-risk patterns
        for pattern in self.risk_patterns['medium']:
            if pattern in content_lower:
                score += 8
                factors.append(f'Contains medium-risk pattern: {pattern}')

        # Check for low-risk patterns (reduce risk)
        for pattern in self.risk_patterns['low']:
            if pattern in content_lower:
                score = max(0, score - 5)
                factors.append(f'Contains low-risk pattern: {pattern}')

        return {'score': score, 'factors': factors}

    def _get_risk_recommendations(self, risk_level: str) -> List[str]:
        """Get recommendations based on risk level"""
        recommendations = {
            'critical': [
                'Quarantine file immediately',
                'Do not process or store full content',
                'Notify security team',
                'Consider deleting file'
            ],
            'high': [
                'Store in secure location',
                'Limit access to authorized personnel',
                'Extract only metadata',
                'Monitor access logs'
            ],
            'medium': [
                'Store with encryption',
                'Regular security scans',
                'Access logging enabled'
            ],
            'low': [
                'Standard storage procedures',
                'Regular backup',
                'Normal access controls'
            ]
        }
        return recommendations.get(risk_level, [])

    def _scan_malware(self, file_path: str) -> Dict[str, Any]:
        """Scan file for malware (placeholder for actual scanner integration)"""
        # This is a placeholder - integrate with actual malware scanner like ClamAV
        try:
            # Simulate malware scan
            file_size = os.path.getsize(file_path)

            # Simple heuristics (this should be replaced with real scanner)
            suspicious_indicators = []

            if file_size == 0:
                suspicious_indicators.append('Empty file')

            # Check file extension vs content
            _, ext = os.path.splitext(file_path)
            if ext.lower() in ['.exe', '.bat', '.scr', '.pif']:
                suspicious_indicators.append('Executable file extension')

            # For now, return clean result
            return {
                'status': 'clean' if not suspicious_indicators else 'suspicious',
                'scanner': 'basic_heuristics',
                'indicators': suspicious_indicators,
                'recommendation': 'Integrate with ClamAV or VirusTotal for real scanning'
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'scanner': 'basic_heuristics'
            }

    def process_upload(self, file, uploader_id: int = None, is_public: bool = False) -> Dict[str, Any]:
        """Process file upload with scanning and risk assessment"""
        try:
            # Secure filename
            filename = secure_filename(file.filename)
            if not filename:
                return {'error': 'Invalid filename'}

            # Check file extension
            _, ext = os.path.splitext(filename)
            extension = ext.lower().lstrip('.') if ext else ''

            if extension not in self.allowed_extensions:
                return {'error': f'File type .{extension} not allowed'}

            # Generate unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{uploader_id or 'anonymous'}_{filename}"
            file_path = os.path.join(self.upload_folder, unique_filename)

            # Save file temporarily for scanning
            file.save(file_path)

            # Scan file
            scan_result = self.scan_file(file_path)

            if scan_result.get('error'):
                # Remove file if scan failed
                os.remove(file_path)
                return scan_result

            # Determine storage location based on risk
            risk_level = scan_result['risk_assessment']['level']

            if risk_level == 'critical':
                # Move to quarantine
                quarantine_path = os.path.join(self.quarantine_folder, unique_filename)
                os.rename(file_path, quarantine_path)
                storage_path = quarantine_path
                storage_status = 'quarantined'
            else:
                storage_path = file_path
                storage_status = 'stored'

            # Extract partial content for non-critical files
            partial_content = None
            if risk_level != 'critical':
                try:
                    partial_content = self._extract_partial_content(file_path, scan_result['mime_type'])
                except Exception as e:
                    logger.warning(f"Failed to extract partial content: {e}")

            # Prepare result
            result = {
                'filename': filename,
                'unique_filename': unique_filename,
                'storage_path': storage_path,
                'storage_status': storage_status,
                'uploader_id': uploader_id,
                'is_public': is_public,
                'uploaded_at': datetime.utcnow().isoformat(),
                'scan_result': scan_result,
                'partial_content': partial_content
            }

            return result

        except Exception as e:
            logger.error(f"Error processing upload: {e}")
            return {'error': str(e)}

    def _extract_partial_content(self, file_path: str, mime_type: str) -> Optional[str]:
        """Extract partial content for storage (metadata only for risky files)"""
        try:
            if mime_type.startswith('text/') or mime_type == 'application/json':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2048)  # First 2KB
                    return content
            elif mime_type == 'text/csv':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i < 5:  # First 5 lines
                            lines.append(line.strip())
                        else:
                            break
                    return '\n'.join(lines)
            else:
                # For other types, just return file info
                file_size = os.path.getsize(file_path)
                return f"Binary file - Size: {file_size} bytes, Type: {mime_type}"

        except Exception as e:
            return f"Content extraction failed: {str(e)}"

# Global instance
upload_manager = FileUploadManager()
