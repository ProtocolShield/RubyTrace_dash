// Threat News Feed JavaScript

// API URLs
const NEWS_API_URL = '/api/news';

// DOM elements
const newsContainer = document.getElementById('news-container');
const refreshNewsBtn = document.getElementById('refresh-news-btn');
const addNewsBtn = document.getElementById('add-news-btn');
const newsRiskFilter = document.getElementById('news-risk-filter');
const newsSearch = document.getElementById('news-search');
const newsLimit = document.getElementById('news-limit');
const newsFilterBtn = document.getElementById('news-filter-btn');

// Current state
let currentNews = [];
let filteredNews = [];

// Initialize Threat News
function initThreatNews() {
    console.log('Initializing Threat News...');
    
    // Add event listeners
    if (refreshNewsBtn) refreshNewsBtn.addEventListener('click', loadNews);
    if (addNewsBtn) addNewsBtn.addEventListener('click', showAddNewsModal);
    if (newsFilterBtn) newsFilterBtn.addEventListener('click', applyNewsFilters);
    
    // Add search functionality
    if (newsSearch) {
        newsSearch.addEventListener('input', debounce(applyNewsFilters, 300));
    }
    
    // Load initial data
    loadNews();
}

// Load news from API
async function loadNews() {
    try {
        showLoading(newsContainer);
        
        const limit = newsLimit ? newsLimit.value : 50;
        const response = await fetch(`${NEWS_API_URL}?limit=${limit}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        currentNews = await response.json();
        filteredNews = [...currentNews];
        
        renderNews();
        
    } catch (error) {
        console.error('Error loading news:', error);
        showError(newsContainer, 'Failed to load news. Please try again.');
    }
}

// Apply filters to news
function applyNewsFilters() {
    const riskFilter = newsRiskFilter ? newsRiskFilter.value : '';
    const searchTerm = newsSearch ? newsSearch.value.toLowerCase() : '';
    
    filteredNews = currentNews.filter(news => {
        // Risk filter
        if (riskFilter && news.risk_level !== riskFilter) {
            return false;
        }
        
        // Search filter
        if (searchTerm) {
            const searchText = `${news.title} ${news.summary || ''} ${news.tags || ''}`.toLowerCase();
            if (!searchText.includes(searchTerm)) {
                return false;
            }
        }
        
        return true;
    });
    
    renderNews();
}

// Render news in the container
function renderNews() {
    if (!newsContainer) return;
    
    if (filteredNews.length === 0) {
        newsContainer.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-newspaper fa-3x mb-3"></i>
                <p>No news found matching your criteria.</p>
            </div>
        `;
        return;
    }
    
    const newsHtml = filteredNews.map(news => `
        <div class="card mb-3 news-card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                    ${news.risk_level ? `<span class="badge bg-${getRiskColor(news.risk_level)} me-2">${news.risk_level}</span>` : ''}
                    <strong>${news.title}</strong>
                </h6>
                <div>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewNewsDetails('${news.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </div>
            <div class="card-body">
                <p class="card-text text-muted">
                    ${news.summary ? news.summary.substring(0, 300) + '...' : 'No summary available'}
                </p>
                <div class="row">
                    <div class="col-md-6">
                        <small class="text-muted">
                            <i class="fas fa-calendar me-1"></i>
                            Published: ${formatDate(news.published_at)}
                        </small>
                    </div>
                    <div class="col-md-6">
                        <small class="text-muted">
                            <i class="fas fa-tags me-1"></i>
                            Tags: ${news.tags || 'None'}
                        </small>
                    </div>
                </div>
                ${news.source_name ? `
                <div class="mt-2">
                    <small class="text-muted">
                        <i class="fas fa-newspaper me-1"></i>
                        Source: ${news.source_name}
                    </small>
                </div>
                ` : ''}
            </div>
            <div class="card-footer">
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>
                        Added: ${formatDate(news.created_at)}
                    </small>
                    ${news.url ? `
                    <a href="${news.url}" target="_blank" class="btn btn-sm btn-outline-secondary">
                        <i class="fas fa-external-link-alt me-1"></i> Read Full Article
                    </a>
                    ` : ''}
                </div>
            </div>
        </div>
    `).join('');
    
    newsContainer.innerHTML = newsHtml;
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

// Show news details modal
function viewNewsDetails(newsId) {
    const news = currentNews.find(n => n.id === parseInt(newsId));
    if (!news) return;
    
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="news-details-modal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            ${news.risk_level ? `<span class="badge bg-${getRiskColor(news.risk_level)} me-2">${news.risk_level}</span>` : ''}
                            ${news.title}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="text-muted">${news.summary || 'No summary available'}</p>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <strong>Published:</strong> ${formatDate(news.published_at)}<br>
                                <strong>Added:</strong> ${formatDate(news.created_at)}
                            </div>
                            <div class="col-md-6">
                                <strong>Tags:</strong> ${news.tags || 'None'}<br>
                                <strong>Source:</strong> ${news.source_name || 'Unknown'}
                            </div>
                        </div>
                        
                        ${news.url ? `
                        <div class="mt-3">
                            <a href="${news.url}" target="_blank" class="btn btn-primary">
                                <i class="fas fa-external-link-alt me-1"></i> Read Full Article
                            </a>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('news-details-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('news-details-modal'));
    modal.show();
    
    // Clean up modal after hiding
    document.getElementById('news-details-modal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Show add news modal
function showAddNewsModal() {
    const modalHtml = `
        <div class="modal fade" id="add-news-modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Add News Article</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="add-news-form">
                            <div class="mb-3">
                                <label for="news-title-input" class="form-label">Title</label>
                                <input type="text" class="form-control" id="news-title-input" placeholder="News title" required>
                            </div>
                            <div class="mb-3">
                                <label for="news-summary-input" class="form-label">Summary</label>
                                <textarea class="form-control" id="news-summary-input" rows="3" placeholder="Brief summary of the news"></textarea>
                            </div>
                            <div class="mb-3">
                                <label for="news-url-input" class="form-label">URL</label>
                                <input type="url" class="form-control" id="news-url-input" placeholder="https://example.com/article">
                            </div>
                            <div class="mb-3">
                                <label for="news-source-input" class="form-label">Source Name</label>
                                <input type="text" class="form-control" id="news-source-input" placeholder="News source name">
                            </div>
                            <div class="mb-3">
                                <label for="news-risk-input" class="form-label">Risk Level</label>
                                <select class="form-select" id="news-risk-input">
                                    <option value="">Select risk level</option>
                                    <option value="high">High</option>
                                    <option value="medium">Medium</option>
                                    <option value="low">Low</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label for="news-tags-input" class="form-label">Tags</label>
                                <input type="text" class="form-control" id="news-tags-input" placeholder="cybersecurity, breach, malware">
                            </div>
                            <div class="mb-3">
                                <label for="news-published-input" class="form-label">Published Date</label>
                                <input type="datetime-local" class="form-control" id="news-published-input">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="save-news-btn">Save News</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('add-news-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('add-news-modal'));
    modal.show();
    
    // Add save event listener
    document.getElementById('save-news-btn').addEventListener('click', saveNews);
    
    // Clean up modal after hiding
    document.getElementById('add-news-modal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Save new news
async function saveNews() {
    const newsData = {
        title: document.getElementById('news-title-input').value,
        summary: document.getElementById('news-summary-input').value,
        url: document.getElementById('news-url-input').value,
        source_name: document.getElementById('news-source-input').value,
        risk_level: document.getElementById('news-risk-input').value,
        tags: document.getElementById('news-tags-input').value,
        published_at: document.getElementById('news-published-input').value
    };
    
    try {
        const response = await fetch(NEWS_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newsData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Close modal and reload data
        bootstrap.Modal.getInstance(document.getElementById('add-news-modal')).hide();
        loadNews();
        
        // Show success message
        showSuccess('News article added successfully!');
        
    } catch (error) {
        console.error('Error saving news:', error);
        showError('Failed to save news. Please try again.');
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
window.initThreatNews = initThreatNews;
window.loadNews = loadNews; 