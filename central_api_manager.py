from flask import Blueprint, request, jsonify, render_template
import importlib
import datetime
from api_integrations.breach_leak_vault import vault as breach_vault
from file_upload_system import upload_manager

central_api = Blueprint('central_api', __name__)

# Store API connectors and configs
dynamic_apis = {}

# Central vault for breach/leak data (integrated with breach_vault)
# vault = []  # Removed, using breach_vault instead

@central_api.route('/admin/add_api', methods=['POST'])
def add_api():
    data = request.json
    api_name = data['api_name']
    config = data['config']
    try:
        module = importlib.import_module(f"api_integrations.{api_name}_integration")
        # Get the Connector class from the module
        connector_class = getattr(module, 'Connector')
        connector = connector_class(config)
        dynamic_apis[api_name] = connector
        # Auto-restructure backend pipelines: register new routes dynamically
        _restructure_pipelines(api_name, connector)
        return jsonify({'success': True, 'message': f'{api_name} added and pipelines restructured.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

def _restructure_pipelines(api_name, connector):
    """Dynamically restructure backend pipelines for new API"""
    # Example: Add new routes based on API capabilities
    if hasattr(connector, 'fetch_breaches'):
        # Register a new route for breach fetching
        @central_api.route(f'/admin/{api_name}/fetch_breaches', methods=['POST'])
        def fetch_breaches():
            data = request.json
            query = data.get('query', '')
            try:
                results = connector.fetch_breaches(query)
                # Store in vault
                for result in results:
                    breach_vault.add_breach(result)
                return jsonify({'success': True, 'results': results})
            except Exception as e:
                return jsonify({'error': str(e)}), 400

    if hasattr(connector, 'fetch_leaks'):
        @central_api.route(f'/admin/{api_name}/fetch_leaks', methods=['POST'])
        def fetch_leaks():
            data = request.json
            query = data.get('query', '')
            try:
                results = connector.fetch_leaks(query)
                for result in results:
                    breach_vault.add_leak(result)
                return jsonify({'success': True, 'results': results})
            except Exception as e:
                return jsonify({'error': str(e)}), 400

@central_api.route('/admin/query_api', methods=['POST'])
def query_api():
    data = request.json
    api_name = data['api_name']
    query = data['query']
    if api_name in dynamic_apis:
        try:
            result = dynamic_apis[api_name].fetch(query)
            return jsonify({'result': result})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    return jsonify({'error': 'API not found'}), 404

@central_api.route('/admin/push_to_user_panel', methods=['POST'])
def push_to_user_panel():
    data = request.json
    user_id = data['user_id']
    api_data = data['api_data']
    # Logic to push data to user panel (e.g., update user dashboard)
    # This is a placeholder; integrate with user routes or dashboard
    return jsonify({'success': True, 'message': f'Data pushed to user {user_id}'})

@central_api.route('/admin/test_api', methods=['POST'])
def test_api():
    data = request.json
    api_name = data['api_name']
    test_query = data.get('test_query', 'test')
    if api_name in dynamic_apis:
        try:
            result = dynamic_apis[api_name].fetch(test_query)
            return jsonify({'success': True, 'test_result': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    return jsonify({'error': 'API not found'}), 404

@central_api.route('/vault/add', methods=['POST'])
def add_to_vault():
    data = request.json
    data['timestamp'] = datetime.datetime.now().isoformat()
    # Use breach_vault instead of local vault
    if 'breach' in data:
        breach_vault.add_breach(data['breach'])
    elif 'leak' in data:
        breach_vault.add_leak(data['leak'])
    return jsonify({'success': True})

@central_api.route('/vault/search', methods=['GET'])
def search_vault():
    query = request.args.get('query', '')
    filters = request.args.to_dict()
    filters.pop('query', None)  # Remove query from filters
    try:
        results = breach_vault.search_breaches(query, filters)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@central_api.route('/vault/search_leaks', methods=['GET'])
def search_leaks():
    query = request.args.get('query', '')
    filters = request.args.to_dict()
    filters.pop('query', None)
    try:
        results = breach_vault.search_leaks(query, filters)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@central_api.route('/vault/stats', methods=['GET'])
def get_vault_stats():
    try:
        stats = breach_vault.get_vault_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@central_api.route('/admin/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    uploader_id = request.form.get('uploader_id', None)
    is_public = request.form.get('is_public', 'false').lower() == 'true'
    try:
        result = upload_manager.process_upload(file, uploader_id, is_public)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@central_api.route('/admin/api_panel')
def api_panel():
    return render_template('admin_api_panel.html')

# API configuration routes
@central_api.route('/api/config/integrated_apis', methods=['GET'])
def get_integrated_apis():
    # Return the list of integrated APIs
    return jsonify({'success': True, 'integrated_apis': dynamic_apis})

@central_api.route('/api/config/integrate_api', methods=['POST'])
def integrate_api():
    data = request.json
    api_name = data['api_name']
    config = data['config']
    try:
        module = importlib.import_module(f"api_integrations.{api_name}_integration")
        connector_class = getattr(module, 'Connector')
        connector = connector_class(config)
        dynamic_apis[api_name] = connector
        return jsonify({'success': True, 'message': f'{api_name} integrated.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@central_api.route('/api/config/integrate_api/<service>', methods=['DELETE'])
def remove_integrated_api(service):
    if service in dynamic_apis:
        del dynamic_apis[service]
        return jsonify({'success': True, 'message': f'{service} removed.'})
    return jsonify({'success': False, 'error': 'API not found'}), 404

@central_api.route('/api/config/api_keys', methods=['GET'])
def get_api_keys():
    # Return the list of API keys
    # This is a placeholder; integrate with database
    return jsonify([])
