"""
CVE Manager Module
Handles CVE data retrieval, filtering, and management operations
"""

from models import CVEItem as CVE, db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CVEManager:
    """Manager class for CVE operations"""

    @staticmethod
    def get_all_cves(limit=None, offset=0):
        """Get all CVEs with optional pagination"""
        try:
            query = CVE.query.order_by(CVE.created_at.desc())

            if limit:
                query = query.limit(limit).offset(offset)

            cves = query.all()
            return [cve.to_dict() for cve in cves]

        except Exception as e:
            logger.error(f"Error retrieving CVEs: {e}")
            return []

    @staticmethod
    def get_cves_by_severity(severity, limit=None):
        """Get CVEs filtered by severity"""
        try:
            query = CVE.query.filter(CVE.severity.ilike(f"%{severity}%")).order_by(CVE.created_at.desc())

            if limit:
                query = query.limit(limit)

            cves = query.all()
            return [cve.to_dict() for cve in cves]

        except Exception as e:
            logger.error(f"Error retrieving CVEs by severity: {e}")
            return []

    @staticmethod
    def get_recent_cves(days=30, limit=None):
        """Get CVEs from the last N days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = CVE.query.filter(CVE.created_at >= cutoff_date).order_by(CVE.created_at.desc())

            if limit:
                query = query.limit(limit)

            cves = query.all()
            return [cve.to_dict() for cve in cves]

        except Exception as e:
            logger.error(f"Error retrieving recent CVEs: {e}")
            return []

    @staticmethod
    def search_cves(search_term, limit=None):
        """Search CVEs by CVE ID, title, or description"""
        try:
            search_filter = f"%{search_term}%"
            query = CVE.query.filter(
                (CVE.cve_id.ilike(search_filter)) |
                (CVE.title.ilike(search_filter)) |
                (CVE.description.ilike(search_filter))
            ).order_by(CVE.created_at.desc())

            if limit:
                query = query.limit(limit)

            cves = query.all()
            return [cve.to_dict() for cve in cves]

        except Exception as e:
            logger.error(f"Error searching CVEs: {e}")
            return []

    @staticmethod
    def get_cve_statistics():
        """Get CVE statistics by severity"""
        try:
            # Get counts by severity
            critical_count = CVE.query.filter(CVE.severity.ilike("%critical%")).count()
            high_count = CVE.query.filter(CVE.severity.ilike("%high%")).count()
            medium_count = CVE.query.filter(CVE.severity.ilike("%medium%")).count()
            low_count = CVE.query.filter(CVE.severity.ilike("%low%")).count()

            # Get total count
            total_count = CVE.query.count()

            # Get recent CVEs (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_count = CVE.query.filter(CVE.created_at >= week_ago).count()

            return {
                'total': total_count,
                'critical': critical_count,
                'high': high_count,
                'medium': medium_count,
                'low': low_count,
                'recent': recent_count
            }

        except Exception as e:
            logger.error(f"Error getting CVE statistics: {e}")
            return {
                'total': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'recent': 0
            }

    @staticmethod
    def get_cve_by_id(cve_id):
        """Get a specific CVE by ID"""
        try:
            cve = CVE.query.filter_by(cve_id=cve_id).first()
            return cve.to_dict() if cve else None

        except Exception as e:
            logger.error(f"Error retrieving CVE {cve_id}: {e}")
            return None



# Convenience functions for direct use
def get_all_cves(limit=None, offset=0):
    """Convenience function to get all CVEs"""
    return CVEManager.get_all_cves(limit=limit, offset=offset)

def get_cves_by_severity(severity, limit=None):
    """Convenience function to get CVEs by severity"""
    return CVEManager.get_cves_by_severity(severity, limit=limit)

def get_recent_cves(days=30, limit=None):
    """Convenience function to get recent CVEs"""
    return CVEManager.get_recent_cves(days=days, limit=limit)

def search_cves(search_term, limit=None):
    """Convenience function to search CVEs"""
    return CVEManager.search_cves(search_term, limit=limit)

def get_cve_statistics():
    """Convenience function to get CVE statistics"""
    return CVEManager.get_cve_statistics()

def get_cve_by_id(cve_id):
    """Convenience function to get a specific CVE"""
    return CVEManager.get_cve_by_id(cve_id)


