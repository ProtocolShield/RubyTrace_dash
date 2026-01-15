// Tools & Scripts JavaScript

// API URLs
const TOOLS_API_URL = '/api/tools';
const UPLOADS_API_URL = '/api/admin/uploads';

// DOM elements
const toolsContainer = document.getElementById('tools-container');
const refreshToolsBtn = document.getElementById('refresh-tools-btn');
const addToolBtn = document.getElementById('add-tool-btn');
const uploadToolBtn = document.getElementById('upload-tool-btn');
const toolsRiskFilter = document.getElementById('tools-risk-filter');
const toolsSearch = document.getElementById('tools-search');
const toolsLimit = document.getElementById('tools-limit');
const toolsFilterBtn = document.getElementById('tools-filter-btn');

// Statistics elements
const totalTools = document.getElementById('total-tools');
const highRiskTools = document.getElementById('high-risk-tools');
const downloadedTools = document.getElementById('downloaded-tools');

// Current state
let currentTools = [];
let filteredTools = [];

// Initialize Tools & Scripts
function initToolsScripts() {
    console.log('Initializing Tools & Scripts...');
    
    // Add event listeners
    if (refreshToolsBtn) refreshToolsBtn.addEventListener('click', loadTools);
    if (addToolBtn) addToolBtn.addEventListener('click', showAddToolModal);
    if (uploadToolBtn) uploadToolBtn.addEventListener('click', showUploadModal);
    if (toolsFilterBtn) toolsFilterBtn.addEventListener('click', applyToolsFilters);
    
    // Add search functionality
    if (toolsSearch) {
        toolsSearch.addEventListener('input', debounce(applyToolsFilters, 300));
    }
    
    // Load initial data
    loadTools();
}

