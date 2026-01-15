"""
Data enrichment utilities for breach, leak, and CVE intelligence.
"""
import logging
from datetime import datetime
from models import BreachItem, LeakItem, CVEItem

def enrich_breach_data(breach):
    """
    Enrich breach data with additional context and risk scoring.
    
    Args:
        breach (BreachItem): The breach to enrich
        
    Returns:
        dict: Enriched breach data
    """
    try:
        # Calculate risk score based on various factors
        risk_score = calculate_breach_risk_score(breach)
        
        # Add additional context
        enriched_data = {
            'id': breach.id,
            'name': breach.name,
            'description': breach.description,
            'affected_organizations': breach.affected_organizations,
            'data_types_exposed': breach.data_types_exposed,
            'records_affected': breach.records_affected,
            'discovery_date': breach.discovery_date.isoformat() if breach.discovery_date else None,
            'disclosure_date': breach.disclosure_date.isoformat() if breach.disclosure_date else None,
            'source_url': breach.source_url,
            'created_at': breach.created_at.isoformat(),
            'risk_score': risk_score,
            'severity_level': get_severity_level(risk_score),
            'impact_assessment': assess_breach_impact(breach)
        }
        
        return enriched_data
    except Exception as e:
        logging.error(f"Error enriching breach data: {e}")
        return None

def calculate_breach_risk_score(breach):
    """
    Calculate a risk score for a breach based on various factors.
    
    Args:
        breach (BreachItem): The breach to score
        
    Returns:
        float: Risk score between 0 and 100
    """
    score = 0
    
    # Factor 1: Number of records affected
    if breach.records_affected:
        if breach.records_affected > 1000000:
            score += 40
        elif breach.records_affected > 100000:
            score += 30
        elif breach.records_affected > 10000:
            score += 20
        elif breach.records_affected > 1000:
            score += 10
    
    # Factor 2: Data types exposed
    if breach.data_types_exposed:
        data_types = breach.data_types_exposed.split(',')
        if 'password' in data_types:
            score += 25
        if 'email' in data_types:
            score += 15
        if 'credit_card' in data_types:
            score += 30
        if 'ssn' in data_types:
            score += 35
    
    # Factor 3: Time since discovery
    if breach.discovery_date:
        days_since_discovery = (datetime.utcnow() - breach.discovery_date).days
        if days_since_discovery < 7:
            score += 15  # Recent breaches are higher risk
    
    return min(score, 100)  # Cap at 100

def get_severity_level(risk_score):
    """
    Convert risk score to severity level.
    
    Args:
        risk_score (float): Risk score between 0 and 100
        
    Returns:
        str: Severity level (Low, Medium, High, Critical)
    """
    if risk_score >= 80:
        return "Critical"
    elif risk_score >= 60:
        return "High"
    elif risk_score >= 40:
        return "Medium"
    else:
        return "Low"

def assess_breach_impact(breach):
    """
    Assess the impact of a breach.
    
    Args:
        breach (BreachItem): The breach to assess
        
    Returns:
        dict: Impact assessment
    """
    impact = {
        'financial_impact': 'Unknown',
        'reputation_impact': 'Unknown',
        'operational_impact': 'Unknown'
    }
    
    # Simple impact assessment based on data types
    if breach.data_types_exposed:
        data_types = breach.data_types_exposed.split(',')
        if 'credit_card' in data_types or 'ssn' in data_types:
            impact['financial_impact'] = 'High'
            impact['reputation_impact'] = 'High'
        elif 'password' in data_types:
            impact['operational_impact'] = 'High'
            impact['reputation_impact'] = 'Medium'
        elif 'email' in data_types:
            impact['reputation_impact'] = 'Medium'
    
    return impact

def verify_leak(leak):
    """
    Verify the authenticity of a leak.
    
    Args:
        leak (LeakItem): The leak to verify
        
    Returns:
        dict: Verification results
    """
    verification = {
        'status': 'unverified',
        'confidence': 0,
        'verification_method': 'manual'
    }
    
    # Simple verification logic
    if leak.data_content and len(leak.data_content) > 100:
        verification['confidence'] = 50
        verification['status'] = 'pending_review'
    
    # If associated with a known breach, higher confidence
    if leak.associated_breach_id:
        verification['confidence'] = 75
        verification['status'] = 'likely_authentic'
        verification['verification_method'] = 'breach_association'
    
    return verification

def enrich_leak_data(leak):
    """
    Enrich leak data with verification and context.
    
    Args:
        leak (LeakItem): The leak to enrich
        
    Returns:
        dict: Enriched leak data
    """
    try:
        verification = verify_leak(leak)
        
        enriched_data = {
            'id': leak.id,
            'source': leak.source,
            'data_content': leak.data_content[:500] + '...' if leak.data_content and len(leak.data_content) > 500 else leak.data_content,
            'verification_status': leak.verification_status,
            'associated_breach_id': leak.associated_breach_id,
            'created_at': leak.created_at.isoformat(),
            'verification_results': verification,
            'risk_level': 'Low'  # Default risk level
        }
        
        # Adjust risk level based on verification
        if verification['confidence'] > 70:
            enriched_data['risk_level'] = 'High'
        elif verification['confidence'] > 40:
            enriched_data['risk_level'] = 'Medium'
        
        return enriched_data
    except Exception as e:
        logging.error(f"Error enriching leak data: {e}")
        return None

if __name__ == "__main__":
    # Test the enrichment functions
    sample_breach = BreachItem(
        name="Test Breach",
        description="A test breach for enrichment",
        affected_organizations="Test Org",
        data_types_exposed="email,password",
        records_affected=100000,
        discovery_date=datetime.utcnow(),
        disclosure_date=datetime.utcnow(),
        source_url="http://example.com"
    )
    
    enriched = enrich_breach_data(sample_breach)
    print("Enriched Breach Data:", enriched)
