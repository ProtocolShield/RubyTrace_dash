"""
OpenAI API Integration
Provides AI-powered analysis and text processing capabilities
"""

import openai
import json
from datetime import datetime
from typing import Dict, Any, List
from . import APIIntegration

class OpenAIIntegration(APIIntegration):
    """OpenAI API integration for AI-powered analysis"""

    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        super().__init__(api_key, config)
        self.name = "openai"
        openai.api_key = api_key
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.max_tokens = config.get('max_tokens', 1000)
        self.temperature = config.get('temperature', 0.7)

        self.rate_limits = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'burst_limit': 10
        }

    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                timeout=10
            )
            return response is not None
        except Exception as e:
            print(f"OpenAI connection test failed: {e}")
            return False

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            "text_analysis",
            "sentiment_analysis",
            "entity_extraction",
            "risk_assessment",
            "content_classification",
            "threat_analysis",
            "data_pattern_recognition"
        ]

    def execute_query(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query against OpenAI API"""
        if query_type == "text_analysis":
            return self.analyze_text(params.get('text', ''), params.get('analysis_type', 'general'))
        elif query_type == "sentiment_analysis":
            return self.analyze_sentiment(params.get('text', ''))
        elif query_type == "entity_extraction":
            return self.extract_entities(params.get('text', ''))
        elif query_type == "risk_assessment":
            return self.assess_risk(params.get('content', ''), params.get('context', ''))
        elif query_type == "threat_analysis":
            return self.analyze_threat(params.get('data', ''))
        else:
            return {'error': f'Unknown query type: {query_type}'}

    def analyze_text(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze text using OpenAI"""
        try:
            prompts = {
                "general": f"Analyze the following text and provide insights: {text[:2000]}",
                "security": f"Analyze this text for security implications and potential threats: {text[:2000]}",
                "privacy": f"Analyze this text for privacy concerns and data exposure risks: {text[:2000]}",
                "technical": f"Analyze this technical content and extract key information: {text[:2000]}"
            }

            prompt = prompts.get(analysis_type, prompts["general"])

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=30
            )

            analysis = response.choices[0].message.content.strip()

            return {
                'text_length': len(text),
                'analysis_type': analysis_type,
                'analysis': analysis,
                'model_used': self.model,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else None
            }

        except Exception as e:
            return {'error': f'Failed to analyze text: {str(e)}'}

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        try:
            prompt = f"""Analyze the sentiment of the following text. Provide:
1. Overall sentiment (positive, negative, neutral)
2. Confidence score (0-1)
3. Key emotional indicators
4. Any concerning language or red flags

Text: {text[:1500]}"""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
                timeout=30
            )

            analysis = response.choices[0].message.content.strip()

            return {
                'text': text[:100],
                'sentiment_analysis': analysis,
                'model_used': self.model
            }

        except Exception as e:
            return {'error': f'Failed to analyze sentiment: {str(e)}'}

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text"""
        try:
            prompt = f"""Extract and categorize entities from the following text. Include:
- People names
- Organizations
- Locations
- Email addresses
- Phone numbers
- URLs
- Technical terms
- Sensitive data patterns

Text: {text[:2000]}"""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.2,
                timeout=30
            )

            entities = response.choices[0].message.content.strip()

            return {
                'text_length': len(text),
                'extracted_entities': entities,
                'model_used': self.model
            }

        except Exception as e:
            return {'error': f'Failed to extract entities: {str(e)}'}

    def assess_risk(self, content: str, context: str = "") -> Dict[str, Any]:
        """Assess risk level of content"""
        try:
            prompt = f"""Assess the risk level of the following content in the context of privacy and security:

Context: {context}
Content: {content[:1500]}

Provide:
1. Risk level (Low, Medium, High, Critical)
2. Risk factors identified
3. Recommended actions
4. Confidence in assessment"""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.3,
                timeout=30
            )

            assessment = response.choices[0].message.content.strip()

            return {
                'content_type': 'text',
                'risk_assessment': assessment,
                'context': context,
                'model_used': self.model
            }

        except Exception as e:
            return {'error': f'Failed to assess risk: {str(e)}'}

    def analyze_threat(self, data: str) -> Dict[str, Any]:
        """Analyze potential threats in data"""
        try:
            prompt = f"""Analyze the following data for potential security threats and privacy concerns:

{data[:2000]}

Identify:
1. Potential threat indicators
2. Privacy violations
3. Security vulnerabilities
4. Recommended mitigation steps"""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.4,
                timeout=30
            )

            analysis = response.choices[0].message.content.strip()

            return {
                'data_type': 'threat_analysis',
                'threat_analysis': analysis,
                'model_used': self.model
            }

        except Exception as e:
            return {'error': f'Failed to analyze threat: {str(e)}'}

class Connector:
    def __init__(self, config):
        self.config = config

    def fetch(self, query):
        # Example: Call OpenAI API (pseudo)
        return {'response': f'OpenAI result for {query}'}
