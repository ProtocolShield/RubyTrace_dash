// Settings Management (API Keys & Cache)

// API URLs
const API_KEYS_URL = '/api/config/api_keys';
const SCHEDULE_URL = '/api/schedule';
// CLEAR_CACHE_URL is defined in search.js

// DOM elements
const apiKeysContainer = document.getElementById('api-keys-container');
const addApiKeyForm = document.getElementById('add-api-key-form');
const serviceSelect = document.getElementById('service-select');
const customServiceField = document.getElementById('custom-service-field');
const customServiceInput = document.getElementById('custom-service-input');
const apiKeyInput = document.getElementById('api-key-input');
const scheduleInfoContainer = document.getElementById('schedule-info');
const updateScheduleForm = document.getElementById('update-schedule-form');
const scheduleIntervalInput = document.getElementById('schedule-interval');
const clearSearchCacheBtn = document.getElementById('clear-search-cache-btn');
const goToSettingsBtn = document.getElementById('go-to-settings-btn');

// Initialize settings functions when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initSettings();
});

function initSettings() {
    // Load API keys and schedule info on settings page load
    if (window.location.hash === '#settings-view') {
        loadApiKeys();
        loadScheduleInfo();
    }
    
    // When the "Configure API Keys" button is clicked, go to settings page
    if (goToSettingsBtn) {
        goToSettingsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active nav link
            document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
            document.querySelector('.nav-link[data-view="settings"]').classList.add('active');
            
            // Show settings view
            document.querySelectorAll('.view-section').forEach(section => {
                section.classList.remove('active-view');
                if (section.id === 'settings-view') {
                    section.classList.add('active-view');
                }
            });
            
            // Load API keys and schedule information
            loadApiKeys();
            loadScheduleInfo();
        });
    }
    
    // Toggle custom service field based on selection
    if (serviceSelect) {
        serviceSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customServiceField.classList.remove('d-none');
                customServiceInput.setAttribute('required', 'required');
            } else {
                customServiceField.classList.add('d-none');
                customServiceInput.removeAttribute('required');
            }
        });
    }
    
    // Handle API key form submission
    if (addApiKeyForm) {
        addApiKeyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form values
            const selectedService = serviceSelect.value;
            let service = selectedService;
            
            if (selectedService === 'custom') {
                service = customServiceInput.value.trim();
                if (!service) {
                    alert('Please enter a custom service name');
                    return;
                }
            } else if (!selectedService) {
                alert('Please select a service');
                return;
            }
            
            const key = apiKeyInput.value.trim();
            if (!key) {
                alert('Please enter an API key');
                return;
            }
            
            // Save API key using our utility function
            saveApiKey(service, key)
                .then(() => {
                    // Reset form on success (the saveApiKey function handles errors)
                    addApiKeyForm.reset();
                    customServiceField.classList.add('d-none');
                });
        });
    }
    
    // Handle clear cache button
    if (clearSearchCacheBtn) {
        clearSearchCacheBtn.addEventListener('click', async function() {
            try {
                const response = await fetch(CLEAR_CACHE_URL, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('Search cache has been cleared!');
                } else {
                    throw new Error(data.error || 'Failed to clear cache');
                }
            } catch (error) {
                console.error('Error clearing cache:', error);
                alert(`Error clearing cache: ${error.message}`);
            }
        });
    }
    
    // Handle schedule update form
    if (updateScheduleForm) {
        updateScheduleForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const interval = parseInt(scheduleIntervalInput.value);
            if (isNaN(interval) || interval < 15) {
                alert('Please enter a valid interval (at least 15 minutes)');
                return;
            }
            
            try {
                const response = await fetch(SCHEDULE_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        interval_minutes: interval
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert(`Schedule updated to run every ${interval} minutes!`);
                    loadScheduleInfo(); // Reload schedule info
                } else {
                    throw new Error(data.error || 'Failed to update schedule');
                }
            } catch (error) {
                console.error('Error updating schedule:', error);
                alert(`Error updating schedule: ${error.message}`);
            }
        });
    }
}

