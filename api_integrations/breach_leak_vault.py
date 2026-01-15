"""
Central Breach and Leak Data Vault
Provides search, filtering, and metadata management for breach/leak data
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import or_, and_, func, desc
from models import db, BreachItem, LeakItem

logger = logging.getLogger(__name__)

class BreachLeakVault:
    """Central vault for managing breach and leak data with advanced search capabilities"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def add_breach(self, breach_data: Dict[str, Any]) -> bool:
        """Add a new breach to the vault"""
        try:
            breach = BreachItem(
                name=breach_data.get('name', ''),
                description=breach_data.get('description'),
                affected_organizations=json.dumps(breach_data.get('affected_organizations', [])),
                data_types_exposed=json.dumps(breach_data.get('data_types_exposed', [])),
                records_affected=breach_data.get('records_affected'),
                discovery_date=self._parse_date(breach_data.get('discovery_date')),
                disclosure_date=self._parse_date(breach_data.get('disclosure_date')),
                source_url=breach_data.get('source_url')
            )

            db.session.add(breach)
            db.session.commit()
            self.logger.info(f"Added breach: {breach.name}")
            return True

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error adding breach: {e}")
            return False

    def add_leak(self, leak_data: Dict[str, Any]) -> bool:
        """Add a new leak to the vault"""
        try:
            leak = LeakItem(
                source=leak_data.get('source', ''),
                data_content=leak_data.get('data_content'),
                verification_status=leak_data.get('verification_status', 'unverified'),
                associated_breach_id=leak_data.get('associated_breach_id')
            )

            db.session.add(leak)
            db.session.commit()
            self.logger.info(f"Added leak from: {leak.source}")
            return True

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error adding leak: {e}")
            return False

    def search_breaches(self, query: str = "", filters: Dict[str, Any] = None,
                       page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Search breaches with advanced filtering"""
        try:
            filters = filters or {}

            # Base query
            q = BreachItem.query

            # Text search
            if query:
                search_terms = query.split()
                search_filters = []
                for term in search_terms:
                    search_filters.append(
                        or_(
                            BreachItem.name.ilike(f'%{term}%'),
                            BreachItem.description.ilike(f'%{term}%'),
                            BreachItem.source_url.ilike(f'%{term}%')
                        )
                    )
                q = q.filter(and_(*search_filters))

            # Apply filters
            if 'min_records' in filters:
                q = q.filter(BreachItem.records_affected >= filters['min_records'])

            if 'max_records' in filters:
                q = q.filter(BreachItem.records_affected <= filters['max_records'])

            if 'data_types' in filters and filters['data_types']:
                data_type_filters = []
                for data_type in filters['data_types']:
                    data_type_filters.append(
                        BreachItem.data_types_exposed.ilike(f'%{data_type}%')
                    )
                q = q.filter(or_(*data_type_filters))

            if 'organizations' in filters and filters['organizations']:
                org_filters = []
                for org in filters['organizations']:
                    org_filters.append(
                        BreachItem.affected_organizations.ilike(f'%{org}%')
                    )
                q = q.filter(or_(*org_filters))

            if 'date_from' in filters:
                date_from = self._parse_date(filters['date_from'])
                if date_from:
                    q = q.filter(BreachItem.discovery_date >= date_from)

            if 'date_to' in filters:
                date_to = self._parse_date(filters['date_to'])
                if date_to:
                    q = q.filter(BreachItem.discovery_date <= date_to)

            # Get total count
            total = q.count()

            # Apply sorting and pagination
            sort_by = filters.get('sort_by', 'discovery_date')
            sort_order = filters.get('sort_order', 'desc')

            if sort_by == 'name':
                q = q.order_by(desc(BreachItem.name) if sort_order == 'desc' else BreachItem.name)
            elif sort_by == 'records_affected':
                q = q.order_by(desc(BreachItem.records_affected) if sort_order == 'desc' else BreachItem.records_affected)
            else:  # default to discovery_date
                q = q.order_by(desc(BreachItem.discovery_date) if sort_order == 'desc' else BreachItem.discovery_date)

            # Pagination
            breaches = q.offset((page - 1) * per_page).limit(per_page).all()

            # Format results
            results = []
            for breach in breaches:
                results.append({
                    'id': breach.id,
                    'name': breach.name,
                    'description': breach.description,
                    'affected_organizations': json.loads(breach.affected_organizations or '[]'),
                    'data_types_exposed': json.loads(breach.data_types_exposed or '[]'),
                    'records_affected': breach.records_affected,
                    'discovery_date': breach.discovery_date.isoformat() if breach.discovery_date else None,
                    'disclosure_date': breach.disclosure_date.isoformat() if breach.disclosure_date else None,
                    'source_url': breach.source_url,
                    'created_at': breach.created_at.isoformat()
                })

            return {
                'results': results,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }

        except Exception as e:
            self.logger.error(f"Error searching breaches: {e}")
            return {'error': str(e)}

    def search_leaks(self, query: str = "", filters: Dict[str, Any] = None,
                    page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Search leaks with advanced filtering"""
        try:
            filters = filters or {}

            # Base query
            q = LeakItem.query

            # Text search
            if query:
                search_terms = query.split()
                search_filters = []
                for term in search_terms:
                    search_filters.append(
                        or_(
                            LeakItem.source.ilike(f'%{term}%'),
                            LeakItem.data_content.ilike(f'%{term}%')
                        )
                    )
                q = q.filter(and_(*search_filters))

            # Apply filters
            if 'verification_status' in filters:
                q = q.filter(LeakItem.verification_status == filters['verification_status'])

            if 'source' in filters:
                q = q.filter(LeakItem.source.ilike(f'%{filters["source"]}%'))

            if 'date_from' in filters:
                date_from = self._parse_date(filters['date_from'])
                if date_from:
                    q = q.filter(LeakItem.created_at >= date_from)

            if 'date_to' in filters:
                date_to = self._parse_date(filters['date_to'])
                if date_to:
                    q = q.filter(LeakItem.created_at <= date_to)

            # Get total count
            total = q.count()

            # Apply sorting
            sort_by = filters.get('sort_by', 'created_at')
            sort_order = filters.get('sort_order', 'desc')

            if sort_by == 'source':
                q = q.order_by(desc(LeakItem.source) if sort_order == 'desc' else LeakItem.source)
            else:  # default to created_at
                q = q.order_by(desc(LeakItem.created_at) if sort_order == 'desc' else LeakItem.created_at)

            # Pagination
            leaks = q.offset((page - 1) * per_page).limit(per_page).all()

            # Format results
            results = []
            for leak in leaks:
                results.append({
                    'id': leak.id,
                    'source': leak.source,
                    'data_content': leak.data_content,
                    'verification_status': leak.verification_status,
                    'associated_breach_id': leak.associated_breach_id,
                    'created_at': leak.created_at.isoformat()
                })

            return {
                'results': results,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }

        except Exception as e:
            self.logger.error(f"Error searching leaks: {e}")
            return {'error': str(e)}

    def get_vault_stats(self) -> Dict[str, Any]:
        """Get comprehensive vault statistics"""
        try:
            # Breach statistics
            breach_stats = db.session.query(
                func.count(BreachItem.id).label('total_breaches'),
                func.sum(BreachItem.records_affected).label('total_records_affected'),
                func.avg(BreachItem.records_affected).label('avg_records_per_breach')
            ).first()

            # Leak statistics
            leak_stats = db.session.query(
                func.count(LeakItem.id).label('total_leaks'),
                LeakItem.verification_status,
                func.count(LeakItem.id).label('count')
            ).group_by(LeakItem.verification_status).all()

            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_breaches = BreachItem.query.filter(
                BreachItem.created_at >= thirty_days_ago
            ).count()

            recent_leaks = LeakItem.query.filter(
                LeakItem.created_at >= thirty_days_ago
            ).count()

            # Top data types exposed
            data_type_counts = {}
            breaches = BreachItem.query.filter(BreachItem.data_types_exposed.isnot(None)).all()
            for breach in breaches:
                try:
                    data_types = json.loads(breach.data_types_exposed)
                    for dt in data_types:
                        data_type_counts[dt] = data_type_counts.get(dt, 0) + 1
                except:
                    pass

            # Top affected organizations
            org_counts = {}
            for breach in breaches:
                try:
                    orgs = json.loads(breach.affected_organizations or '[]')
                    for org in orgs:
                        org_counts[org] = org_counts.get(org, 0) + 1
                except:
                    pass

            return {
                'breach_stats': {
                    'total_breaches': breach_stats.total_breaches or 0,
                    'total_records_affected': breach_stats.total_records_affected or 0,
                    'avg_records_per_breach': float(breach_stats.avg_records_per_breach or 0)
                },
                'leak_stats': {
                    'total_leaks': sum(stat.count for stat in leak_stats),
                    'verification_breakdown': {stat.verification_status: stat.count for stat in leak_stats}
                },
                'recent_activity': {
                    'breaches_last_30_days': recent_breaches,
                    'leaks_last_30_days': recent_leaks
                },
                'top_data_types': dict(sorted(data_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                'top_organizations': dict(sorted(org_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            }

        except Exception as e:
            self.logger.error(f"Error getting vault stats: {e}")
            return {'error': str(e)}

    def deduplicate_breaches(self) -> int:
        """Remove duplicate breaches based on name and source_url"""
        try:
            # Find duplicates
            duplicates = db.session.query(
                BreachItem.name,
                BreachItem.source_url,
                func.count(BreachItem.id).label('count'),
                func.min(BreachItem.id).label('keep_id')
            ).group_by(BreachItem.name, BreachItem.source_url).having(func.count(BreachItem.id) > 1).all()

            removed_count = 0
            for dup in duplicates:
                # Delete all but the first occurrence
                deleted = db.session.query(BreachItem).filter(
                    and_(
                        BreachItem.name == dup.name,
                        BreachItem.source_url == dup.source_url,
                        BreachItem.id != dup.keep_id
                    )
                ).delete()
                removed_count += deleted

            db.session.commit()
            self.logger.info(f"Removed {removed_count} duplicate breaches")
            return removed_count

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deduplicating breaches: {e}")
            return 0

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        if not date_str:
            return None

        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Try common formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
                return None
            except:
                return None

# Global vault instance
vault = BreachLeakVault()
