// Privacy OSINT Dashboard JavaScript

// API URLs
const API_BASE_URL = '/api';
const POSTS_URL = `${API_BASE_URL}/posts`;
const SOURCES_URL = `${API_BASE_URL}/posts/sources`;
const SEARCH_URL = `${API_BASE_URL}/posts/search`;
const SENTIMENT_URL = `${API_BASE_URL}/posts/sentiment`;
const KEYWORDS_URL = `${API_BASE_URL}/config/keywords`;
const CONFIG_SOURCES_URL = `${API_BASE_URL}/config/sources`;
const REDDIT_SOURCES_URL = `${API_BASE_URL}/config/sources/reddit`;
const ADD_SOURCE_URL = `${API_BASE_URL}/config/sources/add`;
// API_KEYS_URL is defined in settings.js
// Search API Endpoints defined in search.js

// DOM elements
const navLinks = document.querySelectorAll('.nav-link');
const viewSections = document.querySelectorAll('.view-section');
const postsContainer = document.getElementById('posts-container');
const sourceFilter = document.getElementById('source-filter');
const sentimentFilter = document.getElementById('sentiment-filter');
const postsLimit = document.getElementById('posts-limit');
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const refreshBtn = document.getElementById('refresh-btn');
const keywordsContainer = document.getElementById('keywords-container');
const newKeywordInput = document.getElementById('new-keyword-input');
const addKeywordBtn = document.getElementById('add-keyword-btn');
const saveKeywordsBtn = document.getElementById('save-keywords-btn');
const sourcesContainer = document.getElementById('sources-container');

// Sources related DOM elements
const defaultSourcesContainer = document.getElementById('default-sources-container');
const redditSourcesContainer = document.getElementById('reddit-sources-container');
const customSourcesContainer = document.getElementById('custom-sources-container');
const sourceTypeSelect = document.getElementById('source-type');
const redditFields = document.getElementById('reddit-fields');
const customFields = document.getElementById('custom-fields');
const subredditNameInput = document.getElementById('subreddit-name');
const sourceIdInput = document.getElementById('source-id');
const sourceNameInput = document.getElementById('source-name');
const sourceUrlInput = document.getElementById('source-url');
const saveSourceBtn = document.getElementById('save-source-btn');
const redditEditList = document.getElementById('reddit-edit-list');
const newSubredditInput = document.getElementById('new-subreddit');
const addSubredditBtn = document.getElementById('add-subreddit-btn');
const saveSubredditsBtn = document.getElementById('save-subreddits-btn');

// Search tools related DOM elements
const emailSearchForm = document.getElementById('email-search-form');
const emailInput = document.getElementById('email-input');
const emailResults = document.getElementById('email-results');
const emailResultsContent = document.getElementById('email-results-content');
const phoneSearchForm = document.getElementById('phone-search-form');
const phoneInput = document.getElementById('phone-input');
const phoneResults = document.getElementById('phone-results');
const phoneResultsContent = document.getElementById('phone-results-content');

// Current state
let currentKeywords = [];
let isKeywordsModified = false;
let currentSubreddits = [];
let isSubredditsModified = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing dashboard...');
    
    // Initialize navigation first
    initNavigation();
    
    // Initialize event listeners
    initEventListeners();
    
    // Load data in proper order
    setTimeout(() => {
        loadSources();
        loadPosts();
        loadSourcesForFilter();
        initKeywords();
        initSearchTools();
        initDownloadsSystem();
        initTorControls();

        // Initialize file upload system
        initFileUploadSystem();

        // Initialize crawler if the function exists
        if (typeof initCrawler === 'function') {
            initCrawler();
        }

        // Add event listener for the new dynamic API manager button
        const apiManagerBtn = document.getElementById('dynamic-api-manager-btn');
        if (apiManagerBtn) {
            apiManagerBtn.addEventListener('click', () => {
                // For now, just alert. Later, implement modal or navigation to API manager UI
                alert('Dynamic API Manager button clicked. Implement UI navigation or modal here.');
            });
        }
    }, 100); // Small delay to ensure DOM is fully ready
    
    // Initialize source management components
    if (sourceTypeSelect) {
        sourceTypeSelect.addEventListener('change', () => {
            const selectedType = sourceTypeSelect.value;
            redditFields.style.display = selectedType === 'reddit' ? 'block' : 'none';
            customFields.style.display = selectedType === 'custom' ? 'block' : 'none';
        });
    }
    
    // Load data for current view based on hash
    if (window.location.hash === '#sources-view') {
        loadConfiguredSources();
    } else if (window.location.hash === '#settings-view') {
        // Load API keys
        if (typeof loadApiKeys === 'function') {
            loadApiKeys();
        }
        
        // Load schedule information
        if (typeof loadScheduleInfo === 'function') {
            loadScheduleInfo();
        }
    } else if (window.location.hash === '#alerts-view') {
        // Load alerts
        if (typeof loadAlerts === 'function') {
            loadAlerts();
        }
    }
});

