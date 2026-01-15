// Dashboard JavaScript

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    initializeNavigation();
    initializeTheme();
    initializeNotifications();
    loadDashboardData();
});

// Dashboard initialization
function initializeDashboard() {
    // Initialize sidebar
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }
    
    if (mobileSidebarToggle) {
        mobileSidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }
    
    // Initialize logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Initialize quick actions
    const actionBtns = document.querySelectorAll('.action-btn');
    actionBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.currentTarget.dataset.action;
            handleQuickAction(action);
        });
    });
}

// Navigation handling
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.content-section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            const sectionId = link.dataset.section;
            
            // Update active nav link
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Show corresponding section
            sections.forEach(section => {
                section.classList.remove('active');
            });
            
            const targetSection = document.getElementById(`${sectionId}-section`);
            if (targetSection) {
                targetSection.classList.add('active');
                
                // Update page title
                const pageTitle = document.getElementById('page-title');
                if (pageTitle) {
                    pageTitle.textContent = link.querySelector('span').textContent;
                }
                
                // Load section-specific data
                loadSectionData(sectionId);
            }
        });
    });
}

// Theme handling
function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Set initial theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Notifications
function initializeNotifications() {
    const notificationsBtn = document.getElementById('notifications-btn');
    const notificationsDropdown = document.getElementById('notifications-dropdown');
    
    if (notificationsBtn && notificationsDropdown) {
        notificationsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notificationsDropdown.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            notificationsDropdown.classList.remove('show');
        });
    }
    
    // Load notifications
    loadNotifications();
}

// Data loading functions
async function loadDashboardData() {
    try {
        // Load overview stats
        await loadOverviewStats();
        
        // Load recent intelligence
        await loadRecentIntelligence();
        
        // Load source activity
        await loadSourceActivity();
        
        // Initialize charts
        initializeCharts();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showToast('Error', 'Failed to load dashboard data', 'error');
    }
}

async function loadOverviewStats() {
    try {
        const response = await fetch('/api/stats/overview');
        const data = await response.json();
        
        if (response.ok) {
            updateStatCards(data);
        }
    } catch (error) {
        console.error('Error loading overview stats:', error);
    }
}

function updateStatCards(data) {
    // Update stat values with animation
    const stats = [
        { id: 'threats-detected', value: data.threats_detected || 2847 },
        { id: 'data-points', value: data.data_points || 15234 },
        { id: 'security-score', value: data.security_score || '98.7%' },
        { id: 'uptime', value: data.uptime || '99.9%' }
    ];
    
    stats.forEach(stat => {
        const element = document.getElementById(stat.id);
        if (element) {
            animateNumber(element, stat.value);
        }
    });
}

function animateNumber(element, targetValue) {
    const isPercentage = typeof targetValue === 'string' && targetValue.includes('%');
    const numericValue = isPercentage ? parseFloat(targetValue) : targetValue;
    
    let currentValue = 0;
    const increment = numericValue / 50; // 50 steps
    
    const animation = setInterval(() => {
        currentValue += increment;
        
        if (currentValue >= numericValue) {
            currentValue = numericValue;
            clearInterval(animation);
        }
        
        if (isPercentage) {
            element.textContent = currentValue.toFixed(1) + '%';
        } else {
            element.textContent = Math.floor(currentValue).toLocaleString();
        }
    }, 20);
}

async function loadRecentIntelligence() {
    try {
        const response = await fetch('/api/intelligence/recent?limit=5');
        const data = await response.json();
        
        if (response.ok) {
            displayRecentIntelligence(data.intelligence || []);
        }
    } catch (error) {
        console.error('Error loading recent intelligence:', error);
        displayRecentIntelligence(getMockIntelligence());
    }
}

