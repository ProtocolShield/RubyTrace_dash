/**
 * Admin Dashboard Script
 * Handles sidebar functionality, search, notifications, and theme switching
 */

class AdminDashboard {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.sidebarToggle = document.querySelector('.sidebar-toggle');
        this.sidebarOverlay = document.querySelector('.sidebar-overlay');
        this.themeToggle = document.getElementById('theme-toggle');
        this.notificationsBtn = document.getElementById('notifications-btn');
        this.notificationsDropdown = document.getElementById('notifications-dropdown');
        this.logoutBtn = document.getElementById('logout-btn');
        this.topSearchInput = document.getElementById('top-search-input');
        this.topSearchBtn = document.getElementById('top-search-btn');

        this.notifications = [];
        this.isSidebarCollapsed = false;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadNotifications();
        this.updateApiStatus();
        this.setActiveNavLink();
        this.setupSearch();
    }

    setupEventListeners() {
        // Sidebar toggle
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => {
                this.sidebar?.classList.toggle('active');
                this.sidebarOverlay?.classList.toggle('active');
            });
        }

        if (this.sidebarOverlay) {
            this.sidebarOverlay.addEventListener('click', () => {
                this.sidebar?.classList.remove('active');
                this.sidebarOverlay?.classList.remove('active');
            });
        }

        // Theme toggle
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Notifications
        if (this.notificationsBtn) {
            this.notificationsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleNotifications();
            });
        }

        // Close notifications when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.notificationsBtn?.contains(e.target) && !this.notificationsDropdown?.contains(e.target)) {
                this.closeNotifications();
            }
        });

        // Logout
        if (this.logoutBtn) {
            this.logoutBtn.addEventListener('click', () => this.logout());
        }

        // Mark all notifications as read
        const markAllReadBtn = document.querySelector('.mark-all-read');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => this.markAllNotificationsRead());
        }

        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());
    }

    toggleTheme() {
        const body = document.body;
        const currentTheme = body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        this.showToast(`Switched to ${newTheme} theme`, 'success');
    }

    toggleNotifications() {
        const notifications = this.notificationsBtn?.parentElement;
        if (notifications?.classList.contains('show')) {
            this.closeNotifications();
        } else {
            this.openNotifications();
        }
    }

    openNotifications() {
        const notifications = this.notificationsBtn?.parentElement;
        notifications?.classList.add('show');
    }

    closeNotifications() {
        const notifications = this.notificationsBtn?.parentElement;
        notifications?.classList.remove('show');
    }

    async loadNotifications() {
        try {
            // This would typically fetch from an API
            // For now, we'll simulate some notifications
            this.notifications = [
                {
                    id: 1,
                    title: 'Bot Status Update',
                    message: 'Surface web bot has completed its cycle',
                    type: 'info',
                    timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5 minutes ago
                    read: false
                },
                {
                    id: 2,
                    title: 'New Data Source Added',
                    message: 'Reddit scraper has been configured',
                    type: 'success',
                    timestamp: new Date(Date.now() - 1000 * 60 * 15), // 15 minutes ago
                    read: false
                }
            ];

            this.updateNotificationUI();
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    }

    updateNotificationUI() {
        const count = this.notifications.filter(n => !n.read).length;
        const countElement = document.querySelector('.notification-count');

        if (countElement) {
            countElement.textContent = count;
            countElement.style.display = count > 0 ? 'flex' : 'none';
        }

        const listElement = document.querySelector('.notifications-list');
        if (listElement) {
            listElement.innerHTML = '';

            if (this.notifications.length === 0) {
                listElement.innerHTML = '<div class="no-notifications">No notifications</div>';
                return;
            }

            this.notifications.forEach(notification => {
                const item = document.createElement('div');
                item.className = `notification-item ${notification.read ? 'read' : 'unread'}`;
                item.innerHTML = `
                    <div class="notification-content">
                        <div class="notification-title">${notification.title}</div>
                        <div class="notification-message">${notification.message}</div>
                        <div class="notification-time">${this.formatTime(notification.timestamp)}</div>
                    </div>
                    <div class="notification-actions">
                        <button class="mark-read-btn" onclick="dashboard.markNotificationRead(${notification.id})">
                            <i class="fas fa-check"></i>
                        </button>
                    </div>
                `;
                listElement.appendChild(item);
            });
        }
    }

    markNotificationRead(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (notification) {
            notification.read = true;
            this.updateNotificationUI();
        }
    }

    markAllNotificationsRead() {
        this.notifications.forEach(n => n.read = true);
        this.updateNotificationUI();
        this.showToast('All notifications marked as read', 'success');
    }

    formatTime(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / (1000 * 60));
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    }

    async updateApiStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            const statusElement = document.getElementById('api-status');
            const statusDot = statusElement?.querySelector('.status-dot');
            const statusText = statusElement?.querySelector('.status-text');

            if (data.connected) {
                statusDot?.classList.add('online');
                statusText.textContent = 'API Online';
            } else {
                statusDot?.classList.remove('online');
                statusText.textContent = 'API Offline';
            }
        } catch (error) {
            console.error('Failed to update API status:', error);
        }
    }

    setActiveNavLink() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    setupSearch() {
        if (this.topSearchInput && this.topSearchBtn) {
            const performSearch = () => {
                const query = this.topSearchInput.value.trim();
                if (query) {
                    this.performSearch(query);
                }
            };

            this.topSearchBtn.addEventListener('click', performSearch);
            this.topSearchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
        }
    }

    async performSearch(query) {
        try {
            // This would typically search through the admin data
            // For now, we'll show a toast message
            this.showToast(`Searching for: "${query}"`, 'info');

            // Simulate search delay
            setTimeout(() => {
                this.showToast('Search completed. Check results below.', 'success');
            }, 1000);

        } catch (error) {
            console.error('Search failed:', error);
            this.showToast('Search failed. Please try again.', 'error');
        }
    }

    logout() {
        if (confirm('Are you sure you want to logout?')) {
            // Clear any stored session data
            localStorage.removeItem('admin_session');
            sessionStorage.clear();

            // Redirect to login page
            window.location.href = '/admin/login';
        }
    }

    handleResize() {
        if (window.innerWidth > 1024) {
            this.expandSidebar();
        } else {
            this.collapseSidebar();
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span>${message}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AdminDashboard();

    // Load theme from localStorage
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);
});

// Utility functions
function showToast(message, type = 'info') {
    if (window.dashboard) {
        window.dashboard.showToast(message, type);
    }
}

function toggleSidebar() {
    if (window.dashboard) {
        window.dashboard.toggleSidebar();
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminDashboard;
}
