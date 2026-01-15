// Search tools functionality

// API URLs
const EMAIL_SEARCH_URL = '/api/search/email';
const PHONE_SEARCH_URL = '/api/search/phone';
const CLEAR_CACHE_URL = '/api/search/clear_cache';

// Initialize search tools
function initSearchTools() {
    // Add event listener for email search form
    if (emailSearchForm) {
        emailSearchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = emailInput.value.trim();
            if (!email) return;
            
            // Show loading indicator
            emailResults.classList.remove('d-none');
            emailResultsContent.innerHTML = `
                <div class="d-flex justify-content-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            `;
            
            try {
                // Make API request
                const response = await fetch(`${EMAIL_SEARCH_URL}?email=${encodeURIComponent(email)}`);
                const data = await response.json();
                
                // Format and display results
                renderEmailResults(data);
            } catch (error) {
                console.error('Error searching email:', error);
                emailResultsContent.innerHTML = `
                    <div class="alert alert-danger">
                        Error searching email: ${error.message}
                    </div>
                `;
            }
        });
    }
    
    // Add event listener for phone search form
    if (phoneSearchForm) {
        phoneSearchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const phone = phoneInput.value.trim();
            if (!phone) return;
            
            // Show loading indicator
            phoneResults.classList.remove('d-none');
            phoneResultsContent.innerHTML = `
                <div class="d-flex justify-content-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            `;
            
            try {
                // Make API request
                const response = await fetch(`${PHONE_SEARCH_URL}?phone=${encodeURIComponent(phone)}`);
                const data = await response.json();
                
                // Format and display results
                renderPhoneResults(data);
            } catch (error) {
                console.error('Error searching phone:', error);
                phoneResultsContent.innerHTML = `
                    <div class="alert alert-danger">
                        Error searching phone: ${error.message}
                    </div>
                `;
            }
        });
    }
}

