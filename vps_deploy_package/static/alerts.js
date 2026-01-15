/**
 * Alerts management functionality for the privacy OSINT dashboard.
 * Handles CRUD operations for keyword alerts.
 */

// API endpoints
const ALERTS_API_URL = '/api/alerts';
const CHECK_ALERTS_URL = '/api/alerts/check';

// DOM elements
const alertsContainer = document.getElementById('alerts-container');
const checkAlertsBtn = document.getElementById('check-alerts-btn');
const saveAlertBtn = document.getElementById('save-alert-btn');
const updateAlertBtn = document.getElementById('update-alert-btn');
const deleteAlertBtn = document.getElementById('delete-alert-btn');
const alertKeywordInput = document.getElementById('alert-keyword');
const alertPrioritySelect = document.getElementById('alert-priority');
const alertEnabledSwitch = document.getElementById('alert-enabled');
const editAlertIdInput = document.getElementById('edit-alert-id');
const editAlertKeywordInput = document.getElementById('edit-alert-keyword');
const editAlertPrioritySelect = document.getElementById('edit-alert-priority');
const editAlertEnabledSwitch = document.getElementById('edit-alert-enabled');
const alertResultsDiv = document.getElementById('alert-results');
const alertResultsContent = document.getElementById('alert-results-content');

// Add event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if alerts elements exist
    if (checkAlertsBtn) {
        initAlerts();
    }
});

// Initialize alerts functionality
function initAlerts() {
    // Load alerts on page load if we're on the alerts view
    if (window.location.hash === '#alerts-view' || document.getElementById('alerts-view').classList.contains('active-view')) {
        loadAlerts();
    }
    
    // Add event listeners for alerts management
    if (checkAlertsBtn) {
        checkAlertsBtn.addEventListener('click', checkAlerts);
    }
    
    if (saveAlertBtn) {
        saveAlertBtn.addEventListener('click', saveAlert);
    }
    
    if (updateAlertBtn) {
        updateAlertBtn.addEventListener('click', updateAlert);
    }
    
    if (deleteAlertBtn) {
        deleteAlertBtn.addEventListener('click', deleteAlert);
    }
}

// Load alerts from the API
async function loadAlerts() {
    showLoading(alertsContainer);
    
    try {
        const response = await fetch(ALERTS_API_URL);
        const alerts = await response.json();
        
        renderAlerts(alerts);
    } catch (error) {
        console.error('Error loading alerts:', error);
        alertsContainer.innerHTML = `
            <div class="alert alert-danger">
                Error loading alerts: ${error.message}
            </div>
        `;
    }
}