function displayRecentIntelligence(intelligence) {
    const container = document.getElementById('recent-intelligence');
    if (!container) return;
    
    container.innerHTML = intelligence.map(item => `
        <div class="intelligence-item">
            <div class="intel-header">
                <div class="intel-source">${item.source || 'Unknown'}</div>
                <div class="intel-time">${formatTime(item.created_at)}</div>
            </div>
            <div class="intel-title">${item.title || 'No title'}</div>
            <div class="intel-summary">${item.summary || 'No summary available'}</div>
            <div class="intel-footer">
                <span class="intel-sentiment ${item.sentiment || 'neutral'}">${item.sentiment || 'Neutral'}</span>
                <span class="intel-score">${item.score || 0}/10</span>
            </div>
        </div>
    `).join('');
}

async function loadSourceActivity() {
    try {
        const response = await fetch('/api/sources/activity');
        const data = await response.json();
        
        if (response.ok) {
            displaySourceActivity(data.sources || []);
        }
    } catch (error) {
        console.error('Error loading source activity:', error);
        displaySourceActivity(getMockSources());
    }
}

function displaySourceActivity(sources) {
    const container = document.getElementById('source-activity');
    if (!container) return;
    
    container.innerHTML = sources.map(source => `
        <div class="source-item">
            <div class="source-info">
                <div class="source-name">${source.name}</div>
                <div class="source-status ${source.status}">${source.status}</div>
            </div>
            <div class="source-stats">
                <div class="stat">
                    <span class="stat-value">${source.posts_today || 0}</span>
                    <span class="stat-label">Today</span>
                </div>
                <div class="stat">
                    <span class="stat-value">${source.total_posts || 0}</span>
                    <span class="stat-label">Total</span>
                </div>
            </div>
        </div>
    `).join('');
}

async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications');
        const data = await response.json();
        
        if (response.ok) {
            displayNotifications(data.notifications || []);
            updateNotificationCount(data.unread_count || 0);
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
        displayNotifications(getMockNotifications());
    }
}

function displayNotifications(notifications) {
    const container = document.getElementById('notifications-list');
    if (!container) return;
    
    container.innerHTML = notifications.map(notification => `
        <div class="notification-item ${notification.read ? '' : 'unread'}">
            <div class="notification-icon">
                <i class="fas ${getNotificationIcon(notification.type)}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-title">${notification.title}</div>
                <div class="notification-message">${notification.message}</div>
                <div class="notification-time">${formatTime(notification.created_at)}</div>
            </div>
        </div>
    `).join('');
}

function updateNotificationCount(count) {
    const countElement = document.querySelector('.notification-count');
    const alertsCount = document.getElementById('alerts-count');
    
    if (countElement) {
        countElement.textContent = count;
        countElement.style.display = count > 0 ? 'block' : 'none';
    }
    
    if (alertsCount) {
        alertsCount.textContent = count;
    }
}

// Section-specific data loading
async function loadSectionData(sectionId) {
    switch (sectionId) {
        case 'intelligence':
            await loadIntelligenceFeed();
            break;
        case 'search':
            initializeSearch();
            break;
        case 'alerts':
            await loadAlerts();
            break;
        case 'sources':
            await loadSources();
            break;
        case 'analytics':
            await loadAnalytics();
            break;
        case 'settings':
            await loadSettings();
            break;
    }
}

async function loadIntelligenceFeed() {
    const container = document.getElementById('intelligence-feed');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading intelligence feed...</div>';
    
    try {
        const response = await fetch('/api/intelligence/feed');
        const data = await response.json();
        
        if (response.ok) {
            displayIntelligenceFeed(data.intelligence || []);
        } else {
            container.innerHTML = '<div class="error">Failed to load intelligence feed</div>';
        }
    } catch (error) {
        console.error('Error loading intelligence feed:', error);
        container.innerHTML = '<div class="error">Network error loading intelligence feed</div>';
    }
}

