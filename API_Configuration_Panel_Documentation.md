# API Configuration Panel Documentation

## Overview

The API Configuration Panel is a dynamic admin interface that allows users to integrate third-party APIs seamlessly without manual code changes. The system automatically restructures backend pipelines, manages data flow to user panels, and maintains a central vault for breach/leak data with advanced search and filtering capabilities.

## Features

### 1. Dynamic API Integration

- **Add Any 3rd-Party API**: Supports integration with various APIs including Google, Meta, YouTube, OpenAI, Wayback, HIBP, and more.
- **Auto-Integration**: When a new API is added via the admin panel, the system automatically:
  - Imports the API connector module
  - Instantiates the connector with provided configuration
  - Restructures backend pipelines dynamically
  - Registers new routes based on API capabilities (e.g., breach fetching, leak fetching)
- **No Manual Rebuild Required**: All changes are applied in real-time without needing to restart the application or modify code.

### 2. Data Flow Control

- **Direct Control from Admin Panel**: Administrators can control data flow directly from the panel.
- **Push to User Panel**: Integrated APIs can push data to user dashboards automatically.
- **Central Vault Management**: All breach and leak data is stored in a central vault with search and metadata filtering.

### 3. Central Vault for Breach/Leak Data

- **Search Capabilities**: Full-text search across breach and leak data.
- **Metadata Filtering**: Filter by various metadata such as risk level, date, source, etc.
- **Integration with API Data**: Data from integrated APIs is automatically stored in the vault.

## Usage

### Adding a New API

1. Navigate to the Admin API Configuration Panel (`/admin/api_panel`).
2. In the "Integrate New API" section:
   - Enter the API name (e.g., `wayback`, `openai`, `whois`, `hibp`).
   - Provide the configuration in JSON format (e.g., `{"api_key": "your_key", "other_param": "value"}`).
3. Click "Add API". The system will automatically integrate the API and restructure pipelines.

### Testing an API

1. In the "Test API" section:
   - Enter the API name.
   - Provide a test query.
2. Click "Test API" to verify the integration.

### Pushing Data to User Panel

1. In the "Push Data to User Panel" section:
   - Enter the User ID.
   - Provide the API data in JSON format.
2. Click "Push Data" to send data to the specified user's panel.

### Managing Integrated APIs

- View all integrated APIs in the "Integrated APIs" section.
- Enable/Disable APIs using the toggle buttons.
- Remove APIs using the delete buttons.

### API Key Management

- Add and manage API keys in the "API Key Management" section.
- View existing API keys with masked values for security.

## Admin Panel Upload Functionality

### Overview

The Admin Panel includes a file upload system that supports various file types, auto-scans for malware, extracts partial information, tags risk levels, and flags visibility.

### Supported File Types

- .csv
- .json
- .zip
- .sql
- .7z
- And other common file formats

### Features

1. **Auto-Scan Malware**: Files are automatically scanned for malware upon upload.
2. **Extract Partial Information**: Only metadata and partial content are extracted and stored; full files are not retained.
3. **Auto-Tag Risk Level**:
   - Low: Safe files
   - Medium: Potentially risky files
   - Critical: High-risk files
4. **Flag as Public or Private**: Administrators can set visibility for each upload.
5. **Tracking**: All uploads are tracked with uploader ID and upload time.

### Usage

1. Navigate to the Admin API Configuration Panel.
2. Use the file upload form to select and upload files.
3. The system will automatically scan, extract, tag, and store the file information.
4. View uploaded files in the uploads list with details including risk level, visibility, and metadata.

## Technical Implementation

- **Backend**: Routes are defined in `central_api_manager.py` with dynamic pipeline restructuring.
- **Frontend**: HTML template at `templates/admin_api_panel.html` with JavaScript for interactions.
- **Integration**: Uses existing API integration modules in `api_integrations/` directory.
- **Vault**: Breach/leak data is managed by `breach_leak_vault.py`.

## Security Considerations

- API keys are stored securely and masked in the UI.
- File uploads are scanned for malware before processing.
- Only partial information is stored to minimize risk.
- Access to the admin panel is restricted to authorized users.

## Troubleshooting

- If an API fails to integrate, check the module name and configuration format.
- For upload issues, ensure the file type is supported and the file is not corrupted.
- If data is not pushing to user panels, verify the user ID and data format.

This documentation covers the key features and usage of the API Configuration Panel and upload functionality.
