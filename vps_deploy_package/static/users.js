// User Management JavaScript

let usersData = [];

// Initialize users view when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners when users view is activated
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-view="users"]')) {
            loadUsersData();
        }
    });
    
    // Refresh button
    const refreshUsersBtn = document.getElementById('refresh-users-btn');
    if (refreshUsersBtn) {
        refreshUsersBtn.addEventListener('click', loadUsersData);
    }
    
    // User status filter
    const userStatusFilter = document.getElementById('user-status-filter');
    if (userStatusFilter) {
        userStatusFilter.addEventListener('change', filterUsers);
    }
    
    // User search
    const userSearch = document.getElementById('user-search');
    if (userSearch) {
        userSearch.addEventListener('input', filterUsers);
    }
});

// Load users data from API
async function loadUsersData() {
    try {
        const response = await fetch('/api/user-management/users');
        if (response.ok) {
            usersData = await response.json();
            displayUsers();
        } else {
            throw new Error('Failed to load users');
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Failed to load users data');
    }
}

// Display users in the interface
function displayUsers() {
    const pendingUsers = usersData.filter(user => !user.is_active);
    const allUsers = usersData;
    
    // Update counters
    document.getElementById('pending-count').textContent = pendingUsers.length;
    document.getElementById('total-users-count').textContent = allUsers.length;
    
    // Display pending users
    displayPendingUsers(pendingUsers);
    
    // Display all users
    displayAllUsers(allUsers);
}

// Display pending users for approval
function displayPendingUsers(pendingUsers) {
    const container = document.getElementById('pending-users-container');
    
    if (pendingUsers.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-check-circle fa-2x mb-2"></i>
                <p>No pending user approvals</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = pendingUsers.map(user => `
        <div class="card mb-3">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h6 class="mb-1">${escapeHtml(user.full_name)}</h6>
                        <p class="mb-1">
                            <strong>Username:</strong> ${escapeHtml(user.username)}<br>
                            <strong>Email:</strong> ${escapeHtml(user.email)}<br>
                            <strong>Registered:</strong> ${formatDate(user.created_at)}
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <button class="btn btn-success btn-sm me-2" onclick="approveUser(${user.id})">
                            <i class="fas fa-check me-1"></i> Approve
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="declineUser(${user.id})">
                            <i class="fas fa-times me-1"></i> Decline
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// Display all users
function displayAllUsers(users) {
    const container = document.getElementById('all-users-container');
    
    if (users.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-users fa-2x mb-2"></i>
                <p>No users found</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Status</th>
                        <th>Registered</th>
                        <th>Last Login</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${users.map(user => `
                        <tr>
                            <td>${escapeHtml(user.full_name)}</td>
                            <td>${escapeHtml(user.username)}</td>
                            <td>${escapeHtml(user.email)}</td>
                            <td>
                                ${getUserStatusBadge(user)}
                            </td>
                            <td>${formatDate(user.created_at)}</td>
                            <td>${user.last_login ? formatDate(user.last_login) : 'Never'}</td>
                            <td>
                                ${getUserActions(user)}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// Get user status badge HTML
function getUserStatusBadge(user) {
    if (user.is_admin) {
        return '<span class="badge bg-danger">Admin</span>';
    } else if (user.is_active) {
        return '<span class="badge bg-success">Active</span>';
    } else {
        return '<span class="badge bg-warning text-dark">Pending</span>';
    }
}

// Get user actions HTML
function getUserActions(user) {
    let actions = '';
    
    if (!user.is_active && !user.is_admin) {
        actions += `
            <button class="btn btn-success btn-sm me-1" onclick="approveUser(${user.id})" title="Approve User">
                <i class="fas fa-check"></i>
            </button>
            <button class="btn btn-danger btn-sm me-1" onclick="declineUser(${user.id})" title="Decline User">
                <i class="fas fa-times"></i>
            </button>
        `;
    } else if (user.is_active && !user.is_admin) {
        actions += `
            <button class="btn btn-warning btn-sm me-1" onclick="deactivateUser(${user.id})" title="Deactivate User">
                <i class="fas fa-pause"></i>
            </button>
            <button class="btn btn-info btn-sm me-1" onclick="makeAdmin(${user.id})" title="Make Admin">
                <i class="fas fa-crown"></i>
            </button>
        `;
    }
    
    return actions;
}

// Approve a user
async function approveUser(userId) {
    if (!confirm('Are you sure you want to approve this user?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/user-management/users/${userId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showSuccess('User approved successfully');
            loadUsersData(); // Refresh the data
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to approve user');
        }
    } catch (error) {
        console.error('Error approving user:', error);
        showError(`Failed to approve user: ${error.message}`);
    }
}

// Decline a user
async function declineUser(userId) {
    if (!confirm('Are you sure you want to decline this user? This will delete their account.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/user-management/users/${userId}/decline`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showSuccess('User declined and removed successfully');
            loadUsersData(); // Refresh the data
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to decline user');
        }
    } catch (error) {
        console.error('Error declining user:', error);
        showError(`Failed to decline user: ${error.message}`);
    }
}

// Deactivate a user
async function deactivateUser(userId) {
    if (!confirm('Are you sure you want to deactivate this user?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/user-management/users/${userId}/deactivate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showSuccess('User deactivated successfully');
            loadUsersData(); // Refresh the data
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to deactivate user');
        }
    } catch (error) {
        console.error('Error deactivating user:', error);
        showError(`Failed to deactivate user: ${error.message}`);
    }
}

// Make user an admin
async function makeAdmin(userId) {
    if (!confirm('Are you sure you want to make this user an admin? This will give them full administrative privileges.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/user-management/users/${userId}/make-admin`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showSuccess('User promoted to admin successfully');
            loadUsersData(); // Refresh the data
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to make user admin');
        }
    } catch (error) {
        console.error('Error making user admin:', error);
        showError(`Failed to make user admin: ${error.message}`);
    }
}

// Filter users based on status and search
function filterUsers() {
    const statusFilter = document.getElementById('user-status-filter').value;
    const searchTerm = document.getElementById('user-search').value.toLowerCase();
    
    let filteredUsers = usersData;
    
    // Apply status filter
    if (statusFilter) {
        filteredUsers = filteredUsers.filter(user => {
            switch (statusFilter) {
                case 'active':
                    return user.is_active && !user.is_admin;
                case 'inactive':
                    return !user.is_active;
                case 'admin':
                    return user.is_admin;
                default:
                    return true;
            }
        });
    }
    
    // Apply search filter
    if (searchTerm) {
        filteredUsers = filteredUsers.filter(user => 
            user.username.toLowerCase().includes(searchTerm) ||
            user.email.toLowerCase().includes(searchTerm) ||
            user.full_name.toLowerCase().includes(searchTerm)
        );
    }
    
    displayAllUsers(filteredUsers);
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function showSuccess(message) {
    // Create a temporary success alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}

function showError(message) {
    // Create a temporary error alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        <i class="fas fa-exclamation-circle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}