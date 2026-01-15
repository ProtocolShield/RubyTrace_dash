// CVE Monitor JavaScript

// API URLs
const CVE_API_URL = '/api/cve';

// DOM elements
const cveContainer = document.getElementById('cve-container');
const refreshCveBtn = document.getElementById('refresh-cve-btn');
const addCveBtn = document.getElementById('add-cve-btn');
const cveSeverityFilter = document.getElementById('cve-severity-filter');
const cveSearch = document.getElementById('cve-search');
const cveLimit = document.getElementById('cve-limit');
const cveFilterBtn = document.getElementById('cve-filter-btn');

// Statistics elements
const criticalCount = document.getElementById('critical-count');
const highCount = document.getElementById('high-count');
const mediumCount = document.getElementById('medium-count');
const lowCount = document.getElementById('low-count');

// Current state
let currentCves = [];
let filteredCves = [];

// Initialize CVE Monitor
function initCveMonitor() {
    console.log('Initializing CVE Monitor...');
    
    // Add event listeners
    if (refreshCveBtn) refreshCveBtn.addEventListener('click', loadCves);
    if (addCveBtn) addCveBtn.addEventListener('click', showAddCveModal);
    if (cveFilterBtn) cveFilterBtn.addEventListener('click', applyCveFilters);
    
    // Add search functionality
    if (cveSearch) {
        cveSearch.addEventListener('input', debounce(applyCveFilters, 300));
    }
    
    // Load initial data
    loadCves();
}