// Render alerts to the container
function renderAlerts(alerts) {
    if (!alerts || alerts.length === 0) {
        alertsContainer.innerHTML = `
            <div class="alert alert-info">
                No keyword alerts configured. Add an alert to get notified when specific privacy-related terms appear.
            </div>
        `;
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-hover">';
    html += `
        <thead>
            <tr>
                <th>Keyword</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Last Triggered</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
    `;
    
    alerts.forEach(alert => {
        // Format priority badge
        const priorityClass = {
            'low': 'bg-secondary',
            'medium': 'bg-primary',
            'high': 'bg-danger'
        }[alert.priority] || 'bg-secondary';
        
        // Format status badge
        const statusClass = alert.enabled ? 'bg-success' : 'bg-warning text-dark';
        const statusText = alert.enabled ? 'Active' : 'Disabled';
        
        // Format last triggered time
        let lastTriggered = 'Never';
        if (alert.last_triggered) {
            try {
                const date = new Date(alert.last_triggered);
                if (!isNaN(date)) {
                    lastTriggered = date.toLocaleString();
                }
            } catch (e) {
                // Use original value if parsing fails
                lastTriggered = alert.last_triggered;
            }
        }
        
        html += `
            <tr>
                <td>${alert.keyword}</td>
                <td><span class="badge ${priorityClass}">${alert.priority}</span></td>
                <td><span class="badge ${statusClass}">${statusText}</span></td>
                <td>${lastTriggered}</td>
                <td>
                    <button class="btn btn-sm btn-primary edit-alert-btn" data-alert-id="${alert.id}" data-bs-toggle="modal" data-bs-target="#edit-alert-modal">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    alertsContainer.innerHTML = html;
    
    // Add event listeners to edit buttons
    document.querySelectorAll('.edit-alert-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const alertId = btn.getAttribute('data-alert-id');
            prepareEditAlert(alertId, alerts);
        });
    });
}

// Prepare edit alert modal with the alert data
function prepareEditAlert(alertId, alerts) {
    const alert = alerts.find(a => a.id == alertId);
    if (!alert) return;
    
    editAlertIdInput.value = alert.id;
    editAlertKeywordInput.value = alert.keyword;
    editAlertPrioritySelect.value = alert.priority;
    editAlertEnabledSwitch.checked = alert.enabled;
}

// Save a new alert
async function saveAlert() {
    const keyword = alertKeywordInput.value.trim();
    if (!keyword) {
        alert('Please enter a keyword.');
        return;
    }
    
    const alertData = {
        keyword: keyword,
        priority: alertPrioritySelect.value,
        enabled: alertEnabledSwitch.checked
    };
    
    try {
        const response = await fetch(ALERTS_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(alertData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Close modal and reload alerts
            bootstrap.Modal.getInstance(document.getElementById('add-alert-modal')).hide();
            alertKeywordInput.value = '';
            alertPrioritySelect.value = 'medium';
            alertEnabledSwitch.checked = true;
            
            loadAlerts();
            
            // Show success message
            alert('Alert created successfully!');
        } else {
            alert(`Error: ${result.error || 'Failed to create alert'}`);
        }
    } catch (error) {
        console.error('Error saving alert:', error);
        alert(`Error: ${error.message}`);
    }
}

// Update an existing alert
async function updateAlert() {
    const alertId = editAlertIdInput.value;
    if (!alertId) return;
    
    const alertData = {
        priority: editAlertPrioritySelect.value,
        enabled: editAlertEnabledSwitch.checked
    };
    
    try {
        const response = await fetch(`${ALERTS_API_URL}/${alertId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(alertData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Close modal and reload alerts
            bootstrap.Modal.getInstance(document.getElementById('edit-alert-modal')).hide();
            
            loadAlerts();
            
            // Show success message
            alert('Alert updated successfully!');
        } else {
            alert(`Error: ${result.error || 'Failed to update alert'}`);
        }
    } catch (error) {
        console.error('Error updating alert:', error);
        alert(`Error: ${error.message}`);
    }
}

// Delete an alert
async function deleteAlert() {
    const alertId = editAlertIdInput.value;
    if (!alertId) return;
    
    if (!confirm('Are you sure you want to delete this alert?')) {
        return;
    }
    
    try {
        const response = await fetch(`${ALERTS_API_URL}/${alertId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Close modal and reload alerts
            bootstrap.Modal.getInstance(document.getElementById('edit-alert-modal')).hide();
            
            loadAlerts();
            
            // Show success message
            alert('Alert deleted successfully!');
        } else {
            alert(`Error: ${result.error || 'Failed to delete alert'}`);
        }
    } catch (error) {
        console.error('Error deleting alert:', error);
        alert(`Error: ${error.message}`);
    }
}

// Check for alerts in current data
async function checkAlerts() {
    // Show loading state
    checkAlertsBtn.disabled = true;
    checkAlertsBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking...';
    alertResultsDiv.classList.add('d-none');
    
    try {
        const response = await fetch(CHECK_ALERTS_URL, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            renderAlertResults(result);
            // Also refresh the alerts list to update "last triggered" times
            loadAlerts();
        } else {
            alert(`Error: ${result.error || 'Failed to check alerts'}`);
        }
    } catch (error) {
        console.error('Error checking alerts:', error);
        alert(`Error: ${error.message}`);
    } finally {
        // Reset button state
        checkAlertsBtn.disabled = false;
        checkAlertsBtn.innerHTML = '<i class="fas fa-bell me-1"></i> Check Alerts';
    }
}

// Render alert check results
function renderAlertResults(data) {
    alertResultsDiv.classList.remove('d-none');
    
    if (!data.triggered || data.triggered.length === 0) {
        alertResultsContent.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-check-circle me-2"></i> No alerts triggered. All clear!
            </div>
        `;
        return;
    }
    
    // Sort alerts by priority (high > medium > low)
    const sortedAlerts = [...data.triggered].sort((a, b) => {
        const priorityRank = { 'high': 3, 'medium': 2, 'low': 1 };
        return priorityRank[b.alert.priority] - priorityRank[a.alert.priority];
    });
    
    let html = `
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i> <strong>${sortedAlerts.length} alert(s) triggered!</strong>
        </div>
    `;
    
    sortedAlerts.forEach(triggered => {
        const priorityClass = {
            'low': 'bg-secondary',
            'medium': 'bg-primary',
            'high': 'bg-danger'
        }[triggered.alert.priority] || 'bg-secondary';
        
        html += `
            <div class="card mb-3 border-${priorityClass.replace('bg-', '')}">
                <div class="card-header ${priorityClass} text-white">
                    <strong>Keyword:</strong> ${triggered.alert.keyword}
                    <span class="badge bg-light text-dark float-end">${triggered.alert.priority} priority</span>
                </div>
                <div class="card-body">
                    <h6 class="mb-3">Matching Posts (${triggered.matching_posts.length}):</h6>
                    <div class="list-group">
        `;
        
        triggered.matching_posts.forEach(post => {
            // Format date
            let formattedDate = post.timestamp;
            try {
                const date = new Date(post.timestamp);
                if (!isNaN(date)) {
                    formattedDate = date.toLocaleString();
                }
            } catch (e) {
                // Keep original format if parsing fails
            }
            
            html += `
                <a href="${post.url}" class="list-group-item list-group-item-action" target="_blank">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${post.title}</h6>
                        <small>${formattedDate}</small>
                    </div>
                    <small class="text-muted">Source: ${post.source}</small>
                </a>
            `;
        });
        
        html += `
                    </div>
                </div>
            </div>
        `;
    });
    
    alertResultsContent.innerHTML = html;
    
    // Scroll to the results
    alertResultsDiv.scrollIntoView({ behavior: 'smooth' });
}

// Utility function to show loading state
function showLoading(container) {
    container.innerHTML = `
        <div class="d-flex justify-content-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
}