function displayIntelligenceFeed(intelligence) {
    const container = document.getElementById('intelligence-feed');
    if (!container) return;
    
    if (intelligence.length === 0) {
        container.innerHTML = '<div class="empty-state">No intelligence data available</div>';
        return;
    }
    
    container.innerHTML = intelligence.map(item => `
        <div class="intelligence-card">
            <div class="card-header">
                <div class="source-info">
                    <span class="source-name">${item.source || 'Unknown'}</span>
                    <span class="post-time">${formatTime(item.created_at)}</span>
                </div>
                <div class="sentiment-badge ${item.sentiment || 'neutral'}">
                    ${item.sentiment || 'Neutral'}
                </div>
            </div>
            <div class="card-content">
                <h3 class="post-title">${item.title || 'No title'}</h3>
                <p class="post-summary">${item.summary || 'No summary available'}</p>
                <div class="post-meta">
                    <span class="score">Score: ${item.score || 0}/10</span>
                    <span class="keywords">${(item.keywords || []).join(', ')}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// Chart initialization
function initializeCharts() {
    const chartCanvas = document.getElementById('threat-chart');
    if (!chartCanvas) return;
    
    // Mock chart data for demonstration
    const ctx = chartCanvas.getContext('2d');
    
    // Simple line chart drawing
    drawThreatChart(ctx);
}

function drawThreatChart(ctx) {
    const width = ctx.canvas.width;
    const height = ctx.canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Mock data points
    const data = [20, 35, 45, 30, 60, 55, 40, 65, 50, 70];
    const maxValue = Math.max(...data);
    
    // Draw line
    ctx.beginPath();
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2;
    
    data.forEach((value, index) => {
        const x = (index / (data.length - 1)) * width;
        const y = height - (value / maxValue) * height;
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
}

// Event handlers
async function handleLogout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
        } else {
            showToast('Error', 'Logout failed', 'error');
        }
    } catch (error) {
        console.error('Logout error:', error);
        showToast('Error', 'Network error during logout', 'error');
    }
}

function handleQuickAction(action) {
    switch (action) {
        case 'new-search':
            // Switch to search section
            document.querySelector('[data-section="search"]').click();
            break;
        case 'create-alert':
            // Switch to alerts section
            document.querySelector('[data-section="alerts"]').click();
            break;
        case 'export-data':
            exportData();
            break;
        case 'view-logs':
            viewLogs();
            break;
    }
}

// Utility functions
function formatTime(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
}

function getNotificationIcon(type) {
    const icons = {
        'alert': 'fa-exclamation-triangle',
        'info': 'fa-info-circle',
        'success': 'fa-check-circle',
        'warning': 'fa-exclamation-circle'
    };
    return icons[type] || 'fa-bell';
}

// Mock data functions (for demonstration)
function getMockIntelligence() {
    return [
        {
            source: 'HackerNews',
            title: 'Privacy concerns with new tracking technology',
            summary: 'Discussion about privacy implications of new tracking methods',
            sentiment: 'negative',
            score: 7,
            created_at: new Date(Date.now() - 3600000).toISOString()
        },
        {
            source: 'Reddit',
            title: 'Security vulnerability discovered',
            summary: 'New security flaw found in popular software',
            sentiment: 'negative',
            score: 9,
            created_at: new Date(Date.now() - 7200000).toISOString()
        }
    ];
}

function getMockSources() {
    return [
        { name: 'HackerNews', status: 'active', posts_today: 45, total_posts: 1234 },
        { name: 'Reddit', status: 'active', posts_today: 78, total_posts: 2567 },
        { name: 'PrivacyGuides', status: 'inactive', posts_today: 0, total_posts: 456 }
    ];
}

function getMockNotifications() {
    return [];
}

// Toast notification system
function showToast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas ${iconMap[type]}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="closeToast(this)">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            closeToast(toast.querySelector('.toast-close'));
        }
    }, 5000);
}

function closeToast(closeBtn) {
    const toast = closeBtn.parentElement;
    toast.style.animation = 'slideOutRight 0.3s ease forwards';
    
    setTimeout(() => {
        if (toast.parentElement) {
            toast.parentElement.removeChild(toast);
        }
    }, 300);
}