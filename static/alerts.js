// Alerts functionality for user panel
class AlertsManager {
    constructor() {
        this.alertsList = document.getElementById('alerts-list');
        this.notificationsList = document.getElementById('notifications-list');
        this.alertsCount = document.getElementById('alerts-count');
        this.notificationCount = document.querySelector('.notification-count');
        this.refreshBtn = document.getElementById('refresh-alerts');
        this.viewAllBtn = document.querySelector('.view-all-alerts');

        this.init();
    }

    init() {
        this.loadAlerts();

        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.loadAlerts());
        }

        if (this.viewAllBtn) {
            this.viewAllBtn.addEventListener('click', () => {
                if (window.switchSection) {
                    window.switchSection('alerts');
                }
            });
        }

        // Auto-refresh every 5 minutes
        setInterval(() => this.loadAlerts(), 300000);
    }

    async loadAlerts() {
        try {
            const response = await fetch('/api/user/alerts', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    // Unauthorized - prompt for login or show message
                    this.showToast('Please login to view alerts', 'warning');
                    return;
                }
                throw new Error(`Failed to load alerts: ${response.status}`);
            }

            const data = await response.json();
            this.displayAlerts(data.alerts);
            this.updateCounts(data.alerts);

        } catch (error) {
            console.error('Error loading alerts:', error);
            this.showToast('Failed to load alerts', 'error');
        }
    }

    displayAlerts(alerts) {
        if (!this.alertsList) return;

        if (!alerts || alerts.length === 0) {
            this.alertsList.innerHTML = '<div class="no-alerts">No alerts found</div>';
            return;
        }

        let html = '';
        alerts.forEach(alert => {
            const isRead = alert.read || false;
            html += `
                <div class="alert-item ${isRead ? 'read' : 'unread'}" data-id="${alert.id}">
                    <div class="alert-header">
                        <div class="alert-title">${alert.title}</div>
                        <div class="alert-time">${this.formatTime(alert.created_at)}</div>
                    </div>
                    <div class="alert-content">${alert.message}</div>
                    <div class="alert-meta">
                        <span class="alert-type">${alert.type}</span>
                        ${alert.severity ? `<span class="alert-severity ${alert.severity}">${alert.severity}</span>` : ''}
                    </div>
                    <div class="alert-actions">
                        ${!isRead ? '<button class="btn-mark-read">Mark as Read</button>' : ''}
                        <button class="btn-view-details">View Details</button>
                    </div>
                </div>
            `;
        });

        this.alertsList.innerHTML = html;

        // Add event listeners
        this.alertsList.querySelectorAll('.btn-mark-read').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const alertId = e.target.closest('.alert-item').dataset.id;
                this.markAsRead(alertId);
            });
        });

        this.alertsList.querySelectorAll('.btn-view-details').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const alertId = e.target.closest('.alert-item').dataset.id;
                this.viewAlertDetails(alertId);
            });
        });
    }

    updateCounts(alerts) {
        const unreadCount = alerts.filter(alert => !alert.read).length;

        if (this.alertsCount) {
            this.alertsCount.textContent = unreadCount;
        }

        if (this.notificationCount) {
            this.notificationCount.textContent = unreadCount;
        }

        // Update notifications dropdown preview
        this.updateNotificationsPreview(alerts.slice(0, 5));
    }

    updateNotificationsPreview(alerts) {
        if (!this.notificationsList) return;

        if (!alerts || alerts.length === 0) {
            this.notificationsList.innerHTML = '<div class="no-notifications">No recent alerts</div>';
            return;
        }

        let html = '';
        alerts.forEach(alert => {
            html += `
                <div class="notification-item ${alert.read ? 'read' : 'unread'}">
                    <div class="notification-title">${alert.title}</div>
                    <div class="notification-message">${alert.message.substring(0, 100)}${alert.message.length > 100 ? '...' : ''}</div>
                    <div class="notification-time">${this.formatTime(alert.created_at)}</div>
                </div>
            `;
        });

        this.notificationsList.innerHTML = html;
    }

    async markAsRead(alertId) {
        try {
            const response = await fetch(`/api/user/alerts/${alertId}/read`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                this.loadAlerts(); // Refresh the list
                this.showToast('Alert marked as read', 'success');
            } else {
                throw new Error('Failed to mark as read');
            }

        } catch (error) {
            console.error('Error marking alert as read:', error);
            this.showToast('Failed to mark alert as read', 'error');
        }
    }

    viewAlertDetails(alertId) {
        // For now, just show a simple alert. Could be expanded to a modal
        this.showToast('Alert details view not implemented yet', 'info');
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return date.toLocaleDateString();
    }

    showToast(message, type = 'info') {
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            alert(message);
        }
    }

    getAuthToken() {
        return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.alertsManager = new AlertsManager();
});
