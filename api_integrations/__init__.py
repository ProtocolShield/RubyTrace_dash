"""
Dynamic API Integration System
Supports auto-integration of 3rd-party APIs with automatic pipeline restructuring
"""

import importlib
import json
import logging
import os
import threading
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class APIIntegration(ABC):
    """Base class for all API integrations"""

    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        self.api_key = api_key
        self.config = config or {}
        self.name = self.__class__.__name__.replace('Integration', '').lower()
        self.base_url = ""
        self.rate_limits = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'burst_limit': 10
        }

    @abstractmethod
    def test_connection(self) -> bool:
        """Test API connection and authentication"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this API provides"""
        pass

    @abstractmethod
    def execute_query(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query against the API"""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this integration"""
        return {
            'name': self.name,
            'capabilities': self.get_capabilities(),
            'rate_limits': self.rate_limits,
            'config_options': list(self.config.keys()),
            'last_tested': datetime.utcnow().isoformat()
        }

class APIIntegrationManager:
    """Manages dynamic loading and execution of API integrations"""

    def __init__(self):
        self.integrations: Dict[str, APIIntegration] = {}
        self.integration_configs: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self.pipeline_callbacks: List[callable] = []
        self.config_file = os.path.join(os.path.dirname(__file__), 'api_configs.json')
        self._load_persisted_configs()

    def register_integration(self, integration_class: type, api_key: str, config: Dict[str, Any] = None) -> bool:
        """Register a new API integration dynamically"""
        try:
            integration = integration_class(api_key, config)
            integration_name = integration.name

            # Test the connection
            if not integration.test_connection():
                self.logger.error(f"Failed to connect to {integration_name} API")
                return False

            self.integrations[integration_name] = integration
            self.integration_configs[integration_name] = {
                'api_key': api_key,
                'config': config or {},
                'registered_at': datetime.utcnow().isoformat(),
                'capabilities': integration.get_capabilities()
            }

            self.logger.info(f"Successfully registered {integration_name} integration")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register integration: {e}")
            return False

    def get_integration(self, name: str) -> Optional[APIIntegration]:
        """Get an integration instance by name"""
        return self.integrations.get(name)

    def list_integrations(self) -> Dict[str, Dict[str, Any]]:
        """List all registered integrations with their metadata"""
        result = {}
        for name, integration in self.integrations.items():
            result[name] = integration.get_metadata()
            result[name]['config'] = self.integration_configs[name]
        return result

    def execute_query(self, integration_name: str, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query on a specific integration"""
        integration = self.get_integration(integration_name)
        if not integration:
            return {'error': f'Integration {integration_name} not found'}

        try:
            return integration.execute_query(query_type, params)
        except Exception as e:
            self.logger.error(f"Error executing query on {integration_name}: {e}")
            return {'error': str(e)}

    def remove_integration(self, name: str) -> bool:
        """Remove an integration"""
        if name in self.integrations:
            del self.integrations[name]
            del self.integration_configs[name]
            self._save_persisted_configs()
            self._trigger_pipeline_callbacks('remove', name)
            self.logger.info(f"Removed integration: {name}")
            return True
        return False

    def add_pipeline_callback(self, callback: callable) -> None:
        """Add a callback function to be called when integrations change"""
        self.pipeline_callbacks.append(callback)

    def remove_pipeline_callback(self, callback: callable) -> None:
        """Remove a pipeline callback"""
        if callback in self.pipeline_callbacks:
            self.pipeline_callbacks.remove(callback)

    def _trigger_pipeline_callbacks(self, action: str, integration_name: str) -> None:
        """Trigger all pipeline callbacks"""
        for callback in self.pipeline_callbacks:
            try:
                callback(action, integration_name)
            except Exception as e:
                self.logger.error(f"Error in pipeline callback: {e}")

    def _load_persisted_configs(self) -> None:
        """Load persisted API configurations"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    configs = json.load(f)
                    for name, config in configs.items():
                        self._restore_integration(name, config)
        except Exception as e:
            self.logger.error(f"Error loading persisted configs: {e}")

    def _save_persisted_configs(self) -> None:
        """Save current API configurations to disk"""
        try:
            configs_to_save = {}
            for name, config in self.integration_configs.items():
                configs_to_save[name] = {
                    'api_key': config['api_key'],
                    'config': config['config'],
                    'class_name': self.integrations[name].__class__.__name__,
                    'module_name': self.integrations[name].__class__.__module__
                }

            with open(self.config_file, 'w') as f:
                json.dump(configs_to_save, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving persisted configs: {e}")

    def _restore_integration(self, name: str, config: Dict[str, Any]) -> None:
        """Restore an integration from persisted config"""
        try:
            module_name = config.get('module_name', 'api_integrations')
            class_name = config.get('class_name')

            if not class_name:
                return

            # Import the module and get the class
            module = importlib.import_module(module_name)
            integration_class = getattr(module, class_name)

            # Register the integration
            self.register_integration(
                integration_class,
                config['api_key'],
                config['config']
            )
        except Exception as e:
            self.logger.error(f"Error restoring integration {name}: {e}")

    def register_integration_by_name(self, integration_name: str, api_key: str, config: Dict[str, Any] = None) -> bool:
        """Register an integration by name (dynamically loads the class)"""
        try:
            # Try to find the integration class in the api_integrations module
            module = importlib.import_module('api_integrations')
            class_name = f"{integration_name.title()}Integration"
            integration_class = getattr(module, class_name, None)

            if not integration_class:
                self.logger.error(f"Integration class {class_name} not found")
                return False

            success = self.register_integration(integration_class, api_key, config)
            if success:
                self._save_persisted_configs()
                self._trigger_pipeline_callbacks('add', integration_name)
            return success

        except Exception as e:
            self.logger.error(f"Error registering integration by name: {e}")
            return False

    def remove_integration_by_name(self, integration_name: str) -> bool:
        """Remove an integration by name"""
        success = self.remove_integration(integration_name)
        if success:
            self._trigger_pipeline_callbacks('remove', integration_name)
        return success

    def get_available_integrations(self) -> List[str]:
        """Get list of available integration classes"""
        try:
            module = importlib.import_module('api_integrations')
            available = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, APIIntegration) and
                    obj != APIIntegration):
                    available.append(obj.__name__.replace('Integration', '').lower())
            return available
        except Exception as e:
            self.logger.error(f"Error getting available integrations: {e}")
            return []

    def test_integration_connection(self, name: str) -> bool:
        """Test connection for a specific integration"""
        integration = self.get_integration(name)
        if integration:
            return integration.test_connection()
        return False

    def get_integration_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all integrations"""
        status = {}
        for name, integration in self.integrations.items():
            status[name] = {
                'connected': self.test_integration_connection(name),
                'capabilities': integration.get_capabilities(),
                'last_tested': datetime.utcnow().isoformat(),
                'config': self.integration_configs[name]
            }
        return status

# Global instance
api_manager = APIIntegrationManager()
