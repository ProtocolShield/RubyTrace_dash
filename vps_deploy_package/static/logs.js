/*
 * Logs functionality for viewing scraping logs and errors
 */

// Initialize logs section
function initLogs() {
    // Add event listeners
    document.getElementById('refresh-logs-btn').addEventListener('click', loadLogs);
    document.getElementById('view-errors-btn').addEventListener('click', viewErrorLogs);
    
    // Add filter change listeners
    document.getElementById('logs-source-filter').addEventListener('change', loadLogs);
    document.getElementById('logs-status-filter').addEventListener('change', loadLogs);
    document.getElementById('logs-limit').addEventListener('change', loadLogs);
    
    // Load logs on initialization
    loadLogs();
    
    // Load source options for the filter
    loadSourceOptionsForFilter();
}

// Load all sources for the filter dropdown
async function loadSourceOptionsForFilter() {
    try {
        const response = await fetch('/api/logs/sources');
        if (response.ok) {
            const sources = await response.json();
            const sourceFilter = document.getElementById('logs-source-filter');
            
            // Clear existing options except the default "All Sources" option
            while (sourceFilter.options.length > 1) {
                sourceFilter.remove(1);
            }
            
            // Add all sources as options
            sources.forEach(source => {
                const option = document.createElement('option');
                option.value = source;
                option.textContent = source;
                sourceFilter.appendChild(option);
            });
        } else {
            console.error('Failed to load sources for filter');
        }
    } catch (error) {
        console.error('Error loading sources for filter:', error);
    }
}

// Load logs with optional filtering
async function loadLogs() {
    const logsContainer = document.getElementById('logs-container');
    showLoading(logsContainer);
    
    // Hide error details if shown
    document.getElementById('error-details-container').classList.add('d-none');
    
    // Get filter values
    const source = document.getElementById('logs-source-filter').value;
    const status = document.getElementById('logs-status-filter').value;
    const limit = document.getElementById('logs-limit').value;
    
    // Change header based on status filter
    const logsHeader = document.getElementById('logs-header');
    if (status === 'error') {
        logsHeader.textContent = 'Error Logs';
    } else if (status === 'success') {
        logsHeader.textContent = 'Success Logs';
    } else {
        logsHeader.textContent = 'All Scraping Logs';
    }
    
    try {
        // Build query URL with filters
        let url = '/api/logs?';
        if (source) url += `source=${encodeURIComponent(source)}&`;
        if (status) url += `status=${encodeURIComponent(status)}&`;
        if (limit) url += `limit=${encodeURIComponent(limit)}&`;
        
        const response = await fetch(url);
        if (response.ok) {
            const logs = await response.json();
            renderLogs(logs);
        } else {
            logsContainer.innerHTML = '<div class="alert alert-danger">Failed to load logs. Please try again.</div>';
        }
    } catch (error) {
        console.error('Error loading logs:', error);
        logsContainer.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

// Helper function to handle API errors specifically
async function viewErrorLogs() {
    document.getElementById('logs-status-filter').value = 'error';
    loadLogs();
}

// Render logs to the container
function renderLogs(logs) {
    const logsContainer = document.getElementById('logs-container');
    
    if (logs.length === 0) {
        logsContainer.innerHTML = '<div class="alert alert-info">No logs found matching the current filters.</div>';
        return;
    }
    
    // Create table to display logs
    let html = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Date/Time</th>
                        <th>Source</th>
                        <th>Status</th>
                        <th>Items Found</th>
                        <th>Items Added</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add each log to the table
    logs.forEach(log => {
        const timestamp = new Date(log.timestamp).toLocaleString();
        const statusClass = log.status === 'error' ? 'text-danger' : 'text-success';
        const statusIcon = log.status === 'error' 
            ? '<i class="fas fa-times-circle"></i>' 
            : '<i class="fas fa-check-circle"></i>';
        
        html += `
            <tr>
                <td>${timestamp}</td>
                <td>${log.source_name}</td>
                <td class="${statusClass}">${statusIcon} ${log.status}</td>
                <td>${log.items_found}</td>
                <td>${log.items_added}</td>
                <td>
        `;
        
        // Add view details button for error logs
        if (log.status === 'error' && log.error_message) {
            html += `
                <button class="btn btn-sm btn-outline-danger view-error-btn" 
                    data-error-message="${encodeURIComponent(log.error_message)}"
                    data-source="${encodeURIComponent(log.source_name)}"
                    data-timestamp="${encodeURIComponent(timestamp)}">
                    <i class="fas fa-eye"></i> View Error
                </button>
            `;
        }
        
        html += `
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    logsContainer.innerHTML = html;
    
    // Add event listeners to the error buttons
    document.querySelectorAll('.view-error-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const errorMessage = decodeURIComponent(this.getAttribute('data-error-message'));
            const source = decodeURIComponent(this.getAttribute('data-source'));
            const timestamp = decodeURIComponent(this.getAttribute('data-timestamp'));
            showErrorDetails(errorMessage, source, timestamp);
        });
    });
}

// Show detailed error information
function showErrorDetails(errorMessage, source, timestamp) {
    const errorContainer = document.getElementById('error-details-container');
    const errorContent = document.getElementById('error-details-content');
    
    errorContent.innerHTML = `
        <div class="mb-3">
            <strong>Source:</strong> ${source}
        </div>
        <div class="mb-3">
            <strong>Timestamp:</strong> ${timestamp}
        </div>
        <div class="mb-3">
            <strong>Error Message:</strong>
            <div class="alert alert-danger mt-2">
                <pre class="mb-0" style="white-space: pre-wrap; word-break: break-word;">${errorMessage}</pre>
            </div>
        </div>
        <button class="btn btn-secondary" id="hide-error-details-btn">
            <i class="fas fa-times me-1"></i> Close
        </button>
    `;
    
    errorContainer.classList.remove('d-none');
    
    // Add event listener to hide the error details
    document.getElementById('hide-error-details-btn').addEventListener('click', function() {
        errorContainer.classList.add('d-none');
    });
    
    // Scroll to error details
    errorContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Show loading spinner
function showLoading(container) {
    container.innerHTML = `
        <div class="d-flex justify-content-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
}