// Initialize navigation between views
function initNavigation() {
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Update active nav link
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Show corresponding view
            const viewToShow = link.getAttribute('data-view');
            viewSections.forEach(section => {
                section.classList.remove('active-view');
                if (section.id === `${viewToShow}-view`) {
                    section.classList.add('active-view');
                }
            });
            
            // Load data for the view if needed
            if (viewToShow === 'posts') {
                console.log('Posts view selected, calling loadPosts()');
                loadPosts();
                loadSourcesForFilter();
            } else if (viewToShow === 'sources') {
                console.log('Sources view selected, calling loadSourcesList()');
                loadSourcesList();
            } else if (viewToShow === 'settings') {
                loadApiKeys();
                // Load schedule information if the function exists
                if (typeof loadScheduleInfo === 'function') {
                    loadScheduleInfo();
                }
            } else if (viewToShow === 'alerts') {
                // Load alerts if the function exists
                if (typeof loadAlerts === 'function') {
                    loadAlerts();
                }
            } else if (viewToShow === 'logs') {
                // Load logs if the function exists
                if (typeof initLogs === 'function') {
                    initLogs();
                }
            } else if (viewToShow === 'crawler') {
                // Initialize crawler interface
                if (typeof initCrawler === 'function') {
                    initCrawler();
                } else if (typeof loadCrawlerStatus === 'function') {
                    loadCrawlerStatus();
                }
                // Also load discovered sites
                if (typeof loadDiscoveredSites === 'function') {
                    loadDiscoveredSites();
                }
            } else if (viewToShow === 'downloads') {
                // Load downloads if the function exists
                if (typeof loadDownloads === 'function') {
                    loadDownloads();
                }
            } else if (viewToShow === 'cve-monitor') {
                // Initialize CVE Monitor
                if (typeof initCveMonitor === 'function') {
                    initCveMonitor();
                }
            } else if (viewToShow === 'threat-news') {
                // Initialize Threat News
                if (typeof initThreatNews === 'function') {
                    initThreatNews();
                }
            } else if (viewToShow === 'tools-scripts') {
                // Initialize Tools & Scripts
                if (typeof initToolsScripts === 'function') {
                    initToolsScripts();
                }
            } else if (viewToShow === 'file-upload') {
                // Load file uploads
                loadFileUploads();
            }
        });
    });
}

// Load sources for filter dropdown
async function loadSourcesForFilter() {
    try {
        const response = await fetch(SOURCES_URL);
        const sources = await response.json();
        
        if (sourceFilter) {
            sourceFilter.innerHTML = '<option value="">All Sources</option>';
            sources.forEach(source => {
                const option = document.createElement('option');
                option.value = source;
                option.textContent = source;
                sourceFilter.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading sources for filter:', error);
    }
}

// Initialize event listeners
function initEventListeners() {
    // Filter change events
    if (sourceFilter) sourceFilter.addEventListener('change', loadPosts);
    if (sentimentFilter) sentimentFilter.addEventListener('change', loadPosts);
    if (postsLimit) postsLimit.addEventListener('change', loadPosts);
    
    // Search form submit
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = searchInput ? searchInput.value.trim() : '';
            if (query) {
                searchPosts(query);
            } else {
                loadPosts();
            }
        });
    }
    
    // Refresh button
    if (refreshBtn) refreshBtn.addEventListener('click', loadPosts);

    // Export CSV button
    const exportCsvBtn = document.getElementById('export-csv-btn');
    if (exportCsvBtn) exportCsvBtn.addEventListener('click', exportCsv);
    
    // Keyword management
    if (addKeywordBtn) addKeywordBtn.addEventListener('click', addNewKeyword);
    if (saveKeywordsBtn) saveKeywordsBtn.addEventListener('click', saveKeywords);
    if (newKeywordInput) {
        newKeywordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                addNewKeyword();
            }
        });
    }
    
    // Source management
    sourceTypeSelect.addEventListener('change', () => {
        const selectedType = sourceTypeSelect.value;
        redditFields.style.display = selectedType === 'reddit' ? 'block' : 'none';
        customFields.style.display = selectedType === 'custom' ? 'block' : 'none';
    });
    
    saveSourceBtn.addEventListener('click', addNewSource);
    
    // Reddit subreddit management
    addSubredditBtn.addEventListener('click', addSubreddit);
    saveSubredditsBtn.addEventListener('click', saveSubreddits);
    newSubredditInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addSubreddit();
        }
    });

    // File upload management
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFileUpload);
    }
    const refreshUploadsBtn = document.getElementById('refresh-uploads-btn');
    if (refreshUploadsBtn) {
        refreshUploadsBtn.addEventListener('click', loadFileUploads);
    }
    const uploadsRiskFilter = document.getElementById('uploads-risk-filter');
    const uploadsLimit = document.getElementById('uploads-limit');
    if (uploadsRiskFilter) uploadsRiskFilter.addEventListener('change', loadFileUploads);
    if (uploadsLimit) uploadsLimit.addEventListener('change', loadFileUploads);
}

