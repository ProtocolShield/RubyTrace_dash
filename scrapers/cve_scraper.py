import logging
import json
import requests
from datetime import datetime
from api import app
from models import CVEItem, db

def scrape_cve_data():
    """
    Scrape CVE data from NVD and other sources with detailed information.
    """
    from api import app

    cve_sources = [
        {
            "name": "NVD",
            "url": "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=50"
        }
    ]

    with app.app_context():
        for source in cve_sources:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }

                response = requests.get(source["url"], headers=headers)
                response.raise_for_status()
                data = response.json()

                # NVD API returns data in 'vulnerabilities' array
                vulnerabilities = data.get('vulnerabilities', [])
                cves_added = 0

                for vuln in vulnerabilities:
                    cve_data = vuln.get('cve', {})

                    # Extract CVSS metrics
                    metrics = cve_data.get('metrics', {})
                    cvss_data = None
                    cvss_version = None

                    if 'cvssMetricV31' in metrics:
                        cvss_data = metrics['cvssMetricV31'][0]['cvssData']
                        cvss_version = '3.1'
                    elif 'cvssMetricV30' in metrics:
                        cvss_data = metrics['cvssMetricV30'][0]['cvssData']
                        cvss_version = '3.0'
                    elif 'cvssMetricV2' in metrics:
                        cvss_data = metrics['cvssMetricV2'][0]['cvssData']
                        cvss_version = '2.0'

                    # Extract affected products
                    configurations = cve_data.get('configurations', [])
                    affected_products = []
                    affected_vendors = set()
                    for config in configurations:
                        for node in config.get('nodes', []):
                            for cpe_match in node.get('cpeMatch', []):
                                if 'criteria' in cpe_match:
                                    criteria = cpe_match['criteria']
                                    affected_products.append(criteria)
                                    # Extract vendor from CPE: cpe:2.3:a:vendor:product:version:...
                                    if criteria.startswith('cpe:2.3:'):
                                        parts = criteria.split(':')
                                        if len(parts) > 3:
                                            vendor = parts[3]
                                            if vendor:
                                                affected_vendors.add(vendor)

                    # Extract description
                    descriptions = cve_data.get('descriptions', [])
                    description = ""
                    for desc in descriptions:
                        if desc.get('lang') == 'en':
                            description = desc.get('value', '')
                            break

                    # Extract references
                    references = cve_data.get('references', [])
                    reference_urls = [ref.get('url') for ref in references]

                    # Extract last modified
                    last_modified = cve_data.get('lastModified', '')
                    last_modified_at = datetime.fromisoformat(last_modified.replace('Z', '+00:00')) if last_modified else None

                    # Determine severity based on CVSS score
                    severity = 'Unknown'
                    cvss_score = 0.0
                    if cvss_data:
                        cvss_score = cvss_data.get('baseScore', 0)
                        if cvss_score >= 9.0:
                            severity = 'Critical'
                        elif cvss_score >= 7.0:
                            severity = 'High'
                        elif cvss_score >= 4.0:
                            severity = 'Medium'
                        elif cvss_score >= 0.1:
                            severity = 'Low'

                    # Check if CVE already exists
                    existing = CVEItem.query.filter_by(cve_id=cve_data.get('id')).first()
                    if existing:
                        continue

                    cve_item = CVEItem(
                        cve_id=cve_data.get('id'),
                        title=f"CVE {cve_data.get('id')} - {description[:100]}..." if len(description) > 100 else f"CVE {cve_data.get('id')}",
                        description=description,
                        severity=severity,
                        cvss=cvss_score,
                        cvss_vector=cvss_data.get('vectorString') if cvss_data else None,
                        affected_products=json.dumps(affected_products[:10]) if affected_products else None,
                        affected_vendors=json.dumps(list(affected_vendors)) if affected_vendors else None,
                        tags='',  # Empty for now, could populate from CWE
                        source_url=f"https://nvd.nist.gov/vuln/detail/{cve_data.get('id')}",
                        references=json.dumps(reference_urls) if reference_urls else None,
                        published_at=datetime.fromisoformat(cve_data.get('published', '').replace('Z', '+00:00')) if cve_data.get('published') else None,
                        last_modified_at=last_modified_at,
                        created_at=datetime.utcnow()
                    )

                    try:
                        db.session.add(cve_item)
                        cves_added += 1
                    except Exception as add_error:
                        logging.error(f"Error adding CVE {cve_data.get('id')}: {add_error}")

                try:
                    db.session.commit()
                    logging.info(f"Successfully scraped and stored {cves_added} CVEs from {source['name']}")
                except Exception as commit_error:
                    db.session.rollback()
                    logging.error(f"Error committing CVEs from {source['name']}: {commit_error}")

            except Exception as e:
                logging.error(f"Error scraping {source['name']}: {e}")

if __name__ == "__main__":
    scrape_cve_data()