// Load API keys from the backend
async function loadApiKeys() {
    if (!apiKeysContainer) return;
    
    // Show loading indicator
    apiKeysContainer.innerHTML = `
        <div class="d-flex justify-content-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    try {
        const response = await fetch(API_KEYS_URL);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to fetch API keys');
        }
        
        renderApiKeys(data.services);
    } catch (error) {
        console.error('Error loading API keys:', error);
        apiKeysContainer.innerHTML = `
            <div class="alert alert-danger">
                Error loading API keys: ${error.message}
            </div>
        `;
    }
}

// Render API keys in the container
function renderApiKeys(services) {
    if (!apiKeysContainer) return;
    
    if (!services || services.length === 0) {
        apiKeysContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i> No API keys configured yet.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="table-responsive">
            <table class="table table-bordered table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>Service</th>
                        <th>Key Preview</th>
                        <th>Last Updated</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    services.forEach(service => {
        // Format date
        let formattedDate = 'N/A';
        if (service.updated_at) {
            try {
                const date = new Date(service.updated_at);
                if (!isNaN(date)) {
                    formattedDate = date.toLocaleString();
                }
            } catch (e) {
                // Keep default format if parsing fails
            }
        }
        
        html += `
            <tr>
                <td>${service.service}</td>
                <td><code>${service.key_preview || '***'}</code></td>
                <td>${formattedDate}</td>
                <td>
                    <button class="btn btn-sm btn-primary update-api-key me-2" data-service="${service.service}">
                        <i class="fas fa-edit"></i> Update
                    </button>
                    <button class="btn btn-sm btn-danger delete-api-key" data-service="${service.service}">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    apiKeysContainer.innerHTML = html;
    
    // Add event listeners to delete buttons
    document.querySelectorAll('.delete-api-key').forEach(button => {
        button.addEventListener('click', async function() {
            const service = this.getAttribute('data-service');
            if (confirm(`Are you sure you want to delete the API key for ${service}?`)) {
                await deleteApiKey(service);
            }
        });
    });
    
    // Add event listeners to update buttons
    document.querySelectorAll('.update-api-key').forEach(button => {
        button.addEventListener('click', function() {
            const service = this.getAttribute('data-service');
            updateApiKey(service);
        });
    });
}

// Delete an API key
async function deleteApiKey(service) {
    try {
        const response = await fetch(`${API_KEYS_URL}/${encodeURIComponent(service)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reload API keys
            loadApiKeys();
            
            // Show success notification
            alert(`API key for ${service} has been deleted!`);
        } else {
            throw new Error(data.error || 'Failed to delete API key');
        }
    } catch (error) {
        console.error('Error deleting API key:', error);
        alert(`Error deleting API key: ${error.message}`);
    }
}

// Update an API key
function updateApiKey(service) {
    // Prompt for the new key value
    const newKey = prompt(`Enter new API key for ${service}:`);
    
    // If the user cancels or enters an empty string, do nothing
    if (newKey === null || newKey.trim() === '') {
        return;
    }
    
    // Save the updated key
    saveApiKey(service, newKey.trim());
}

// Save or update an API key
async function saveApiKey(service, key) {
    try {
        const response = await fetch(API_KEYS_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                service: service,
                key: key
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reload API keys
            loadApiKeys();
            
            // Show success notification
            alert(`API key for ${service} has been ${data.message.includes('updated') ? 'updated' : 'added'}!`);
        } else {
            throw new Error(data.error || 'Failed to save API key');
        }
    } catch (error) {
        console.error('Error saving API key:', error);
        alert(`Error saving API key: ${error.message}`);
    }
}

// Load and display schedule information
async function loadScheduleInfo() {
    if (!scheduleInfoContainer) return;
    
    // Show loading indicator
    scheduleInfoContainer.innerHTML = `
        <div class="d-flex justify-content-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading schedule information...</span>
            </div>
        </div>
    `;
    
    try {
        const response = await fetch(SCHEDULE_URL);
        const data = await response.json();
        
        // Format the next run time
        let nextRunText = 'Not scheduled';
        if (data.next_run) {
            try {
                const nextRunDate = new Date(data.next_run);
                if (!isNaN(nextRunDate)) {
                    nextRunText = nextRunDate.toLocaleString();
                }
            } catch (e) {
                // Keep default format if parsing fails
            }
        }
        
        // Create the schedule info display
        const html = `
            <div class="card mb-3">
                <div class="card-body p-3">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <div class="me-3">
                                    <span class="badge ${data.active ? 'bg-success' : 'bg-secondary'} p-2 rounded-circle">
                                        <i class="fas fa-${data.active ? 'check' : 'pause'}"></i>
                                    </span>
                                </div>
                                <div>
                                    <h6 class="mb-0">Current Schedule</h6>
                                    <p class="mb-0 text-muted">Every ${data.interval_minutes} minutes</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex align-items-center">
                                <div class="me-3">
                                    <span class="badge bg-info p-2 rounded-circle">
                                        <i class="fas fa-calendar-alt"></i>
                                    </span>
                                </div>
                                <div>
                                    <h6 class="mb-0">Next Run</h6>
                                    <p class="mb-0 text-muted">${nextRunText}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        scheduleInfoContainer.innerHTML = html;
        
        // Set the current interval in the input field
        if (scheduleIntervalInput) {
            scheduleIntervalInput.value = data.interval_minutes;
        }
        
    } catch (error) {
        console.error('Error loading schedule information:', error);
        scheduleInfoContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i> Error loading schedule information: ${error.message}
            </div>
        `;
    }
}