// Load posts with current filters
async function loadPosts() {
    console.log('Loading posts...');
    const container = document.getElementById('posts-container');
    if (!container) {
        console.error('Posts container not found');
        return;
    }
    
    showLoading(container);
    
    try {
        let url = POSTS_URL;
        const params = new URLSearchParams();
        
        const source = sourceFilter ? sourceFilter.value : '';
        if (source) {
            params.append('source', source);
        }
        
        const limit = postsLimit ? postsLimit.value : '';
        if (limit) {
            params.append('limit', limit);
        }
        
        const sentiment = sentimentFilter ? sentimentFilter.value : '';
        if (sentiment) {
            url = `${SENTIMENT_URL}?sentiment=${sentiment}`;
            // Add other params if needed
            if (source) {
                url += `&source=${encodeURIComponent(source)}`;
            }
            if (limit) {
                url += `&limit=${limit}`;
            }
        } else if (params.toString()) {
            url += `?${params.toString()}`;
        }
        
        console.log('Fetching posts from:', url);
        const response = await fetch(url, {
            headers: {
                'Accept': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Expected JSON but got:', text.substring(0, 200));
            throw new Error('Server returned non-JSON response');
        }
        
        const posts = await response.json();
        console.log('Received posts:', posts.length);
        
        renderPosts(posts);
    } catch (error) {
        console.error('Error loading posts:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Error loading posts: ${error.message}
                <button class="btn btn-sm btn-outline-danger ms-2" onclick="loadPosts()">Retry</button>
            </div>
        `;
    }
}

// Search for posts
async function searchPosts(query) {
    showLoading(postsContainer);

    try {
        const url = `${SEARCH_URL}?q=${encodeURIComponent(query)}`;
        const response = await fetch(url);
        const posts = await response.json();

        renderPosts(posts);
    } catch (error) {
        console.error('Error searching posts:', error);
        postsContainer.innerHTML = `
            <div class="alert alert-danger">
                Error searching posts: ${error.message}
            </div>
        `;
    }
}

// Export posts to CSV
async function exportCsv() {
    try {
        // Get current filter parameters
        const source = sourceFilter ? sourceFilter.value : '';
        const sentiment = sentimentFilter ? sentimentFilter.value : '';
        const limit = postsLimit ? postsLimit.value : '';

        // Build URL with current filters
        let url = '/api/export/posts/csv';
        const params = new URLSearchParams();

        if (source) params.append('source', source);
        if (sentiment) params.append('sentiment', sentiment);
        if (limit) params.append('limit', limit);

        if (params.toString()) {
            url += '?' + params.toString();
        }

        // Create a temporary link to download the CSV
        const link = document.createElement('a');
        link.href = url;
        link.download = 'posts_export.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Show success message
        showToast('Posts exported successfully!', 'success');
    } catch (error) {
        console.error('Error exporting CSV:', error);
        showToast('Error exporting posts: ' + error.message, 'error');
    }
}

// Render posts to the container
function renderPosts(posts) {
    if (!posts || posts.length === 0) {
        postsContainer.innerHTML = `
            <div class="alert alert-info">
                No posts found matching the criteria.
            </div>
        `;
        return;
    }
    
    let html = '';
    
    posts.forEach(post => {
        // Determine sentiment class
        const sentimentClass = `sentiment-badge-${post.sentiment?.assessment || 'neutral'}`;
        
        // Format date (assuming ISO format)
        let formattedDate = post.timestamp;
        try {
            const date = new Date(post.timestamp);
            if (!isNaN(date)) {
                formattedDate = date.toLocaleString();
            }
        } catch (e) {
            // Keep original format if parsing fails
        }
        
        // Prepare keywords display
        const keywordsHtml = post.keywords && post.keywords.length > 0
            ? post.keywords.map(k => `<span class="badge bg-secondary">${k}</span>`).join(' ')
            : '<span class="text-muted">No keywords</span>';
        
        html += `
            <div class="card post-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h5 class="card-title mb-0">${post.title}</h5>
                        <span class="badge ${sentimentClass}">${post.sentiment?.assessment || 'neutral'}</span>
                    </div>
                    <h6 class="card-subtitle mb-2 text-muted">${post.source} • ${formattedDate}</h6>
                    <p class="card-text">${post.summary}</p>
                    <div class="keywords-list mb-2">
                        ${keywordsHtml}
                    </div>
                    <a href="${post.url}" target="_blank" class="card-link">View Original <i class="fas fa-external-link-alt"></i></a>
                </div>
            </div>
        `;
    });
    
    postsContainer.innerHTML = html;
}

// Load available sources
async function loadSources() {
    console.log('Loading sources...');
    const container = document.getElementById('sources-container');
    if (!container) {
        console.error('Sources container not found');
        return;
    }
    
    showLoading(container);
    
    try {
        const response = await fetch('/api/sources', {
            headers: {
                'Accept': 'application/json'
            }
        });
        
        console.log('Sources response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Received sources:', data.length);
        
        renderSourcesList(data, container);
        
    } catch (error) {
        console.error('Error loading sources:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Error loading sources: ${error.message}
                <button class="btn btn-sm btn-outline-danger ms-2" onclick="loadSources()">Retry</button>
            </div>
        `;
    }
}

// Render sources list to container
function renderSourcesList(sources, container) {
    if (!sources || sources.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No sources configured yet.
            </div>
        `;
        return;
    }
    
    let html = '<div class="row g-3">';
    
    sources.forEach(source => {
        const statusClass = source.enabled ? 'text-success' : 'text-muted';
        const statusIcon = source.enabled ? 'fa-check-circle' : 'fa-pause-circle';
        const typeClass = getTypeClass(source.source_type);
        const riskClass = getRiskClass(source.risk_level);
        
        html += `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0">${source.name}</h6>
                            <i class="fas ${statusIcon} ${statusClass}"></i>
                        </div>
                        <div class="mb-2">
                            <span class="badge ${typeClass} me-1">${source.source_type}</span>
                            <span class="badge ${riskClass}">${source.risk_level} risk</span>
                        </div>
                        <p class="card-text small text-muted">${source.url}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">Every ${source.scrape_interval || 60}min</small>
                            <div class="btn-group btn-group-sm">
                                <button class="btn btn-outline-primary" onclick="editSource(${source.id})" title="Edit">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-outline-danger" onclick="deleteSource(${source.id})" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Helper functions for styling
function getTypeClass(type) {
    const classes = {
        'forum': 'bg-primary',
        'news': 'bg-info',
        'pastebin': 'bg-warning',
        'darkweb': 'bg-dark'
    };
    return classes[type] || 'bg-secondary';
}

function getRiskClass(risk) {
    const classes = {
        'low': 'bg-success',
        'medium': 'bg-warning',
        'high': 'bg-danger'
    };
    return classes[risk] || 'bg-secondary';
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

// Edit source function
function editSource(sourceId) {
    alert(`Edit source ${sourceId} - Feature coming soon`);
}

// Delete source function
async function deleteSource(sourceId) {
    if (!confirm('Are you sure you want to delete this source?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/config/sources/${sourceId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadSourcesList();
        } else {
            alert('Error deleting source');
        }
    } catch (error) {
        console.error('Error deleting source:', error);
        alert('Error deleting source');
    }
}

// Cache for sources data
let sourcesCache = null;
let sourcesCacheTime = 0;
const CACHE_DURATION = 30000; // 30 seconds

// Load and display sources list in the sources view
async function loadSourcesList(forceRefresh = false) {
    console.log('Loading sources list...');
    const container = document.getElementById('sources-container');
    if (!container) {
        console.error('Sources container not found');
        return;
    }
    
    // Check cache first
    const now = Date.now();
    if (!forceRefresh && sourcesCache && (now - sourcesCacheTime) < CACHE_DURATION) {
        console.log('Using cached sources data');
        renderSourcesList(sourcesCache, container);
        return;
    }
    
    showLoading(container);
    
    try {
        console.log('Fetching sources from API...');
        const response = await fetch('/api/config/sources/db', {
            headers: {
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Expected JSON but got:', text.substring(0, 200));
            throw new Error('Server returned non-JSON response');
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        // Cache the data
        sourcesCache = data.sources || [];
        sourcesCacheTime = now;
        
        renderSourcesList(sourcesCache, container);
        
    } catch (error) {
        console.error('Error loading sources list:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Error loading sources: ${error.message}
                <button class="btn btn-sm btn-outline-danger ms-2" onclick="loadSourcesList(true)">Retry</button>
            </div>
        `;
    }
}

function renderSourcesList(sources, container) {
    if (!sources || sources.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i> No sources configured yet.
            </div>
        `;
        return;
    }
    
    let html = `
            <div class="table-responsive">
                <table class="table table-bordered table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Name</th>
                            <th>URL</th>
                            <th>Type</th>
                            <th>Risk Level</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        sources.forEach(source => {
            // Determine icon and color based on source type
            let typeIcon = 'fa-globe';
            let typeColor = 'text-primary';
            
            if (source.source_type === 'forum') {
                typeIcon = 'fa-comments';
                typeColor = 'text-info';
            } else if (source.source_type === 'news') {
                typeIcon = 'fa-newspaper';
                typeColor = 'text-success';
            } else if (source.source_type === 'darkweb') {
                typeIcon = 'fa-user-secret';
                typeColor = 'text-warning';
            }
            
            const statusBadge = source.enabled ? 
                '<span class="badge bg-success">Active</span>' : 
                '<span class="badge bg-secondary">Disabled</span>';
                
            const riskBadge = {
                'low': '<span class="badge bg-success">Low</span>',
                'medium': '<span class="badge bg-warning">Medium</span>',
                'high': '<span class="badge bg-danger">High</span>'
            }[source.risk_level] || '<span class="badge bg-secondary">Unknown</span>';
            
            html += `
                <tr>
                    <td>
                        <i class="fas ${typeIcon} ${typeColor} me-2"></i>
                        ${source.name}
                    </td>
                    <td>
                        <a href="${source.url}" target="_blank" class="text-decoration-none">
                            ${source.url.length > 50 ? source.url.substring(0, 50) + '...' : source.url}
                            <i class="fas fa-external-link-alt ms-1"></i>
                        </a>
                    </td>
                    <td>${source.source_type}</td>
                    <td>${riskBadge}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <button class="btn btn-sm btn-primary me-1" onclick="editSource(${source.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteSource(${source.id})">
                            <i class="fas fa-trash"></i>
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
        
        container.innerHTML = html;
        console.log('Sources rendered successfully');
}

// Initialize keywords management
async function initKeywords() {
    await loadKeywords();
    renderKeywords();
}

// Load keywords from the API
async function loadKeywords() {
    showLoading(keywordsContainer);
    
    try {
        const response = await fetch(KEYWORDS_URL);
        currentKeywords = await response.json();
        isKeywordsModified = false;
        renderKeywords();
    } catch (error) {
        console.error('Error loading keywords:', error);
        keywordsContainer.innerHTML = `
            <div class="alert alert-danger">
                Error loading keywords: ${error.message}
            </div>
        `;
    }
}

// Render keywords as chips
function renderKeywords() {
    if (!currentKeywords || currentKeywords.length === 0) {
        keywordsContainer.innerHTML = `
            <div class="alert alert-info">
                No keywords defined. Add some keywords to filter content.
            </div>
        `;
        return;
    }
    
    let html = '';
    
    currentKeywords.forEach(keyword => {
        html += `
            <div class="keyword-chip">
                ${keyword}
                <span class="remove-keyword" data-keyword="${keyword}" title="Remove keyword">
                    <i class="fas fa-times"></i>
                </span>
            </div>
        `;
    });
    
    keywordsContainer.innerHTML = html;
    
    // Add event listeners to removal buttons
    document.querySelectorAll('.remove-keyword').forEach(btn => {
        btn.addEventListener('click', () => {
            const keyword = btn.getAttribute('data-keyword');
            removeKeyword(keyword);
        });
    });
    
    // Update save button state
    saveKeywordsBtn.disabled = !isKeywordsModified;
}

// Add a new keyword
function addNewKeyword() {
    const keyword = newKeywordInput.value.trim().toLowerCase();
    
    if (!keyword) {
        return;  // Ignore empty input
    }
    
    if (!currentKeywords.includes(keyword)) {
        currentKeywords.push(keyword);
        isKeywordsModified = true;
        renderKeywords();
        newKeywordInput.value = '';
    } else {
        // Alert that keyword already exists
        alert(`Keyword "${keyword}" already exists.`);
    }
    
    newKeywordInput.focus();
}

// Remove a keyword
function removeKeyword(keyword) {
    const index = currentKeywords.indexOf(keyword);
    if (index !== -1) {
        currentKeywords.splice(index, 1);
        isKeywordsModified = true;
        renderKeywords();
    }
}

// Save keywords to the API
async function saveKeywords() {
    try {
        const response = await fetch(KEYWORDS_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keywords: currentKeywords })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Keywords saved successfully!');
            isKeywordsModified = false;
            saveKeywordsBtn.disabled = true;
        } else {
            throw new Error(result.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error saving keywords:', error);
        alert(`Error saving keywords: ${error.message}`);
    }
}

// Load and display configured sources in the sources management view
async function loadConfiguredSources() {
    showLoading(defaultSourcesContainer);
    showLoading(redditSourcesContainer);
    
    try {
        // Fetch the configuration
        const response = await fetch(CONFIG_SOURCES_URL);
        const sources = await response.json();
        
        // Display default sources
        if (sources.default_sources) {
            let html = '<div class="list-group">';
            
            Object.entries(sources.default_sources).forEach(([id, source]) => {
                const iconClass = getSourceIconClass(source.name);
                
                html += `
                    <div class="list-group-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <i class="fab ${iconClass} me-2"></i>
                                <strong>${source.name}</strong>
                            </div>
                            <span class="badge bg-secondary">${source.type}</span>
                        </div>
                        <div class="mt-2">
                            <small class="text-muted">${source.url}</small>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            defaultSourcesContainer.innerHTML = html;
        } else {
            defaultSourcesContainer.innerHTML = '<p class="text-muted">No default sources configured.</p>';
        }
        
        // Display Reddit subreddits and store them for later use
        loadRedditSubreddits(sources.reddit_subreddits);
        
        // Display custom sources
        if (sources.custom_sources && Object.keys(sources.custom_sources).length > 0) {
            let html = '<div class="list-group">';
            
            Object.entries(sources.custom_sources).forEach(([id, source]) => {
                const iconClass = getSourceIconClass(source.name);
                
                html += `
                    <div class="list-group-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <i class="fab ${iconClass} me-2"></i>
                                <strong>${source.name}</strong>
                            </div>
                            <span class="badge bg-secondary">${source.type}</span>
                        </div>
                        <div class="mt-2">
                            <small class="text-muted">${source.url}</small>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            customSourcesContainer.innerHTML = html;
        } else {
            customSourcesContainer.innerHTML = '<p class="text-muted">No custom sources configured yet.</p>';
        }
    } catch (error) {
        console.error('Error loading configured sources:', error);
        defaultSourcesContainer.innerHTML = `
            <div class="alert alert-danger">
                Error loading sources: ${error.message}
            </div>
        `;
    }
    
    // Load database sources after the built-in sources
    loadDatabaseSources();
}

// Load and display database sources with type and risk level information
async function loadDatabaseSources() {
    try {
        // Fetch database sources
        const response = await fetch('/api/sources');
        const sources = await response.json();
        
        if (sources && sources.length > 0) {
            let html = '<div class="list-group">';
            
            sources.forEach(source => {
                // Determine icon based on source type
                let iconClass = 'fa-globe';
                if (source.source_type === 'forum') {
                    iconClass = 'fa-comments';
                } else if (source.source_type === 'news') {
                    iconClass = 'fa-newspaper';
                } else if (source.source_type === 'pastebin') {
                    iconClass = 'fa-paste';
                } else if (source.source_type === 'darkweb') {
                    iconClass = 'fa-user-secret';
                }
                
                // Determine badge color based on risk level
                let riskBadgeClass = 'bg-info';
                if (source.risk_level === 'low') {
                    riskBadgeClass = 'bg-success';
                } else if (source.risk_level === 'medium') {
                    riskBadgeClass = 'bg-warning';
                } else if (source.risk_level === 'high') {
                    riskBadgeClass = 'bg-danger';
                }
                
                html += `
                    <div class="list-group-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <i class="fas ${iconClass} me-2"></i>
                                <strong>${source.name}</strong>
                            </div>
                            <div>
                                <span class="badge bg-secondary me-1" title="Source Type">${source.source_type}</span>
                                <span class="badge ${riskBadgeClass}" title="Risk Level">${source.risk_level}</span>
                            </div>
                        </div>
                        <div class="mt-2 d-flex justify-content-between align-items-center">
                            <small class="text-muted">${source.url}</small>
                            <div>
                                <button class="btn btn-sm btn-outline-secondary me-1" onclick="editSource(${source.id})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteSource(${source.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            customSourcesContainer.innerHTML = html;
        } else {
            customSourcesContainer.innerHTML = '<p class="text-muted">No custom sources configured yet.</p>';
        }
    } catch (error) {
        console.error('Error loading database sources:', error);
        customSourcesContainer.innerHTML = `
            <div class="alert alert-danger">
                Error loading database sources: ${error.message}
            </div>
        `;
    }
}

// Get icon class based on source name
function getSourceIconClass(sourceName) {
    const name = sourceName.toLowerCase();
    if (name.includes('reddit')) {
        return 'fa-reddit source-icon-reddit';
    } else if (name.includes('hacker')) {
        return 'fa-hacker-news source-icon-hackernews';
    } else if (name.includes('privacy')) {
        return 'fa-shield-alt source-icon-privacyguides';
    }
    return 'fa-globe source-icon-default';
}

// Load and display Reddit subreddits
async function loadRedditSubreddits(subreddits = null) {
    try {
        if (!subreddits) {
            // Fetch the subreddits if not provided
            const response = await fetch(REDDIT_SOURCES_URL);
            subreddits = await response.json();
        }
        
        // Store subreddits for later use
        currentSubreddits = [...subreddits];
        isSubredditsModified = false;
        
        // Display in the sources list
        let html = '<div class="list-group">';
        
        subreddits.forEach(subreddit => {
            html += `
                <div class="list-group-item">
                    <div class="d-flex align-items-center">
                        <i class="fab fa-reddit source-icon-reddit me-2"></i>
                        <span>r/${subreddit}</span>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        redditSourcesContainer.innerHTML = html;
        
        // Display in the edit modal
        renderRedditEditList();
    } catch (error) {
        console.error('Error loading Reddit subreddits:', error);
        redditSourcesContainer.innerHTML = `
            <div class="alert alert-danger">
                Error loading Reddit subreddits: ${error.message}
            </div>
        `;
    }
}

// Render the editable Reddit subreddits list
function renderRedditEditList() {
    if (!currentSubreddits || currentSubreddits.length === 0) {
        redditEditList.innerHTML = `
            <div class="alert alert-info">
                No subreddits configured. Add some below.
            </div>
        `;
        return;
    }
    
    let html = '';
    
    currentSubreddits.forEach(subreddit => {
        html += `
            <div class="reddit-chip">
                r/${subreddit}
                <span class="remove-subreddit" data-subreddit="${subreddit}" title="Remove subreddit">
                    <i class="fas fa-times"></i>
                </span>
            </div>
        `;
    });
    
    redditEditList.innerHTML = html;
    
    // Add event listeners to removal buttons
    document.querySelectorAll('.remove-subreddit').forEach(btn => {
        btn.addEventListener('click', () => {
            const subreddit = btn.getAttribute('data-subreddit');
            removeSubreddit(subreddit);
        });
    });
    
    // Update save button state
    saveSubredditsBtn.disabled = !isSubredditsModified;
}

// Add a new subreddit
function addSubreddit() {
    const subreddit = newSubredditInput.value.trim().toLowerCase();
    
    if (!subreddit) {
        return;  // Ignore empty input
    }
    
    if (!currentSubreddits.includes(subreddit)) {
        currentSubreddits.push(subreddit);
        isSubredditsModified = true;
        renderRedditEditList();
        newSubredditInput.value = '';
    } else {
        // Alert that subreddit already exists
        alert(`Subreddit "r/${subreddit}" already exists.`);
    }
    
    newSubredditInput.focus();
}

// Remove a subreddit
function removeSubreddit(subreddit) {
    const index = currentSubreddits.indexOf(subreddit);
    if (index !== -1) {
        currentSubreddits.splice(index, 1);
        isSubredditsModified = true;
        renderRedditEditList();
    }
}

// Save subreddits to the API
async function saveSubreddits() {
    try {
        const response = await fetch(REDDIT_SOURCES_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ subreddits: currentSubreddits })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Reddit subreddits saved successfully!');
            isSubredditsModified = false;
            saveSubredditsBtn.disabled = true;
            
            // Refresh the subreddits display
            loadRedditSubreddits(result.reddit_subreddits);
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('reddit-modal'));
            modal.hide();
        } else {
            throw new Error(result.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error saving Reddit subreddits:', error);
        alert(`Error saving Reddit subreddits: ${error.message}`);
    }
}

async function addDiscoveredSiteAsSource(siteDataStr) {
    try {
        const siteData = JSON.parse(siteDataStr);
        
        // Open the add source modal
        const addSourceModal = new bootstrap.Modal(document.getElementById('add-source-modal'));
        addSourceModal.show();
        
        // Set source type to custom
        sourceTypeSelect.value = 'custom';
        sourceTypeSelect.dispatchEvent(new Event('change'));
        
        // Populate the form fields
        sourceIdInput.value = siteData.id || siteData.url.split('/').pop() || `discovered_${Date.now()}`;
        sourceNameInput.value = siteData.name ? siteData.name.replace('Auto-discovered: ', '') : 'Discovered Site';
        sourceUrlInput.value = siteData.url || '';
        
        // Optionally set a hidden field for source_type if the form has one, or handle in backend
        // For now, the backend can detect based on name or id prefix
        
        // The save button will now use the pre-populated data when clicked
        console.log('Discovered site form pre-populated:', siteData);
        
    } catch (error) {
        console.error('Error pre-populating discovered site form:', error);
        alert('Error loading site data: ' + error.message);
    }
}

// Add a new source
async function addNewSource() {
    const sourceType = sourceTypeSelect.value;
    
    if (!sourceType) {
        alert('Please select a source type.');
        return;
    }
    
    // Prepare the source data based on type
    let sourceData;
    
    if (sourceType === 'reddit') {
        const subreddit = subredditNameInput.value.trim();
        if (!subreddit) {
            alert('Please enter a subreddit name.');
            return;
        }
        
        sourceData = {
            id: subreddit,
            name: `Reddit - r/${subreddit}`,
            url: `https://www.reddit.com/r/${subreddit}`,
            type: 'reddit'
        };
    } else if (sourceType === 'custom') {
        const id = sourceIdInput.value.trim();
        const name = sourceNameInput.value.trim();
        const url = sourceUrlInput.value.trim();
        
        if (!id || !name || !url) {
            alert('Please fill in all fields for the custom source.');
            return;
        }
        
        sourceData = {
            id,
            name,
            url,
            type: 'custom'
        };
        
        // If this is a discovered site (check name or id), set source_type to 'crawler'
        if (name.includes('Discovered') || id.startsWith('discovered_')) {
            sourceData.source_type = 'crawler';
        }
    }
    
    try {
        const response = await fetch(ADD_SOURCE_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(sourceData)
        });
        
        const result = await response.json();
        
        if (result.success || result.message) {
            alert(result.message || 'Source added successfully!');
            
            // Reset form
            sourceTypeSelect.value = '';
            redditFields.style.display = 'none';
            customFields.style.display = 'none';
            subredditNameInput.value = '';
            sourceIdInput.value = '';
            sourceNameInput.value = '';
            sourceUrlInput.value = '';
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('add-source-modal'));
            modal.hide();
            
            // Refresh the sources list
            loadConfiguredSources();
            loadSources();
        } else {
            throw new Error(result.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error adding source:', error);
        alert(`Error adding source: ${error.message}`);
    }
}

// Override loadSourcesList to use the new source management
function loadSourcesList() {
    // Load the configured sources
    loadConfiguredSources();
}

// Edit a source
function editSource(sourceId) {
    alert(`Edit functionality for source ID ${sourceId} will be implemented soon.`);
}

// Delete a source
function deleteSource(sourceId) {
    if (confirm(`Are you sure you want to delete source ID ${sourceId}?`)) {
        alert('Delete functionality will be implemented soon.');
    }
}

// API key management functions moved to settings.js

function showLoading(container) {
    container.innerHTML = `
        <div class="d-flex justify-content-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
}

// Initialize downloads system
function initDownloadsSystem() {
    const fileCollectionForm = document.getElementById('file-collection-form');
    if (fileCollectionForm) {
        fileCollectionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const urlsTextarea = document.getElementById('download-urls');
            const keywordsInput = document.getElementById('file-keywords');
            
            if (!urlsTextarea || !keywordsInput) return;
            
            const urls = urlsTextarea.value.trim().split('\n').filter(url => url.trim());
            const keywords = keywordsInput.value.trim().split(',').map(k => k.trim()).filter(k => k);
            
            if (urls.length === 0) {
                alert('Please enter at least one URL');
                return;
            }
            
            try {
                const response = await fetch('/api/downloads/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ urls, keywords })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('File collection started successfully');
                    setTimeout(loadDownloads, 2000);
                } else {
                    alert(`Error: ${data.error}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        });
    }
    
    const refreshDownloadsBtn = document.getElementById('refresh-downloads-btn');
    if (refreshDownloadsBtn) {
        refreshDownloadsBtn.addEventListener('click', loadDownloads);
    }
    
    loadDownloads();
}

// Initialize Tor controls
function initTorControls() {
    const startTorBtn = document.getElementById('start-tor-btn');
    if (startTorBtn) {
        startTorBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/tor/start', { method: 'POST' });
                const data = await response.json();
                
                if (response.ok) {
                    alert('Tor service started');
                    updateTorStatus();
                } else {
                    alert(`Error: ${data.error}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        });
    }
    
    const stopTorBtn = document.getElementById('stop-tor-btn');
    if (stopTorBtn) {
        stopTorBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/tor/stop', { method: 'POST' });
                const data = await response.json();
                
                if (response.ok) {
                    alert('Tor service stopped');
                    updateTorStatus();
                } else {
                    alert(`Error: ${data.error}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        });
    }
    
    const darkwebCrawlBtn = document.getElementById('darkweb-crawl-btn');
    if (darkwebCrawlBtn) {
        darkwebCrawlBtn.addEventListener('click', async () => {
            const keywords = prompt('Enter keywords for dark web crawling (comma-separated):', 'privacy,security,leak');
            if (!keywords) return;
            
            try {
                const response = await fetch('/api/darkweb/crawl', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keywords: keywords.split(',').map(k => k.trim()).filter(k => k) })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('Dark web crawl started');
                } else {
                    alert(`Error: ${data.error}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        });
    }
    
    updateTorStatus();
}

// Load downloads
async function loadDownloads() {
    try {
        const response = await fetch('/api/downloads');
        const data = await response.json();
        
        if (response.ok) {
            displayDownloads(data);
            updateDownloadsSummary(data);
        } else {
            console.error('Error loading downloads:', data.error);
        }
    } catch (error) {
        console.error('Error loading downloads:', error);
    }
}

// Update Tor status
async function updateTorStatus() {
    try {
        const response = await fetch('/api/tor/status');
        const data = await response.json();
        
        if (response.ok) {
            const statusText = document.getElementById('tor-status-text');
            const portSpan = document.getElementById('tor-port');
            const controlPortSpan = document.getElementById('tor-control-port');
            
            if (statusText) {
                statusText.textContent = data.running ? 'Running' : 'Stopped';
                statusText.className = `badge ${data.running ? 'bg-success' : 'bg-secondary'}`;
            }
            
            if (portSpan) portSpan.textContent = data.port;
            if (controlPortSpan) controlPortSpan.textContent = data.control_port;
        }
    } catch (error) {
        console.error('Error updating Tor status:', error);
    }
}

// Display downloads
function displayDownloads(data) {
    const container = document.getElementById('downloads-container');
    if (!container) return;
    
    if (!data.downloads || data.downloads.length === 0) {
        container.innerHTML = '<div class="text-center text-muted"><p>No files downloaded yet.</p></div>';
        return;
    }
    
    const html = `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>File Name</th>
                        <th>Size</th>
                        <th>Type</th>
                        <th>Modified</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.downloads.map(file => `
                        <tr>
                            <td><strong>${file.name}</strong></td>
                            <td>${formatFileSize(file.size)}</td>
                            <td><span class="badge bg-secondary">${file.extension}</span></td>
                            <td>${formatDate(file.modified)}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary" onclick="viewFile('${file.path}')">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// Update downloads summary
function updateDownloadsSummary(data) {
    const totalFilesElement = document.getElementById('total-files-count');
    const totalSizeElement = document.getElementById('total-size-display');
    const fileTypesElement = document.getElementById('file-types-count');
    
    if (totalFilesElement) {
        totalFilesElement.textContent = data.total_files || 0;
    }
    
    if (totalSizeElement) {
        totalSizeElement.textContent = formatFileSize(data.total_size || 0);
    }
    
    if (fileTypesElement && data.downloads) {
        const uniqueTypes = new Set(data.downloads.map(f => f.extension));
        fileTypesElement.textContent = uniqueTypes.size;
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// View file
function viewFile(path) {
    alert('File viewing feature: ' + path);
}

// Initialize file upload system
function initFileUploadSystem() {
    // Event listeners are added in initEventListeners
}

// Handle file upload
async function handleFileUpload(e) {
    e.preventDefault();

    const formData = new FormData();
    const fileInput = document.getElementById('upload-file');
    const uploaderId = document.getElementById('uploader-id').value;
    const isPublic = document.getElementById('is-public').checked;

    if (!fileInput.files[0]) {
        alert('Please select a file');
        return;
    }

    formData.append('file', fileInput.files[0]);
    if (uploaderId) formData.append('uploader_id', uploaderId);
    formData.append('is_public', isPublic);

    try {
        const response = await fetch('/api/uploads', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        const uploadResult = document.getElementById('upload-result');
        const uploadAlert = document.getElementById('upload-alert');
        if (response.ok) {
            uploadAlert.className = 'alert alert-success';
            uploadAlert.textContent = 'File uploaded successfully!';
            uploadResult.classList.remove('d-none');
            loadFileUploads(); // Refresh list
        } else {
            uploadAlert.className = 'alert alert-danger';
            uploadAlert.textContent = result.error || 'Upload failed';
            uploadResult.classList.remove('d-none');
        }
    } catch (error) {
        alert('Upload error: ' + error.message);
    }
}

// Load file uploads
async function loadFileUploads() {
    const container = document.getElementById('uploads-container');
    if (!container) return;

    showLoading(container);

    try {
        const riskFilter = document.getElementById('uploads-risk-filter').value;
        const limit = document.getElementById('uploads-limit').value;
        let url = '/api/uploads';
        const params = new URLSearchParams();
        if (riskFilter) params.append('risk_level', riskFilter);
        if (limit) params.append('limit', limit);
        if (params.toString()) url += '?' + params;

        const response = await fetch(url);
        const data = await response.json();

        if (response.ok) {
            renderFileUploads(data.uploads || []);
        } else {
            container.innerHTML = '<div class="alert alert-danger">Error loading uploads</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
    }
}

// Render file uploads
function renderFileUploads(uploads) {
    const container = document.getElementById('uploads-container');
    if (!uploads || uploads.length === 0) {
        container.innerHTML = '<div class="text-center text-muted"><p>No files uploaded yet.</p></div>';
        return;
    }

    let html = `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Filename</th>
                        <th>Size</th>
                        <th>Risk Level</th>
                        <th>Status</th>
                        <th>Uploaded</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;

    uploads.forEach(upload => {
        const riskClass = {
            'low': 'bg-success',
            'medium': 'bg-warning',
            'high': 'bg-danger',
            'critical': 'bg-dark'
        }[upload.risk_level] || 'bg-secondary';

        const status = upload.storage_path && 'quarantine' in upload.storage_path ? 'Quarantined' : 'Stored';
        const date = new Date(upload.created_at).toLocaleString();

        html += `
            <tr>
                <td>${upload.id}</td>
                <td>${upload.filename}</td>
                <td>${formatFileSize(upload.size_bytes)}</td>
                <td><span class="badge ${riskClass}">${upload.risk_level}</span></td>
                <td>${status}</td>
                <td>${date}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewUpload(${upload.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${status !== 'Quarantined' ? `<button class="btn btn-sm btn-outline-success" onclick="downloadUpload(${upload.id})">
                        <i class="fas fa-download"></i>
                    </button>` : ''}
                </td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;
}

// View upload
function viewUpload(id) {
    window.open(`/api/uploads/${id}`, '_blank');
}

// Download upload
function downloadUpload(id) {
    window.open(`/api/uploads/${id}/download`, '_blank');
}

// Run live scan (content scraper)
async function runLiveScan() {
    try {
        const response = await fetch('/api/scraper/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Content scraper started successfully!', 'success');
            // Refresh posts after a delay
            setTimeout(() => {
                loadPosts();
            }, 3000);
        } else {
            throw new Error(data.error || 'Scraping failed');
        }
    } catch (error) {
        console.error('Error running live scan:', error);
        showToast('Error running live scan: ' + error.message, 'error');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}
