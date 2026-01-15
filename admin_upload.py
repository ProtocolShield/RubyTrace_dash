from flask import Flask, request, jsonify, render_template
import os
import datetime
import magic
import zipfile
import py7zr
from central_api_manager import central_api

app = Flask(__name__)
app.register_blueprint(central_api)

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
uploads = []
dynamic_apis = {}
vault = []

def scan_for_malware(file_path):
    # Placeholder for malware scan (integrate VirusTotal/ClamAV as needed)
    return "clean"

def extract_partial_info(file_path, file_type):
    try:
        if 'zip' in file_type:
            with zipfile.ZipFile(file_path) as z:
                return z.namelist()[:2]
        elif '7z' in file_type:
            with py7zr.SevenZipFile(file_path, mode='r') as z:
                return z.getnames()[:2]
        elif 'csv' in file_type or 'json' in file_type or 'sql' in file_type:
            lines = []
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for _ in range(5):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line.strip())
            return lines
        else:
            return "meta"
    except Exception as e:
        return f"Error extracting info: {str(e)}"

def tag_risk(scan_result, file_type):
    if scan_result != "clean":
        return "Critical"
    if 'sql' in file_type or 'zip' in file_type or '7z' in file_type:
        return "Medium"
    return "Low"

@app.route('/admin/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        uploader_id = request.form['uploader_id']
        public_flag = request.form.get('public', 'false') == 'true'
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        file_type = magic.from_file(file_path, mime=True) + '|' + os.path.splitext(file.filename)[1]
        scan_result = scan_for_malware(file_path)
        partial_info = extract_partial_info(file_path, file_type)
        risk_level = tag_risk(scan_result, file_type)
        upload_record = {
            'filename': file.filename,
            'uploader_id': uploader_id,
            'upload_time': datetime.datetime.now().isoformat(),
            'risk_level': risk_level,
            'public': public_flag,
            'partial_info': partial_info
        }
        uploads.append(upload_record)
        return jsonify({'success': True, 'record': upload_record})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/admin/uploads', methods=['GET'])
def list_uploads():
    return jsonify({'uploads': uploads})

@app.route('/admin/add_api', methods=['POST'])
def add_api():
    data = request.json
    api_name = data['api_name']
    config = data['config']
    try:
        module = __import__(f"api_integrations.{api_name}_integration", fromlist=['Connector'])
        connector = module.Connector(config)
        dynamic_apis[api_name] = connector
        return jsonify({'success': True, 'message': f'{api_name} added.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/admin/query_api', methods=['POST'])
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

@app.route('/vault/add', methods=['POST'])
def add_vault():
    data = request.json
    data['timestamp'] = datetime.datetime.now().isoformat()
    vault.append(data)
    return jsonify({'success': True})

@app.route('/vault/search', methods=['GET'])
def search_vault():
    keyword = request.args.get('keyword', '')
    results = [item for item in vault if keyword.lower() in str(item.get('metadata', '')).lower()]
    return jsonify({'results': results})

@app.route('/admin/panel')
def admin_panel():
    return render_template('admin_panel.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))