// Load CVEs from API
async function loadCves() {
    try {
        showLoading(cveContainer);
        
        const limit = cveLimit ? cveLimit.value : 50;
        const response = await fetch(`${CVE_API_URL}?limit=${limit}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        currentCves = await response.json();
        filteredCves = [...currentCves];
        
        updateCveStatistics();
        renderCves();
        
    } catch (error) {
        console.error('Error loading CVEs:', error);
        showError(cveContainer, 'Failed to load CVEs. Please try again.');
    }
}

// Apply filters to CVEs
function applyCveFilters() {
    const severityFilter = cveSeverityFilter ? cveSeverityFilter.value : '';
    const searchTerm = cveSearch ? cveSearch.value.toLowerCase() : '';
    
    filteredCves = currentCves.filter(cve => {
        // Severity filter
        if (severityFilter && cve.severity !== severityFilter) {
            return false;
        }
        
        // Search filter
        if (searchTerm) {
            const searchText = `${cve.cve_id} ${cve.title || ''} ${cve.description || ''}`.toLowerCase();
            if (!searchText.includes(searchTerm)) {
                return false;
            }
        }
        
        return true;
    });
    
    renderCves();
}

// Update CVE statistics
function updateCveStatistics() {
    const stats = {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
    };
    
    currentCves.forEach(cve => {
        const severity = cve.severity ? cve.severity.toLowerCase() : 'unknown';
        if (stats.hasOwnProperty(severity)) {
            stats[severity]++;
        }
    });
    
    if (criticalCount) criticalCount.textContent = stats.critical;
    if (highCount) highCount.textContent = stats.high;
    if (mediumCount) mediumCount.textContent = stats.medium;
    if (lowCount) lowCount.textContent = stats.low;
}

// Render CVEs in the container
function renderCves() {
    if (!cveContainer) return;
    
    if (filteredCves.length === 0) {
        cveContainer.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-bug fa-3x mb-3"></i>
                <p>No CVEs found matching your criteria.</p>
            </div>
        `;
        return;
    }
    
    const cveHtml = filteredCves.map(cve => `
        <div class="card mb-3 cve-card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                    <span class="badge bg-${getSeverityColor(cve.severity)} me-2">${cve.severity || 'Unknown'}</span>
                    <strong>${cve.cve_id}</strong>
                </h6>
                <div>
                    ${cve.cvss ? `<span class="badge bg-secondary me-2">CVSS: ${cve.cvss}</span>` : ''}
                    <button class="btn btn-sm btn-outline-primary" onclick="viewCveDetails('${cve.cve_id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </div>
            <div class="card-body">
                <h6 class="card-title">${cve.title || 'No title available'}</h6>
                <p class="card-text text-muted">
                    ${cve.description ? cve.description.substring(0, 200) + '...' : 'No description available'}
                </p>
                <div class="row">
                    <div class="col-md-6">
                        <small class="text-muted">
                            <i class="fas fa-calendar me-1"></i>
                            Published: ${formatDate(cve.published_at)}
                        </small>
                    </div>
                    <div class="col-md-6">
                        <small class="text-muted">
                            <i class="fas fa-tags me-1"></i>
                            Tags: ${cve.tags || 'None'}
                        </small>
                    </div>
                </div>
                ${cve.affected_products ? `
                <div class="mt-2">
                    <small class="text-muted">
                        <i class="fas fa-cube me-1"></i>
                        Affected: ${cve.affected_products}
                    </small>
                </div>
                ` : ''}
            </div>
            <div class="card-footer">
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>
                        Added: ${formatDate(cve.created_at)}
                    </small>
                    ${cve.link ? `
                    <a href="${cve.link}" target="_blank" class="btn btn-sm btn-outline-secondary">
                        <i class="fas fa-external-link-alt me-1"></i> View Details
                    </a>
                    ` : ''}
                </div>
            </div>
        </div>
    `).join('');
    
    cveContainer.innerHTML = cveHtml;
}

// Get severity color for badges
function getSeverityColor(severity) {
    if (!severity) return 'secondary';
    
    const colors = {
        'critical': 'danger',
        'high': 'warning',
        'medium': 'info',
        'low': 'success'
    };
    
    return colors[severity.toLowerCase()] || 'secondary';
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

// Show CVE details modal
function viewCveDetails(cveId) {
    const cve = currentCves.find(c => c.cve_id === cveId);
    if (!cve) return;
    
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="cve-details-modal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <span class="badge bg-${getSeverityColor(cve.severity)} me-2">${cve.severity || 'Unknown'}</span>
                            ${cve.cve_id}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <h6>${cve.title || 'No title available'}</h6>
                        <p class="text-muted">${cve.description || 'No description available'}</p>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <strong>CVSS Score:</strong> ${cve.cvss || 'Not available'}<br>
                                <strong>Published:</strong> ${formatDate(cve.published_at)}<br>
                                <strong>Added:</strong> ${formatDate(cve.created_at)}
                            </div>
                            <div class="col-md-6">
                                <strong>Tags:</strong> ${cve.tags || 'None'}<br>
                                <strong>Affected Products:</strong> ${cve.affected_products || 'Not specified'}
                            </div>
                        </div>
                        
                        ${cve.link ? `
                        <div class="mt-3">
                            <a href="${cve.link}" target="_blank" class="btn btn-primary">
                                <i class="fas fa-external-link-alt me-1"></i> View Full Details
                            </a>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('cve-details-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('cve-details-modal'));
    modal.show();
    
    // Clean up modal after hiding
    document.getElementById('cve-details-modal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Show add CVE modal
function showAddCveModal() {
    const modalHtml = `
        <div class="modal fade" id="add-cve-modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Add New CVE</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="add-cve-form">
                            <div class="mb-3">
                                <label for="cve-id-input" class="form-label">CVE ID</label>
                                <input type="text" class="form-control" id="cve-id-input" placeholder="CVE-2024-XXXX" required>
                            </div>
                            <div class="mb-3">
                                <label for="cve-title-input" class="form-label">Title</label>
                                <input type="text" class="form-control" id="cve-title-input" placeholder="Brief description" required>
                            </div>
                            <div class="mb-3">
                                <label for="cve-description-input" class="form-label">Description</label>
                                <textarea class="form-control" id="cve-description-input" rows="3" placeholder="Detailed description"></textarea>
                            </div>
                            <div class="mb-3">
                                <label for="cve-severity-input" class="form-label">Severity</label>
                                <select class="form-select" id="cve-severity-input" required>
                                    <option value="">Select severity</option>
                                    <option value="critical">Critical</option>
                                    <option value="high">High</option>
                                    <option value="medium">Medium</option>
                                    <option value="low">Low</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label for="cve-cvss-input" class="form-label">CVSS Score</label>
                                <input type="number" class="form-control" id="cve-cvss-input" min="0" max="10" step="0.1" placeholder="7.5">
                            </div>
                            <div class="mb-3">
                                <label for="cve-tags-input" class="form-label">Tags</label>
                                <input type="text" class="form-control" id="cve-tags-input" placeholder="web, authentication, sql-injection">
                            </div>
                            <div class="mb-3">
                                <label for="cve-products-input" class="form-label">Affected Products</label>
                                <input type="text" class="form-control" id="cve-products-input" placeholder="Apache 2.4.x, PHP 8.x">
                            </div>
                            <div class="mb-3">
                                <label for="cve-url-input" class="form-label">Source URL</label>
                                <input type="url" class="form-control" id="cve-url-input" placeholder="https://example.com/cve-details">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="save-cve-btn">Save CVE</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('add-cve-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('add-cve-modal'));
    modal.show();
    
    // Add save event listener
    document.getElementById('save-cve-btn').addEventListener('click', saveCve);
    
    // Clean up modal after hiding
    document.getElementById('add-cve-modal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Save new CVE
async function saveCve() {
    const form = document.getElementById('add-cve-form');
    const formData = new FormData(form);
    
    const cveData = {
        cve_id: document.getElementById('cve-id-input').value,
        title: document.getElementById('cve-title-input').value,
        description: document.getElementById('cve-description-input').value,
        severity: document.getElementById('cve-severity-input').value,
        cvss: document.getElementById('cve-cvss-input').value || null,
        tags: document.getElementById('cve-tags-input').value,
        affected_products: document.getElementById('cve-products-input').value,
        source_url: document.getElementById('cve-url-input').value
    };
    
    try {
        const response = await fetch(CVE_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(cveData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Close modal and reload data
        bootstrap.Modal.getInstance(document.getElementById('add-cve-modal')).hide();
        loadCves();
        
        // Show success message
        showSuccess('CVE added successfully!');
        
    } catch (error) {
        console.error('Error saving CVE:', error);
        showError('Failed to save CVE. Please try again.');
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
window.initCveMonitor = initCveMonitor;
window.loadCves = loadCves; 