// Render email search results
function renderEmailResults(data) {
    if (!data || data.error) {
        emailResultsContent.innerHTML = `
            <div class="alert alert-danger">
                ${data.error || 'An error occurred while searching for this email.'}
            </div>
        `;
        return;
    }
    
    // Format timestamp
    let formattedDate = data.timestamp;
    try {
        const date = new Date(data.timestamp);
        if (!isNaN(date)) {
            formattedDate = date.toLocaleString();
        }
    } catch (e) {
        // Keep original format if parsing fails
    }
    
    // Start building the results HTML
    let html = `
        <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0">Results for: <strong>${data.email}</strong></h6>
                <span class="text-muted small">${formattedDate}</span>
            </div>
            
            <div class="badge ${data.found ? 'bg-danger' : 'bg-success'} mb-3">
                ${data.found ? 'Exposed' : 'Not Found'}
            </div>
        </div>
    `;
    
    // Check Have I Been Pwned results
    if (data.sources && data.sources.haveibeenpwned) {
        const hibp = data.sources.haveibeenpwned;
        
        html += `
            <div class="card mb-3">
                <div class="card-header bg-secondary text-white">
                    <i class="fas fa-database me-2"></i> Have I Been Pwned
                </div>
                <div class="card-body">
        `;
        
        if (hibp.error) {
            html += `
                <div class="alert alert-warning">
                    ${hibp.error}
                </div>
            `;
        } else if (hibp.found) {
            html += `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Found in ${hibp.breach_count} data breach${hibp.breach_count !== 1 ? 'es' : ''}
                </div>
                <ul class="list-group mb-3">
            `;
            
            hibp.breaches.forEach(breach => {
                html += `
                    <li class="list-group-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <strong>${breach.name}</strong>
                            <span class="badge bg-secondary">${breach.breach_date}</span>
                        </div>
                        <div class="small text-muted">${breach.domain}</div>
                        <div class="mt-2">
                            <span class="small">Data exposed:</span>
                            <div class="mt-1">
                `;
                
                breach.data_classes.forEach(dataClass => {
                    html += `<span class="badge bg-info me-1 mb-1">${dataClass}</span>`;
                });
                
                html += `
                            </div>
                        </div>
                    </li>
                `;
            });
            
            html += `</ul>`;
        } else {
            html += `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    ${hibp.message || 'No breaches found!'}
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    // Check Pastebin results
    if (data.sources && data.sources.pastebin_sites) {
        const pastebin = data.sources.pastebin_sites;
        
        html += `
            <div class="card mb-3">
                <div class="card-header bg-secondary text-white">
                    <i class="fas fa-paste me-2"></i> Paste Sites
                </div>
                <div class="card-body">
        `;
        
        if (pastebin.error) {
            html += `
                <div class="alert alert-warning">
                    ${pastebin.error}
                </div>
            `;
        } else if (pastebin.found) {
            html += `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Found on paste sites
                </div>
                <ul class="list-group mb-3">
            `;
            
            pastebin.sites.forEach(site => {
                if (site.found) {
                    html += `
                        <li class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <strong>${site.site}</strong>
                                <a href="${site.url}" target="_blank" class="btn btn-sm btn-outline-secondary">
                                    <i class="fas fa-external-link-alt"></i> View
                                </a>
                            </div>
                        </li>
                    `;
                }
            });
            
            html += `</ul>`;
        } else {
            html += `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    Not found on paste sites
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    // Add recommendations
    html += `
        <div class="card mb-3">
            <div class="card-header bg-dark text-white">
                <i class="fas fa-shield-alt me-2"></i> Recommendations
            </div>
            <div class="card-body">
                <ul class="list-group">
                    <li class="list-group-item">
                        <i class="fas fa-lock me-2 text-primary"></i>
                        Use a unique, strong password for each account
                    </li>
                    <li class="list-group-item">
                        <i class="fas fa-key me-2 text-primary"></i>
                        Enable two-factor authentication when available
                    </li>
                    <li class="list-group-item">
                        <i class="fas fa-eye-slash me-2 text-primary"></i>
                        Monitor your accounts for suspicious activity
                    </li>
                </ul>
            </div>
        </div>
    `;
    
    emailResultsContent.innerHTML = html;
}

// Render phone search results
function renderPhoneResults(data) {
    if (!data || data.error) {
        phoneResultsContent.innerHTML = `
            <div class="alert alert-danger">
                ${data.error || 'An error occurred while searching for this phone number.'}
            </div>
        `;
        return;
    }
    
    // Format timestamp
    let formattedDate = data.timestamp;
    try {
        const date = new Date(data.timestamp);
        if (!isNaN(date)) {
            formattedDate = date.toLocaleString();
        }
    } catch (e) {
        // Keep original format if parsing fails
    }
    
    // Start building the results HTML
    let html = `
        <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0">Results for: <strong>${data.phone_number}</strong></h6>
                <span class="text-muted small">${formattedDate}</span>
            </div>
            
            <div class="badge ${data.found ? 'bg-danger' : 'bg-success'} mb-3">
                ${data.found ? 'Found in Public Sources' : 'Not Found'}
            </div>
        </div>
    `;
    
    // Basic information
    if (data.sources && data.sources.basic_info) {
        const basicInfo = data.sources.basic_info;
        
        html += `
            <div class="card mb-3">
                <div class="card-header bg-secondary text-white">
                    <i class="fas fa-info-circle me-2"></i> Basic Information
                </div>
                <div class="card-body">
        `;
        
        if (basicInfo.error) {
            html += `
                <div class="alert alert-warning">
                    ${basicInfo.error}
                </div>
            `;
        } else if (basicInfo.valid) {
            html += `<dl class="row mb-0">`;
            
            if (basicInfo.number) {
                html += `
                    <dt class="col-sm-4">Number</dt>
                    <dd class="col-sm-8">${basicInfo.number}</dd>
                `;
            }
            
            if (basicInfo.country) {
                html += `
                    <dt class="col-sm-4">Country</dt>
                    <dd class="col-sm-8">${basicInfo.country} ${basicInfo.country_code ? `(+${basicInfo.country_code})` : ''}</dd>
                `;
            }
            
            if (basicInfo.carrier) {
                html += `
                    <dt class="col-sm-4">Carrier</dt>
                    <dd class="col-sm-8">${basicInfo.carrier}</dd>
                `;
            }
            
            if (basicInfo.line_type) {
                html += `
                    <dt class="col-sm-4">Line Type</dt>
                    <dd class="col-sm-8">${basicInfo.line_type}</dd>
                `;
            }
            
            if (basicInfo.note) {
                html += `
                    <dt class="col-sm-4">Note</dt>
                    <dd class="col-sm-8"><small class="text-muted">${basicInfo.note}</small></dd>
                `;
            }
            
            html += `</dl>`;
        } else {
            html += `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${basicInfo.message || 'Invalid phone number format'}
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    // Spam database results
    if (data.sources && data.sources.spam_databases) {
        const spam = data.sources.spam_databases;
        
        html += `
            <div class="card mb-3">
                <div class="card-header bg-secondary text-white">
                    <i class="fas fa-exclamation-circle me-2"></i> Spam Databases
                </div>
                <div class="card-body">
        `;
        
        if (spam.error) {
            html += `
                <div class="alert alert-warning">
                    ${spam.error}
                </div>
            `;
        } else if (spam.found) {
            html += `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Found in spam report databases
                </div>
                <ul class="list-group mb-3">
            `;
            
            spam.sites.forEach(site => {
                if (site.found) {
                    html += `
                        <li class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <strong>${site.site}</strong>
                                <a href="${site.url}" target="_blank" class="btn btn-sm btn-outline-secondary">
                                    <i class="fas fa-external-link-alt"></i> View
                                </a>
                            </div>
                            ${site.note ? `<small class="text-muted">${site.note}</small>` : ''}
                        </li>
                    `;
                }
            });
            
            html += `</ul>`;
        } else {
            html += `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    Not found in spam report databases
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    // Classified sites results
    if (data.sources && data.sources.classified_sites) {
        const classifieds = data.sources.classified_sites;
        
        html += `
            <div class="card mb-3">
                <div class="card-header bg-secondary text-white">
                    <i class="fas fa-ad me-2"></i> Classified Sites
                </div>
                <div class="card-body">
        `;
        
        if (classifieds.error) {
            html += `
                <div class="alert alert-warning">
                    ${classifieds.error}
                </div>
            `;
        } else if (classifieds.found) {
            html += `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Found in public classified listings
                </div>
                <ul class="list-group mb-3">
            `;
            
            classifieds.sites.forEach(site => {
                if (site.found) {
                    html += `
                        <li class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <strong>${site.site}</strong>
                                <a href="${site.url}" target="_blank" class="btn btn-sm btn-outline-secondary">
                                    <i class="fas fa-external-link-alt"></i> View
                                </a>
                            </div>
                            ${site.note ? `<small class="text-muted">${site.note}</small>` : ''}
                        </li>
                    `;
                }
            });
            
            html += `</ul>`;
        } else {
            html += `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    Not found in public classified listings
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    // Add recommendations
    html += `
        <div class="card mb-3">
            <div class="card-header bg-dark text-white">
                <i class="fas fa-shield-alt me-2"></i> Recommendations
            </div>
            <div class="card-body">
                <ul class="list-group">
                    <li class="list-group-item">
                        <i class="fas fa-user-shield me-2 text-primary"></i>
                        Consider using a VoIP service or phone number masking app for online accounts
                    </li>
                    <li class="list-group-item">
                        <i class="fas fa-bell-slash me-2 text-primary"></i>
                        Register with Do Not Call registries to reduce telemarketing calls
                    </li>
                    <li class="list-group-item">
                        <i class="fas fa-ban me-2 text-primary"></i>
                        Use spam call blocking apps to filter potential spam calls
                    </li>
                </ul>
            </div>
        </div>
    `;
    
    phoneResultsContent.innerHTML = html;
}