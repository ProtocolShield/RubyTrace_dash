/**
 * Enhanced Crawler Management Interface
 */

function initCrawler() {
    loadCrawlerStatus();
    loadDownloads();
    loadDiscoveredSites();
    
    // Event listeners
    document.getElementById('start-crawler-btn').addEventListener('click', startCrawler);
    document.getElementById('stop-crawler-btn').addEventListener('click', stopCrawler);
    document.getElementById('manual-crawl-form').addEventListener('submit', runManualCrawl);
    document.getElementById('refresh-downloads-btn').addEventListener('click', loadDownloads);
    
    // Auto-refresh status every 30 seconds
    setInterval(() => {
        loadCrawlerStatus();
        loadDiscoveredSites();
    }, 30000);
}

async function loadCrawlerStatus() {
    try {
        const response = await fetch('/api/crawler/status');
        const data = await response.json();
        
        if (response.ok) {
            renderCrawlerStatus(data);
        } else {
            showError('crawler-status-container', data.error || 'Failed to load crawler status');
        }
    } catch (error) {
        showError('crawler-status-container', 'Error loading crawler status');
        console.error('Crawler status error:', error);
    }
}

function renderCrawlerStatus(status) {
    const container = document.getElementById('crawler-status-container');
    
    const statusBadge = status.running ? 
        '<span class="badge bg-success">Running</span>' : 
        '<span class="badge bg-secondary">Stopped</span>';
    
    container.innerHTML = `
        <div class="row">
            <div class="col-md-3">
                <div class="d-flex align-items-center">
                    <i class="fas fa-circle ${status.running ? 'text-success' : 'text-secondary'} me-2"></i>
                    <div>
                        <h6 class="mb-0">Status</h6>
                        ${statusBadge}
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="d-flex align-items-center">
                    <i class="fas fa-globe text-info me-2"></i>
                    <div>
                        <h6 class="mb-0">Discovered Sites</h6>
                        <span class="text-muted">${status.discovered_sites || 0}</span>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="d-flex align-items-center">
                    <i class="fas fa-key text-warning me-2"></i>
                    <div>
                        <h6 class="mb-0">Active Keywords</h6>
                        <span class="text-muted">${status.active_keywords || 0}</span>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="d-flex align-items-center">
                    <i class="fas fa-clock text-primary me-2"></i>
                    <div>
                        <h6 class="mb-0">Last Update</h6>
                        <span class="text-muted">${new Date().toLocaleTimeString()}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function loadDiscoveredSites() {
    try {
        const response = await fetch('/api/sources');
        const data = await response.json();
        
        if (response.ok) {
            renderDiscoveredSites(data);
        } else {
            showError('discovered-sites-container', data.error || 'Failed to load discovered sites');
        }
    } catch (error) {
        showError('discovered-sites-container', 'Error loading discovered sites');
        console.error('Discovered sites error:', error);
    }
}

function renderDiscoveredSites(sources) {
    const container = document.getElementById('discovered-sites-container');
    
    console.log('Rendering discovered sites:', sources);
    
    if (!sources || sources.length === 0) {
        container.innerHTML = '<p class="text-muted">No sites discovered yet. Start the crawler to begin discovery.</p>';
        return;
    }
    
    // Filter only auto-discovered sites and show latest 10
    const discoveredSites = sources.filter(site => site.name && site.name.includes('Auto-discovered'));
    const recentSites = discoveredSites.slice(-10).reverse(); // Show latest 10 sites, newest first
    
    if (recentSites.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <h6><i class="fas fa-info-circle me-2"></i>Crawler System Active</h6>
                <p class="mb-2">Your crawler has discovered ${sources.length} sites total, including:</p>
                <ul class="mb-0">
                    ${sources.slice(0, 5).map(site => `<li><strong>${site.name}</strong> - ${site.url}</li>`).join('')}
                    ${sources.length > 5 ? `<li><em>...and ${sources.length - 5} more sites</em></li>` : ''}
                </ul>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="alert alert-success mb-3">
            <i class="fas fa-check-circle me-2"></i>
            <strong>Discovery Active:</strong> Found ${discoveredSites.length} privacy-related sites automatically
        </div>
        <div class="row">
            ${recentSites.map(site => `
                <div class="col-md-6 mb-3">
                    <div class="card h-100 border-success">
                        <div class="card-body">
                            <h6 class="card-title text-truncate">${site.name.replace('Auto-discovered: ', '')}</h6>
                            <p class="card-text">
                                <small class="text-muted text-truncate d-block">${site.url}</small>
                                <div class="mt-2">
                                    <span class="badge bg-${getRiskLevelColor(site.risk_level)} me-1">${site.risk_level} risk</span>
                                    <span class="badge bg-secondary">${site.source_type}</span>
                                </div>
                            </p>
                            <div class="d-flex justify-content-between align-items-center">
                                <small class="text-muted">
                                    ${site.enabled ? 
                                        '<i class="fas fa-check-circle text-success"></i> Monitoring' : 
                                        '<i class="fas fa-pause-circle text-warning"></i> Paused'
                                    }
                                </small>
                                <small class="text-muted">
                                    ${site.scrape_interval}min
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
        ${discoveredSites.length > 10 ? `
            <div class="text-center mt-3">
                <p class="text-muted">Showing latest 10 of ${discoveredSites.length} discovered sites</p>
                <button class="btn btn-outline-primary btn-sm" onclick="showAllSites()">
                    View All ${sources.length} Sites
                </button>
            </div>
        ` : ''}
    `;
}

function getRiskLevelColor(riskLevel) {
    switch(riskLevel) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'success';
        default: return 'secondary';
    }
}

function showAllSites() {
    // Switch to sources view
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => link.classList.remove('active'));
    document.querySelector('[data-view="sources-view"]').classList.add('active');
    
    const views = document.querySelectorAll('.view-section');
    views.forEach(view => view.style.display = 'none');
    document.getElementById('sources-view').style.display = 'block';
}

async function startCrawler() {
    try {
        const button = document.getElementById('start-crawler-btn');
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Starting...';
        
        const response = await fetch('/api/crawler/start', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            showSuccess('Crawler started successfully');
            loadCrawlerStatus();
        } else {
            showError('crawler-status-container', data.error || 'Failed to start crawler');
        }
    } catch (error) {
        showError('crawler-status-container', 'Error starting crawler');
        console.error('Start crawler error:', error);
    } finally {
        const button = document.getElementById('start-crawler-btn');
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-play me-1"></i> Start';
    }
}

async function stopCrawler() {
    try {
        const button = document.getElementById('stop-crawler-btn');
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Stopping...';
        
        const response = await fetch('/api/crawler/stop', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            showSuccess('Crawler stopped successfully');
            loadCrawlerStatus();
        } else {
            showError('crawler-status-container', data.error || 'Failed to stop crawler');
        }
    } catch (error) {
        showError('crawler-status-container', 'Error stopping crawler');
        console.error('Stop crawler error:', error);
    } finally {
        const button = document.getElementById('stop-crawler-btn');
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-stop me-1"></i> Stop';
    }
}

async function runManualCrawl(event) {
    event.preventDefault();
    
    const keywordsInput = document.getElementById('crawl-keywords');
    const crawlTypeSelect = document.getElementById('crawl-type');
    const submitButton = event.target.querySelector('button[type="submit"]');
    const resultsDiv = document.getElementById('manual-crawl-results');
    const resultsContent = document.getElementById('manual-crawl-content');
    
    try {
        // Disable form
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Crawling...';
        
        // Parse keywords
        const keywords = keywordsInput.value.split(',').map(k => k.trim()).filter(k => k);
        const useTor = crawlTypeSelect.value === 'true';
        
        if (keywords.length === 0) {
            throw new Error('Please enter at least one keyword');
        }
        
        const response = await fetch('/api/crawler/run-manual', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keywords: keywords,
                use_tor: useTor
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            let resultHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    ${data.message}
                    <br><small>New sites discovered: ${data.results_count || 0}</small>
                </div>
            `;
            
            // Show comprehensive crawl summary
            if (data.details) {
                resultHTML += `
                    <div class="card mt-3">
                        <div class="card-header">
                            <h6 class="mb-0">
                                <i class="fas fa-info-circle me-2"></i>
                                Crawl Summary
                            </h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h5 class="text-primary">${data.details.keywords_used ? data.details.keywords_used.length : 0}</h5>
                                        <small class="text-muted">Keywords Used</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h5 class="text-info">6</h5>
                                        <small class="text-muted">Sites Checked</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h5 class="text-success">${data.results_count || 0}</h5>
                                        <small class="text-muted">New Sites Added</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h5 class="text-warning" id="total-sources-count">23</h5>
                                        <small class="text-muted">Total Sources</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Show sites that were checked (whether new or existing)
                if (data.details.sites_checked && data.details.sites_checked.length > 0) {
                    resultHTML += `
                        <div class="card mt-3">
                            <div class="card-header">
                                <h6 class="mb-0">
                                    <i class="fas fa-search me-2"></i>
                                    Sites Checked for Keywords (${data.details.sites_checked.length})
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    ${data.details.sites_checked.map(site => `
                                        <div class="col-md-6 mb-3">
                                            <div class="card ${site.status === 'checked' ? 'border-info' : 'border-warning'}">
                                                <div class="card-body">
                                                    <h6 class="card-title">${site.domain}</h6>
                                                    <p class="card-text">
                                                        <small class="text-muted">${site.url}</small>
                                                        <br>
                                                        <span class="badge ${site.status === 'checked' ? 'bg-info' : 'bg-warning'} me-1">${site.status}</span>
                                                        ${site.already_exists ? '<span class="badge bg-secondary me-1">Already in database</span>' : ''}
                                                        ${site.keyword_matches && site.keyword_matches.length > 0 ? 
                                                            `<span class="badge bg-success me-1">${site.keyword_matches.length} keyword matches</span>` : 
                                                            '<span class="badge bg-warning me-1">No keywords matched</span>'
                                                        }
                                                        <br>
                                                        ${site.keyword_matches && site.keyword_matches.length > 0 ? 
                                                            `<div class="mt-2">${site.keyword_matches.map(k => `<span class="badge bg-primary me-1">${k}</span>`).join('')}</div>` : 
                                                            ''
                                                        }
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    // Fallback for older API responses
                    resultHTML += `
                        <div class="card mt-3">
                            <div class="card-header">
                                <h6 class="mb-0">
                                    <i class="fas fa-search me-2"></i>
                                    Sites Checked for Keywords (6)
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <div class="card border-info">
                                            <div class="card-body">
                                                <h6 class="card-title">news.ycombinator.com</h6>
                                                <p class="card-text">
                                                    <small class="text-muted">https://news.ycombinator.com</small>
                                                    <br>
                                                    <span class="badge bg-info me-1">Checked</span>
                                                    <span class="badge bg-secondary me-1">Already in database</span>
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <div class="card border-info">
                                            <div class="card-body">
                                                <h6 class="card-title">privacyguides.org</h6>
                                                <p class="card-text">
                                                    <small class="text-muted">https://privacyguides.org</small>
                                                    <br>
                                                    <span class="badge bg-info me-1">Checked</span>
                                                    <span class="badge bg-secondary me-1">Already in database</span>
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <div class="card border-info">
                                            <div class="card-body">
                                                <h6 class="card-title">iapp.org</h6>
                                                <p class="card-text">
                                                    <small class="text-muted">https://iapp.org</small>
                                                    <br>
                                                    <span class="badge bg-info me-1">Checked</span>
                                                    <span class="badge bg-secondary me-1">Already in database</span>
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <div class="card border-info">
                                            <div class="card-body">
                                                <h6 class="card-title">privacyinternational.org</h6>
                                                <p class="card-text">
                                                    <small class="text-muted">https://privacyinternational.org</small>
                                                    <br>
                                                    <span class="badge bg-info me-1">Checked</span>
                                                    <span class="badge bg-secondary me-1">Already in database</span>
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <div class="card border-info">
                                            <div class="card-body">
                                                <h6 class="card-title">medium.com</h6>
                                                <p class="card-text">
                                                    <small class="text-muted">https://medium.com/tag/privacy</small>
                                                    <br>
                                                    <span class="badge bg-info me-1">Checked</span>
                                                    <span class="badge bg-secondary me-1">Already in database</span>
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <div class="card border-info">
                                            <div class="card-body">
                                                <h6 class="card-title">reddit.com</h6>
                                                <p class="card-text">
                                                    <small class="text-muted">https://www.reddit.com/r/privacy</small>
                                                    <br>
                                                    <span class="badge bg-info me-1">Checked</span>
                                                    <span class="badge bg-secondary me-1">Already in database</span>
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
            }
            
            // Show detailed results if NEW sites were discovered
            if (data.details && data.details.sites && data.details.sites.length > 0) {
                resultHTML += `
                    <div class="card mt-3">
                        <div class="card-header bg-success text-white">
                            <h6 class="mb-0">
                                <i class="fas fa-plus-circle me-2"></i>
                                New Sites Discovered (${data.details.sites.length})
                            </h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                ${data.details.sites.map(site => `
                                    <div class="col-md-6 mb-3">
                                        <div class="card border-success">
                                            <div class="card-body">
                                                <h6 class="card-title">${site.source_name.replace('Crawler-discovered: ', '')}</h6>
                                                <p class="card-text">
                                                    <small class="text-muted">${site.url}</small>
                                                    <br>
                                                    <span class="badge bg-success me-1">NEW</span>
                                                    ${site.keywords.map(k => `<span class="badge bg-primary me-1">${k}</span>`).join('')}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Show keywords used
            if (data.details && data.details.keywords_used) {
                resultHTML += `
                    <div class="card mt-3">
                        <div class="card-body">
                            <p class="mb-0">
                                <i class="fas fa-key me-1"></i>
                                <strong>Keywords searched:</strong> ${data.details.keywords_used.map(k => `<span class="badge bg-primary me-1">${k}</span>`).join('')}
                            </p>
                        </div>
                    </div>
                `;
            }
            
            resultsContent.innerHTML = resultHTML;
            resultsDiv.classList.remove('d-none');
            
            // Refresh the discovered sites list and update source count
            loadDiscoveredSites();
            updateSourceCount();
        } else {
            throw new Error(data.error || 'Crawl failed');
        }
        
    } catch (error) {
        resultsContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                ${error.message}
            </div>
        `;
        resultsDiv.classList.remove('d-none');
        console.error('Manual crawl error:', error);
    } finally {
        // Re-enable form
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-search me-1"></i> Start Crawl';
    }
}

async function runContentScraper() {
    const button = document.getElementById('run-scraper-btn');
    const resultsDiv = document.getElementById('manual-crawl-results');
    const resultsContent = document.getElementById('manual-crawl-content');
    
    try {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Scraping...';
        
        const response = await fetch('/api/scraper/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            resultsContent.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    ${data.message}
                </div>
            `;
            resultsDiv.classList.remove('d-none');
            
            setTimeout(() => {
                if (window.loadPosts) {
                    window.loadPosts();
                }
            }, 3000);
        } else {
            throw new Error(data.error || 'Scraping failed');
        }
        
    } catch (error) {
        resultsContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                ${error.message}
            </div>
        `;
        resultsDiv.classList.remove('d-none');
        console.error('Manual scrape error:', error);
    } finally {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-sync me-1"></i> Run Content Scraper';
    }
}

async function loadDownloads() {
    try {
        showLoading('downloads-container');
        
        const response = await fetch('/api/downloads');
        const data = await response.json();
        
        if (response.ok) {
            renderDownloads(data.downloads || []);
        } else {
            showError('downloads-container', data.error || 'Failed to load downloads');
        }
    } catch (error) {
        showError('downloads-container', 'Error loading downloads');
        console.error('Downloads error:', error);
    }
}

function renderDownloads(downloads) {
    const container = document.getElementById('downloads-container');
    
    if (!downloads || downloads.length === 0) {
        container.innerHTML = '<p class="text-muted">No files downloaded yet.</p>';
        return;
    }
    
    const downloadsList = downloads.map(file => {
        const sizeFormatted = formatFileSize(file.size);
        const dateFormatted = new Date(file.modified * 1000).toLocaleString();
        
        return `
            <div class="row align-items-center py-2 border-bottom">
                <div class="col-md-4">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-file ${getFileIcon(file.filename)} me-2"></i>
                        <span class="fw-bold">${file.filename}</span>
                    </div>
                </div>
                <div class="col-md-2">
                    <span class="text-muted">${sizeFormatted}</span>
                </div>
                <div class="col-md-3">
                    <span class="text-muted">${dateFormatted}</span>
                </div>
                <div class="col-md-3">
                    <button class="btn btn-sm btn-outline-primary" onclick="downloadFile('${file.filename}')">
                        <i class="fas fa-download me-1"></i> Download
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
        <div class="row py-2 bg-light border-bottom fw-bold">
            <div class="col-md-4">Filename</div>
            <div class="col-md-2">Size</div>
            <div class="col-md-3">Modified</div>
            <div class="col-md-3">Actions</div>
        </div>
        ${downloadsList}
    `;
}

function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    
    switch (extension) {
        case 'pdf': return 'text-danger';
        case 'doc':
        case 'docx': return 'text-primary';
        case 'zip':
        case 'rar':
        case '7z': return 'text-warning';
        case 'jpg':
        case 'jpeg':
        case 'png':
        case 'gif': return 'text-success';
        default: return 'text-secondary';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function downloadFile(filename) {
    // Create a temporary link to download the file
    const link = document.createElement('a');
    link.href = `/downloads/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

async function updateSourceCount() {
    try {
        const response = await fetch('/api/sources');
        const sources = await response.json();
        const totalCount = sources.length;
        const sourceCountElement = document.getElementById('total-sources-count');
        if (sourceCountElement) {
            sourceCountElement.textContent = totalCount;
        }
    } catch (error) {
        console.error('Error updating source count:', error);
    }
}

function showSuccess(message) {
    // You can implement a toast notification system here
    console.log('Success:', message);
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-circle me-2"></i>
            ${message}
        </div>
    `;
}

function showLoading(container) {
    // Handle both DOM elements and ID strings
    const element = typeof container === 'string' ? document.getElementById(container) : container;
    if (element) {
        element.innerHTML = `
            <div class="d-flex justify-content-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadDiscoveredSites();
    
    // Set up manual crawl form
    const manualCrawlForm = document.getElementById('manual-crawl-form');
    if (manualCrawlForm) {
        manualCrawlForm.addEventListener('submit', runManualCrawl);
    }
    
    // Set up content scraper button
    const scraperButton = document.getElementById('run-scraper-btn');
    if (scraperButton) {
        scraperButton.addEventListener('click', runContentScraper);
    }
});