/**
 * Advanced OSINT Homepage JavaScript
 * Real-time API integration and interactive features
 */

(function() {
    'use strict';
    
    // Configuration
    const CONFIG = {
        API_BASE: window.location.origin + '/api',
        REFRESH_INTERVAL: 60000, // 1 minute
        SEARCH_DEBOUNCE: 500,
        MAX_POSTS_DISPLAY: 20,
        MAX_SOURCES_DISPLAY: 12
    };
    
    // DOM Elements
    const DOM = {
        themeToggle: document.getElementById('theme-toggle'),
        headerApiStatus: document.getElementById('header-api-status'),
        footerApiStatus: document.getElementById('footer-api-status'),
        backToTop: document.getElementById('back-to-top'),
        navLinks: document.querySelectorAll('.nav-link'),
        
        // Statistics
        totalPosts: document.getElementById('total-posts'),
        activeSources: document.getElementById('active-sources'),
        highRisk: document.getElementById('high-risk'),
        recentIncidents: document.getElementById('recent-incidents'),
        
        // Feed
        postsFeed: document.getElementById('posts-feed'),
        refreshFeed: document.getElementById('refresh-feed'),
        sourceFilter: document.getElementById('source-filter'),
        
        // Search
        searchForm: document.getElementById('search-form'),
        searchInput: document.getElementById('search-input'),
        searchResults: document.getElementById('search-results'),
        searchStats: document.getElementById('search-stats'),
        searchSourceFilter: document.getElementById('search-source-filter'),
        searchRiskFilter: document.getElementById('search-risk-filter'),
        searchTimeFilter: document.getElementById('search-time-filter'),
        
        // Sources
        sourcesGrid: document.getElementById('sources-grid'),
        sourcesSummary: document.getElementById('sources-summary'),
        
        // Map
        threatMap: document.getElementById('threat-map'),
        refreshMap: document.getElementById('refresh-map'),
        mapSourcesCount: document.getElementById('map-sources-count'),
        
        // Footer
        footerSources: document.getElementById('footer-sources'),
        footerPosts: document.getElementById('footer-posts'),
        lastUpdated: document.getElementById('last-updated'),
        
        // Notifications
        notificationContainer: document.getElementById('notification-container')
    };
    
    // State Management
    const STATE = {
        currentTheme: 'auto',
        apiConnected: false,
        lastUpdate: null,
        searchTimeout: null,
        refreshInterval: null,
        postsData: [],
        sourcesData: [],
        statsData: {}
    };
    
    // Initialize Application
    function init() {
        setupTheme();
        setupNavigation();
        setupApiMonitoring();
        setupEventListeners();
        setupBackToTop();
        loadInitialData();
        setupAutoRefresh();
        
        console.log('OSINT Homepage initialized successfully');
    }
    
    // Theme Management
    function setupTheme() {
        const savedTheme = localStorage.getItem('osint_theme') || 'auto';
        STATE.currentTheme = savedTheme;
        
        applyTheme(savedTheme);
        
        DOM.themeToggle.addEventListener('click', toggleTheme);
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            if (STATE.currentTheme === 'auto') {
                document.body.setAttribute('data-theme', 'auto');
            }
        });
    }
    
    function applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('osint_theme', theme);
        STATE.currentTheme = theme;
    }
    
    function toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        
        showNotification(`Theme changed to ${newTheme} mode`, 'info');
    }
    
    // Navigation
    function setupNavigation() {
        DOM.navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    // Update active nav link
                    DOM.navLinks.forEach(l => l.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Smooth scroll to target
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
    
    // API Monitoring
    function setupApiMonitoring() {
        checkApiStatus();
        setInterval(checkApiStatus, 30000); // Check every 30 seconds
    }
    
    function checkApiStatus() {
        fetch(`${CONFIG.API_BASE}/stats`)
            .then(response => response.json())
            .then(data => {
                updateApiStatus(true);
                updateStats(data);
            })
            .catch(error => {
                updateApiStatus(false);
                console.error('API Status Check Failed:', error);
            });
    }
    
    function updateApiStatus(connected) {
        const statusElements = [DOM.headerApiStatus, DOM.footerApiStatus];
        const statusClass = connected ? 'connected' : 'disconnected';
        const statusText = connected ? 'API Connected' : 'API Disconnected';
        
        statusElements.forEach(element => {
            if (element) {
                element.className = `api-connection-status ${statusClass}`;
                const textElement = element.querySelector('.status-text');
                if (textElement) {
                    textElement.textContent = statusText;
                }
            }
        });
        
        STATE.apiConnected = connected;
        
        if (connected && !STATE.lastUpdate) {
            loadInitialData();
        }
    }
    
    // Statistics Updates
    function updateStats(data) {
        if (!data) return;
        
        STATE.statsData = data;
        
        // Update main statistics
        if (DOM.totalPosts) DOM.totalPosts.textContent = formatNumber(data.total_posts || 0);
        if (DOM.activeSources) DOM.activeSources.textContent = formatNumber(data.active_sources || 0);
        if (DOM.highRisk) DOM.highRisk.textContent = formatNumber(data.high_risk || 0);
        if (DOM.recentIncidents) DOM.recentIncidents.textContent = formatNumber(data.recent_incidents || 0);
        
        // Update footer statistics
        if (DOM.footerSources) DOM.footerSources.textContent = formatNumber(data.active_sources || 0);
        if (DOM.footerPosts) DOM.footerPosts.textContent = formatNumber(data.total_posts || 0);
        if (DOM.mapSourcesCount) DOM.mapSourcesCount.textContent = formatNumber(data.active_sources || 0);
        
        // Update last updated time
        const now = new Date();
        if (DOM.lastUpdated) DOM.lastUpdated.textContent = now.toLocaleTimeString();
        STATE.lastUpdate = now;
        
        // Update change indicators (if available)
        updateChangeIndicators(data);
    }
    
    function updateChangeIndicators(data) {
        const indicators = [
            { element: 'posts-change', value: data.posts_change },
            { element: 'sources-change', value: data.sources_change },
            { element: 'risk-change', value: data.risk_change },
            { element: 'incidents-change', value: data.incidents_change }
        ];
        
        indicators.forEach(indicator => {
            const element = document.getElementById(indicator.element);
            if (element && indicator.value !== undefined) {
                const value = indicator.value;
                element.textContent = value > 0 ? `+${value}` : value.toString();
                element.className = `stat-change ${value > 0 ? 'positive' : value < 0 ? 'negative' : ''}`;
            }
        });
    }
    
    // Load Initial Data
    function loadInitialData() {
        if (!STATE.apiConnected) return;
        
        Promise.all([
            loadPosts(),
            loadSources(),
            loadStats()
        ]).then(() => {
            console.log('Initial data loaded successfully');
        }).catch(error => {
            console.error('Error loading initial data:', error);
            showNotification('Failed to load some data. Please refresh the page.', 'error');
        });
    }
    
    // Posts Feed
    function loadPosts(sourceFilter = '') {
        let url = `${CONFIG.API_BASE}/posts?limit=${CONFIG.MAX_POSTS_DISPLAY}`;
        if (sourceFilter) url += `&source=${sourceFilter}`;
        
        return fetch(url)
            .then(response => response.json())
            .then(data => {
                STATE.postsData = data.posts || [];
                displayPosts(STATE.postsData);
            })
            .catch(error => {
                console.error('Error loading posts:', error);
                displayPostsError();
            });
    }
    
    function displayPosts(posts) {
        if (!DOM.postsFeed) return;
        
        if (!posts || posts.length === 0) {
            DOM.postsFeed.innerHTML = `
                <div class="no-posts">
                    <div class="placeholder-icon">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    <h3>No intelligence posts available</h3>
                    <p>Check back later for new privacy intelligence updates.</p>
                </div>
            `;
            return;
        }
        
        const postsHtml = posts.map(post => `
            <div class="post-item">
                <div class="post-header">
                    <h3 class="post-title">${escapeHtml(post.title || 'Untitled Post')}</h3>
                    ${post.risk_level ? `<div class="risk-indicator ${post.risk_level.toLowerCase()}">${post.risk_level.toUpperCase()}</div>` : ''}
                </div>
                <div class="post-meta">
                    <span class="post-source">${escapeHtml(post.source || 'Unknown Source')}</span>
                    <span class="post-timestamp">${formatTimestamp(post.timestamp)}</span>
                    ${post.sentiment ? `<span class="post-sentiment">${escapeHtml(post.sentiment)}</span>` : ''}
                </div>
                <div class="post-excerpt">
                    ${escapeHtml(truncateText(post.content || '', 200))}
                </div>
                ${post.keywords && post.keywords.length > 0 ? `
                    <div class="post-tags">
                        ${post.keywords.slice(0, 5).map(tag => `<span class="post-tag">${escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        DOM.postsFeed.innerHTML = postsHtml;
    }
    
    function displayPostsError() {
        if (!DOM.postsFeed) return;
        
        DOM.postsFeed.innerHTML = `
            <div class="error-message">
                <div class="placeholder-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3>Unable to load intelligence posts</h3>
                <p>Please check your connection and try again.</p>
                <button class="btn btn-primary" onclick="loadPosts()">Retry</button>
            </div>
        `;
    }
    
    // Sources Monitor
    function loadSources() {
        return fetch(`${CONFIG.API_BASE}/sources`)
            .then(response => response.json())
            .then(data => {
                STATE.sourcesData = data.sources || [];
                displaySources(STATE.sourcesData);
                updateSourcesSummary(data);
            })
            .catch(error => {
                console.error('Error loading sources:', error);
                displaySourcesError();
            });
    }
    
    function displaySources(sources) {
        if (!DOM.sourcesGrid) return;
        
        if (!sources || sources.length === 0) {
            DOM.sourcesGrid.innerHTML = `
                <div class="no-sources">
                    <div class="placeholder-icon">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    <h3>No sources configured</h3>
                    <p>Configure data sources in the admin panel to start monitoring.</p>
                </div>
            `;
            return;
        }
        
        const sourcesHtml = sources.slice(0, CONFIG.MAX_SOURCES_DISPLAY).map(source => `
            <div class="source-item">
                <div class="source-header">
                    <h3 class="source-name">${escapeHtml(source.name || 'Unknown Source')}</h3>
                    <div class="source-status ${source.status || 'unknown'}">${(source.status || 'unknown').toUpperCase()}</div>
                </div>
                <div class="source-stats">
                    <div class="source-stat">
                        <span class="stat-label">Posts:</span>
                        <span class="stat-value">${formatNumber(source.posts_count || 0)}</span>
                    </div>
                    <div class="source-stat">
                        <span class="stat-label">Risk Level:</span>
                        <span class="stat-value risk-${(source.risk_level || 'unknown').toLowerCase()}">${(source.risk_level || 'Unknown').toUpperCase()}</span>
                    </div>
                    <div class="source-stat">
                        <span class="stat-label">Last Updated:</span>
                        <span class="stat-value">${source.last_updated ? formatTimestamp(source.last_updated) : 'Never'}</span>
                    </div>
                </div>
                ${source.description ? `<div class="source-description">${escapeHtml(source.description)}</div>` : ''}
            </div>
        `).join('');
        
        DOM.sourcesGrid.innerHTML = sourcesHtml;
    }
    
    function displaySourcesError() {
        if (!DOM.sourcesGrid) return;
        
        DOM.sourcesGrid.innerHTML = `
            <div class="error-message">
                <div class="placeholder-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3>Unable to load sources</h3>
                <p>Please check your connection and try again.</p>
                <button class="btn btn-primary" onclick="loadSources()">Retry</button>
            </div>
        `;
    }
    
    function updateSourcesSummary(data) {
        if (!DOM.sourcesSummary) return;
        
        const total = data.total || 0;
        const active = data.active || 0;
        DOM.sourcesSummary.textContent = `${active} active of ${total} total sources`;
    }
    
    // Search Functionality
    function setupSearch() {
        if (!DOM.searchForm) return;
        
        DOM.searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch();
        });
        
        DOM.searchInput.addEventListener('input', function() {
            clearTimeout(STATE.searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 3) {
                STATE.searchTimeout = setTimeout(() => {
                    performSearch();
                }, CONFIG.SEARCH_DEBOUNCE);
            } else if (query.length === 0) {
                clearSearchResults();
            }
        });
        
        // Filter change handlers
        [DOM.searchSourceFilter, DOM.searchRiskFilter, DOM.searchTimeFilter].forEach(filter => {
            if (filter) {
                filter.addEventListener('change', function() {
                    if (DOM.searchInput.value.trim()) {
                        performSearch();
                    }
                });
            }
        });
    }
    
    function performSearch() {
        const query = DOM.searchInput.value.trim();
        if (!query) {
            showNotification('Please enter search terms', 'warning');
            return;
        }
        
        showSearchLoading();
        
        const params = new URLSearchParams({
            q: query,
            limit: '50'
        });
        
        // Add filters
        if (DOM.searchSourceFilter?.value) params.append('source', DOM.searchSourceFilter.value);
        if (DOM.searchRiskFilter?.value) params.append('risk_level', DOM.searchRiskFilter.value);
        if (DOM.searchTimeFilter?.value) params.append('time_range', DOM.searchTimeFilter.value);
        
        fetch(`${CONFIG.API_BASE}/search?${params}`)
            .then(response => response.json())
            .then(data => {
                displaySearchResults(data.results || [], query);
                updateSearchStats(data.results?.length || 0);
            })
            .catch(error => {
                console.error('Search error:', error);
                displaySearchError();
            })
            .finally(() => {
                hideSearchLoading();
            });
    }
    
    function displaySearchResults(results, query) {
        if (!DOM.searchResults) return;
        
        if (!results || results.length === 0) {
            DOM.searchResults.innerHTML = `
                <div class="no-results">
                    <div class="placeholder-icon">
                        <i class="fas fa-search"></i>
                    </div>
                    <h3>No results found</h3>
                    <p>No results found for "${escapeHtml(query)}". Try different keywords or adjust your filters.</p>
                </div>
            `;
            return;
        }
        
        const resultsHtml = results.map(result => `
            <div class="post-item">
                <div class="post-header">
                    <h3 class="post-title">${escapeHtml(result.title || 'Untitled')}</h3>
                    ${result.risk_level ? `<div class="risk-indicator ${result.risk_level.toLowerCase()}">${result.risk_level.toUpperCase()}</div>` : ''}
                </div>
                <div class="post-meta">
                    <span class="post-source">${escapeHtml(result.source || 'Unknown')}</span>
                    <span class="post-timestamp">${formatTimestamp(result.timestamp)}</span>
                    ${result.sentiment ? `<span class="post-sentiment">${escapeHtml(result.sentiment)}</span>` : ''}
                </div>
                <div class="post-excerpt">
                    ${escapeHtml(truncateText(result.content || result.summary || '', 200))}
                </div>
                ${result.keywords && result.keywords.length > 0 ? `
                    <div class="post-tags">
                        ${result.keywords.slice(0, 5).map(tag => `<span class="post-tag">${escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        DOM.searchResults.innerHTML = resultsHtml;
    }
    
    function displaySearchError() {
        if (!DOM.searchResults) return;
        
        DOM.searchResults.innerHTML = `
            <div class="error-message">
                <div class="placeholder-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3>Search failed</h3>
                <p>Unable to search the database. Please check your connection and try again.</p>
                <button class="btn btn-primary" onclick="performSearch()">Retry</button>
            </div>
        `;
    }
    
    function clearSearchResults() {
        if (!DOM.searchResults) return;
        
        DOM.searchResults.innerHTML = `
            <div class="search-placeholder">
                <div class="placeholder-icon">
                    <i class="fas fa-search"></i>
                </div>
                <h3>Search Intelligence Database</h3>
                <p>Enter keywords to search through privacy incidents, data breaches, and security threats from multiple sources.</p>
            </div>
        `;
        
        if (DOM.searchStats) DOM.searchStats.textContent = '';
    }
    
    function updateSearchStats(count) {
        if (!DOM.searchStats) return;
        DOM.searchStats.textContent = `${count} results found`;
    }
    
    function showSearchLoading() {
        const searchButton = DOM.searchForm?.querySelector('.search-button');
        if (searchButton) {
            const buttonText = searchButton.querySelector('.button-text');
            const loadingSpinner = searchButton.querySelector('.loading-spinner');
            
            if (buttonText && loadingSpinner) {
                buttonText.style.display = 'none';
                loadingSpinner.style.display = 'inline-block';
                searchButton.disabled = true;
            }
        }
        
        if (DOM.searchResults) {
            DOM.searchResults.innerHTML = `
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <span>Searching intelligence database...</span>
                </div>
            `;
        }
    }
    
    function hideSearchLoading() {
        const searchButton = DOM.searchForm?.querySelector('.search-button');
        if (searchButton) {
            const buttonText = searchButton.querySelector('.button-text');
            const loadingSpinner = searchButton.querySelector('.loading-spinner');
            
            if (buttonText && loadingSpinner) {
                buttonText.style.display = 'inline';
                loadingSpinner.style.display = 'none';
                searchButton.disabled = false;
            }
        }
    }
    
    // Event Listeners
    function setupEventListeners() {
        // Refresh buttons
        if (DOM.refreshFeed) {
            DOM.refreshFeed.addEventListener('click', function() {
                this.disabled = true;
                const originalText = this.textContent;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
                
                loadPosts(DOM.sourceFilter?.value || '').finally(() => {
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
                });
            });
        }
        
        if (DOM.refreshMap) {
            DOM.refreshMap.addEventListener('click', function() {
                this.disabled = true;
                const originalText = this.textContent;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
                
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh Data';
                    showNotification('Map data refreshed', 'success');
                }, 1000);
            });
        }
        
        // Source filter
        if (DOM.sourceFilter) {
            DOM.sourceFilter.addEventListener('change', function() {
                loadPosts(this.value);
            });
        }
        
        // Search setup
        setupSearch();
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                DOM.searchInput?.focus();
            }
            
            // Escape to clear search
            if (e.key === 'Escape' && DOM.searchInput === document.activeElement) {
                DOM.searchInput.value = '';
                clearSearchResults();
            }
        });
    }
    
    // Back to Top
    function setupBackToTop() {
        if (!DOM.backToTop) return;
        
        window.addEventListener('scroll', function() {
            if (window.scrollY > 300) {
                DOM.backToTop.classList.add('visible');
            } else {
                DOM.backToTop.classList.remove('visible');
            }
        });
        
        DOM.backToTop.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Auto Refresh
    function setupAutoRefresh() {
        STATE.refreshInterval = setInterval(() => {
            if (STATE.apiConnected) {
                loadStats();
                
                // Refresh posts if no search is active
                if (!DOM.searchInput?.value.trim()) {
                    loadPosts(DOM.sourceFilter?.value || '');
                }
            }
        }, CONFIG.REFRESH_INTERVAL);
    }
    
    function loadStats() {
        return fetch(`${CONFIG.API_BASE}/stats`)
            .then(response => response.json())
            .then(data => {
                updateStats(data);
            })
            .catch(error => {
                console.error('Error loading stats:', error);
            });
    }
    
    // Utility Functions
    function formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    function formatTimestamp(timestamp) {
        if (!timestamp) return 'Unknown';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) {
            return 'Just now';
        } else if (diff < 3600000) {
            return Math.floor(diff / 60000) + 'm ago';
        } else if (diff < 86400000) {
            return Math.floor(diff / 3600000) + 'h ago';
        } else if (diff < 604800000) {
            return Math.floor(diff / 86400000) + 'd ago';
        } else {
            return date.toLocaleDateString();
        }
    }
    
    function truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function showNotification(message, type = 'info') {
        if (!DOM.notificationContainer) return;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${getNotificationIcon(type)}"></i>
                <span>${escapeHtml(message)}</span>
            </div>
            <button class="notification-close" aria-label="Close notification">&times;</button>
        `;
        
        DOM.notificationContainer.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', function() {
            notification.classList.add('fade-out');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
    }
    
    function getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }
    
    // Expose functions to global scope for inline event handlers
    window.loadPosts = loadPosts;
    window.loadSources = loadSources;
    window.performSearch = performSearch;
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        if (STATE.refreshInterval) {
            clearInterval(STATE.refreshInterval);
        }
        if (STATE.searchTimeout) {
            clearTimeout(STATE.searchTimeout);
        }
    });
    
})();