// Load tools from API
async function loadTools() {
    try {
        showLoading(toolsContainer);
        
        const limit = toolsLimit ? toolsLimit.value : 50;
        const response = await fetch(`${TOOLS_API_URL}?limit=${limit}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        currentTools = await response.json();
        filteredTools = [...currentTools];
        
        updateToolsStatistics();
        renderTools();
        
    } catch (error) {
        console.error('Error loading tools:', error);
        showError(toolsContainer, 'Failed to load tools. Please try again.');
    }
}

// Apply filters to tools
function applyToolsFilters() {
    const riskFilter = toolsRiskFilter ? toolsRiskFilter.value : '';
    const searchTerm = toolsSearch ? toolsSearch.value.toLowerCase() : '';
    
    filteredTools = currentTools.filter(tool => {
        // Risk filter
        if (riskFilter && tool.risk_level !== riskFilter) {
            return false;
        }
        
        // Search filter
        if (searchTerm) {
            const searchText = `${tool.name} ${tool.description || ''}`.toLowerCase();
            if (!searchText.includes(searchTerm)) {
                return false;
            }
        }
        
        return true;
    });
    
    renderTools();
}

// Update tools statistics
function updateToolsStatistics() {
    const stats = {
        total: currentTools.length,
        highRisk: 0,
        downloaded: 0
    };
    
    currentTools.forEach(tool => {
        if (tool.risk_level === 'high') {
            stats.highRisk++;
        }
        if (tool.file_path) {
            stats.downloaded++;
        }
    });
    
    if (totalTools) totalTools.textContent = stats.total;
    if (highRiskTools) highRiskTools.textContent = stats.highRisk;
    if (downloadedTools) downloadedTools.textContent = stats.downloaded;
}

// Render tools in the container
function renderTools() {
    if (!toolsContainer) return;
    
    if (filteredTools.length === 0) {
        toolsContainer.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-tools fa-3x mb-3"></i>
                <p>No tools found matching your criteria.</p>
            </div>
        `;
        return;
    }
    
    const toolsHtml = filteredTools.map(tool => `
        <div class="card mb-3 tool-card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                    ${tool.risk_level ? `<span class="badge bg-${getRiskColor(tool.risk_level)} me-2">${tool.risk_level}</span>` : ''}
                    <strong>${tool.name}</strong>
                </h6>
                <div>
                    ${tool.file_path ? `<span class="badge bg-success me-2">Downloaded</span>` : ''}
                    <button class="btn btn-sm btn-outline-primary" onclick="viewToolDetails('${tool.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </div>
            <div class="card-body">
                <p class="card-text text-muted">
                    ${tool.description ? tool.description.substring(0, 200) + '...' : 'No description available'}
                </p>
                <div class="row">
                    <div class="col-md-6">
                        <small class="text-muted">
                            <i class="fas fa-clock me-1"></i>
                            Added: ${formatDate(tool.created_at)}
                        </small>
                    </div>
                    <div class="col-md-6">
                        <small class="text-muted">
                            <i class="fas fa-shield-alt me-1"></i>
                            Risk: ${tool.risk_level || 'Unknown'}
                        </small>
                    </div>
                </div>
                ${tool.source_name ? `
                <div class="mt-2">
                    <small class="text-muted">
                        <i class="fas fa-download me-1"></i>
                        Source: ${tool.source_name}
                    </small>
                </div>
                ` : ''}
            </div>
            <div class="card-footer">
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">
                        <i class="fas fa-lock me-1"></i>
                        Private Tool
                    </small>
                    <div>
                        ${tool.url ? `
                        <a href="${tool.url}" target="_blank" class="btn btn-sm btn-outline-secondary me-2">
                            <i class="fas fa-external-link-alt me-1"></i> View Source
                        </a>
                        ` : ''}
                        ${tool.file_path ? `
                        <button class="btn btn-sm btn-outline-success" onclick="downloadTool('${tool.id}')">
                            <i class="fas fa-download me-1"></i> Download
                        </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    toolsContainer.innerHTML = toolsHtml;
}

// Get risk color for badges
function getRiskColor(riskLevel) {
    if (!riskLevel) return 'secondary';
    
    const colors = {
        'high': 'danger',
        'medium': 'warning',
        'low': 'success'
    };
    
    return colors[riskLevel.toLowerCase()] || 'secondary';
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch (error) {
        return 'Invalid date';
    }
}

// Show tool details modal
function viewToolDetails(toolId) {
    const tool = currentTools.find(t => t.id === parseInt(toolId));
    if (!tool) return;
    
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="tool-details-modal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            ${tool.risk_level ? `<span class="badge bg-${getRiskColor(tool.risk_level)} me-2">${tool.risk_level}</span>` : ''}
                            ${tool.name}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="text-muted">${tool.description || 'No description available'}</p>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <strong>Risk Level:</strong> ${tool.risk_level || 'Unknown'}<br>
                                <strong>Added:</strong> ${formatDate(tool.created_at)}<br>
                                <strong>Source:</strong> ${tool.source_name || 'Unknown'}
                            </div>
                            <div class="col-md-6">
                                <strong>File Path:</strong> ${tool.file_path || 'Not downloaded'}<br>
                                <strong>Private:</strong> ${tool.is_private ? 'Yes' : 'No'}
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            ${tool.url ? `
                            <a href="${tool.url}" target="_blank" class="btn btn-primary me-2">
                                <i class="fas fa-external-link-alt me-1"></i> View Source
                            </a>
                            ` : ''}
                            ${tool.file_path ? `
                            <button class="btn btn-success" onclick="downloadTool('${tool.id}')">
                                <i class="fas fa-download me-1"></i> Download Tool
                            </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('tool-details-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('tool-details-modal'));
    modal.show();
    
    // Clean up modal after hiding
    document.getElementById('tool-details-modal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Download tool file
async function downloadTool(toolId) {
    try {
        const response = await fetch(`${TOOLS_API_URL}/${toolId}/download`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tool_${toolId}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showSuccess('Tool downloaded successfully!');
        
    } catch (error) {
        console.error('Error downloading tool:', error);
        showError('Failed to download tool. Please try again.');
    }
}

// Show add tool modal
function showAddToolModal() {
    const modalHtml = `
        <div class="modal fade" id="add-tool-modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Add New Tool</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="add-tool-form">
                            <div class="mb-3">
                                <label for="tool-name-input" class="form-label">Tool Name</label>
                                <input type="text" class="form-control" id="tool-name-input" placeholder="Tool name" required>
                            </div>
                            <div class="mb-3">
                                <label for="tool-description-input" class="form-label">Description</label>
                                <textarea class="form-control" id="tool-description-input" rows="3" placeholder="Tool description"></textarea>
                            </div>
                            <div class="mb-3">
                                <label for="tool-url-input" class="form-label">Source URL</label>
                                <input type="url" class="form-control" id="tool-url-input" placeholder="https://example.com/tool">
                            </div>
                            <div class="mb-3">
                                <label for="tool-source-input" class="form-label">Source Name</label>
                                <input type="text" class="form-control" id="tool-source-input" placeholder="Source name">
                            </div>
                            <div class="mb-3">
                                <label for="tool-risk-input" class="form-label">Risk Level</label>
                                <select class="form-select" id="tool-risk-input">
                                    <option value="">Select risk level</option>
                                    <option value="high">High</option>
                                    <option value="medium">Medium</option>
                                    <option value="low">Low</option>
                                </select>
                            </div>
                            <div class="form-check form-switch mb-3">
                                <input class="form-check-input" type="checkbox" id="tool-private-input" checked>
                                <label class="form-check-label" for="tool-private-input">Private Tool</label>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="save-tool-btn">Save Tool</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('add-tool-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('add-tool-modal'));
    modal.show();
    
    // Add save event listener
    document.getElementById('save-tool-btn').addEventListener('click', saveTool);
    
    // Clean up modal after hiding
    document.getElementById('add-tool-modal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Save new tool
async function saveTool() {
    const toolData = {
        name: document.getElementById('tool-name-input').value,
        description: document.getElementById('tool-description-input').value,
        url: document.getElementById('tool-url-input').value,
        source_name: document.getElementById('tool-source-input').value,
        risk_level: document.getElementById('tool-risk-input').value,
        is_private: document.getElementById('tool-private-input').checked
    };
    
    try {
        const response = await fetch(TOOLS_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(toolData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Close modal and reload data
        bootstrap.Modal.getInstance(document.getElementById('add-tool-modal')).hide();
        loadTools();
        
        // Show success message
        showSuccess('Tool added successfully!');
        
    } catch (error) {
        console.error('Error saving tool:', error);
        showError('Failed to save tool. Please try again.');
    }
}

// Show upload modal
function showUploadModal() {
    const modalHtml = `
        <div class="modal fade" id="upload-tool-modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Upload Tool File</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="upload-tool-form" enctype="multipart/form-data">
                            <div class="mb-3">
                                <label for="tool-file-input" class="form-label">Tool File</label>
                                <input type="file" class="form-control" id="tool-file-input" required>
                                <div class="form-text">Select a tool file to upload (ZIP, RAR, EXE, etc.)</div>
                            </div>
                            <div class="mb-3">
                                <label for="upload-risk-input" class="form-label">Risk Level</label>
                                <select class="form-select" id="upload-risk-input">
                                    <option value="low">Low</option>
                                    <option value="medium" selected>Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <div class="form-check form-switch mb-3">
                                <input class="form-check-input" type="checkbox" id="upload-public-input">
                                <label class="form-check-label" for="upload-public-input">Public Tool</label>
                                <div class="form-text">Uncheck to keep tool private</div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="upload-tool-btn">Upload Tool</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('upload-tool-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('upload-tool-modal'));
    modal.show();
    
    // Add upload event listener
    document.getElementById('upload-tool-btn').addEventListener('click', uploadTool);
    
    // Clean up modal after hiding
    document.getElementById('upload-tool-modal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Upload tool file
async function uploadTool() {
    const fileInput = document.getElementById('tool-file-input');
    const riskLevel = document.getElementById('upload-risk-input').value;
    const isPublic = document.getElementById('upload-public-input').checked;
    
    if (!fileInput.files[0]) {
        showError('Please select a file to upload.');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('risk_level', riskLevel);
    formData.append('is_public', isPublic);
    
    try {
        const response = await fetch(UPLOADS_API_URL, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Close modal and reload data
        bootstrap.Modal.getInstance(document.getElementById('upload-tool-modal')).hide();
        loadTools();
        
        // Show success message
        showSuccess('Tool file uploaded successfully!');
        
    } catch (error) {
        console.error('Error uploading tool:', error);
        showError('Failed to upload tool. Please try again.');
    }
}

// Utility functions
function showLoading(container) {
    if (container) {
        container.innerHTML = `
            <div class="d-flex justify-content-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    }
}

function showError(container, message) {
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }
}

function showSuccess(message) {
    // Create a temporary success alert
    const alertHtml = `
        <div class="alert alert-success alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999;" role="alert">
            <i class="fas fa-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert-success');
        if (alert) {
            alert.remove();
        }
    }, 3000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export for use in main app
window.initToolsScripts = initToolsScripts;
window.loadTools = loadTools; 