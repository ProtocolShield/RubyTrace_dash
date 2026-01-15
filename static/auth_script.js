// Authentication JavaScript

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
    initializePasswordToggles();
    initializePasswordStrength();
    initializeFormValidation();
    initializeSocialAuth();
});

// Initialize authentication functionality
function initializeAuth() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
}

// Handle login form submission
async function handleLogin(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = document.getElementById('login-btn');
    const formData = new FormData(form);
    
    const loginData = {
        username: formData.get('username'),
        password: formData.get('password'),
        remember: formData.get('remember') === 'on'
    };
    
    // Validate input
    if (!validateLoginForm(loginData)) {
        return;
    }
    
    // Set loading state
    setButtonLoading(submitBtn, true);
    clearFormErrors();
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(loginData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Success', 'Login successful! Redirecting...', 'success');
            
            // Store token if provided
            if (result.token) {
                localStorage.setItem('auth_token', result.token);
            }
            
            // Redirect to dashboard or intended page
            setTimeout(() => {
                window.location.href = result.redirect_url || '/dashboard';
            }, 1500);
            
        } else {
            showToast('Login Failed', result.error || 'Invalid credentials', 'error');
            
            if (result.errors) {
                displayFormErrors(result.errors);
            }
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showToast('Error', 'Network error. Please try again.', 'error');
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

// Handle register form submission
async function handleRegister(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = document.getElementById('register-btn');
    const formData = new FormData(form);
    
    const registerData = {
        full_name: formData.get('full_name'),
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password'),
        confirm_password: formData.get('confirm_password'),
        terms: formData.get('terms') === 'on',
        newsletter: formData.get('newsletter') === 'on'
    };
    
    // Validate input
    if (!validateRegisterForm(registerData)) {
        return;
    }
    
    // Set loading state
    setButtonLoading(submitBtn, true);
    clearFormErrors();
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(registerData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Registration Successful', 
                'Account created! Please wait for admin approval.', 'success');
            
            // Redirect to login page
            setTimeout(() => {
                window.location.href = '/login?registered=true';
            }, 2000);
            
        } else {
            showToast('Registration Failed', result.error || 'Registration failed', 'error');
            
            if (result.errors) {
                displayFormErrors(result.errors);
            }
        }
        
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Error', 'Network error. Please try again.', 'error');
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

// Form validation
function validateLoginForm(data) {
    let isValid = true;
    
    if (!data.username || data.username.trim().length < 3) {
        showFieldError('username', 'Username must be at least 3 characters');
        isValid = false;
    }
    
    if (!data.password || data.password.length < 6) {
        showFieldError('password', 'Password must be at least 6 characters');
        isValid = false;
    }
    
    return isValid;
}

function validateRegisterForm(data) {
    let isValid = true;
    
    if (!data.full_name || data.full_name.trim().length < 2) {
        showFieldError('full_name', 'Full name must be at least 2 characters');
        isValid = false;
    }
    
    if (!data.username || data.username.trim().length < 3) {
        showFieldError('username', 'Username must be at least 3 characters');
        isValid = false;
    }
    
    if (!/^[a-zA-Z0-9_]+$/.test(data.username)) {
        showFieldError('username', 'Username can only contain letters, numbers, and underscores');
        isValid = false;
    }
    
    if (!validateEmail(data.email)) {
        showFieldError('email', 'Please enter a valid email address');
        isValid = false;
    }
    
    if (!validatePassword(data.password)) {
        showFieldError('password', 'Password must be at least 8 characters with mixed case and numbers');
        isValid = false;
    }
    
    if (data.password !== data.confirm_password) {
        showFieldError('confirm_password', 'Passwords do not match');
        isValid = false;
    }
    
    if (!data.terms) {
        showFieldError('terms', 'You must agree to the terms of service');
        isValid = false;
    }
    
    return isValid;
}

// Password toggle functionality
function initializePasswordToggles() {
    const toggles = document.querySelectorAll('.password-toggle');
    
    toggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input[type="password"], input[type="text"]');
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
}

// Password strength indicator
function initializePasswordStrength() {
    const passwordInput = document.getElementById('password');
    const strengthIndicator = document.getElementById('password-strength');
    
    if (passwordInput && strengthIndicator) {
        const strengthBar = strengthIndicator.querySelector('.strength-fill');
        const strengthText = strengthIndicator.querySelector('.strength-text');
        
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = calculatePasswordStrength(password);
            
            strengthBar.className = `strength-fill ${strength.level}`;
            strengthText.textContent = `Password strength: ${strength.text}`;
        });
    }
}

function calculatePasswordStrength(password) {
    let score = 0;
    
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    
    if (score < 2) return { level: 'weak', text: 'Weak' };
    if (score < 4) return { level: 'fair', text: 'Fair' };
    if (score < 6) return { level: 'good', text: 'Good' };
    return { level: 'strong', text: 'Strong' };
}

// Form validation utilities
function initializeFormValidation() {
    const inputs = document.querySelectorAll('input[required]');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            clearFieldError(this.name);
        });
    });
}

function validateField(input) {
    const value = input.value.trim();
    const name = input.name;
    
    switch (name) {
        case 'email':
            if (!validateEmail(value)) {
                showFieldError(name, 'Please enter a valid email address');
                return false;
            }
            break;
        case 'username':
            if (value.length < 3) {
                showFieldError(name, 'Username must be at least 3 characters');
                return false;
            }
            if (!/^[a-zA-Z0-9_]+$/.test(value)) {
                showFieldError(name, 'Username can only contain letters, numbers, and underscores');
                return false;
            }
            break;
        case 'password':
            if (!validatePassword(value)) {
                showFieldError(name, 'Password must be at least 8 characters with mixed case and numbers');
                return false;
            }
            break;
    }
    
    clearFieldError(name);
    return true;
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 8 && 
           /[a-z]/.test(password) && 
           /[A-Z]/.test(password) && 
           /[0-9]/.test(password);
}

// Social authentication
function initializeSocialAuth() {
    const githubBtn = document.getElementById('github-login') || document.getElementById('github-register');
    const googleBtn = document.getElementById('google-login') || document.getElementById('google-register');
    
    if (githubBtn) {
        githubBtn.addEventListener('click', () => handleSocialAuth('github'));
    }
    
    if (googleBtn) {
        googleBtn.addEventListener('click', () => handleSocialAuth('google'));
    }
}

function handleSocialAuth(provider) {
    showToast('Redirecting', `Redirecting to ${provider} authentication...`, 'warning');
    
    // In a real implementation, this would redirect to OAuth provider
    setTimeout(() => {
        window.location.href = `/api/auth/${provider}`;
    }, 1000);
}

// UI Utilities
function setButtonLoading(button, loading) {
    if (loading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

function showFieldError(fieldName, message) {
    const errorElement = document.getElementById(`${fieldName}-error`);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }
    
    const input = document.querySelector(`input[name="${fieldName}"]`);
    if (input) {
        input.style.borderColor = 'var(--warning)';
    }
}

function clearFieldError(fieldName) {
    const errorElement = document.getElementById(`${fieldName}-error`);
    if (errorElement) {
        errorElement.classList.remove('show');
    }
    
    const input = document.querySelector(`input[name="${fieldName}"]`);
    if (input) {
        input.style.borderColor = 'var(--border-color)';
    }
}

function clearFormErrors() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(element => {
        element.classList.remove('show');
    });
    
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.style.borderColor = 'var(--border-color)';
    });
}

function displayFormErrors(errors) {
    Object.keys(errors).forEach(field => {
        showFieldError(field, errors[field]);
    });
}

// Toast notification system
function showToast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    
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

// Check for URL parameters and show appropriate messages
function checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.get('registered') === 'true') {
        showToast('Registration Complete', 
            'Your account has been created. Please wait for admin approval.', 'success');
    }
    
    if (urlParams.get('approved') === 'true') {
        showToast('Account Approved', 
            'Your account has been approved! You can now log in.', 'success');
    }
    
    if (urlParams.get('error')) {
        showToast('Authentication Error', urlParams.get('error'), 'error');
    }
}

// Initialize URL parameter checking
document.addEventListener('DOMContentLoaded', checkUrlParams);

// Form auto-save (for better UX)
function initializeAutoSave() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input:not([type="password"])');
        
        inputs.forEach(input => {
            // Load saved value
            const savedValue = localStorage.getItem(`form_${form.id}_${input.name}`);
            if (savedValue && input.type !== 'checkbox') {
                input.value = savedValue;
            }
            
            // Save on input
            input.addEventListener('input', function() {
                if (this.type !== 'checkbox') {
                    localStorage.setItem(`form_${form.id}_${this.name}`, this.value);
                }
            });
        });
    });
}

// Clear saved form data on successful submission
function clearSavedFormData(formId) {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
        if (key.startsWith(`form_${formId}_`)) {
            localStorage.removeItem(key);
        }
    });
}

// Initialize auto-save
document.addEventListener('DOMContentLoaded', initializeAutoSave);

// Real-time username availability check (for register form)
function initializeUsernameCheck() {
    const usernameInput = document.getElementById('username');
    
    if (usernameInput && window.location.pathname === '/register') {
        let checkTimeout;
        
        usernameInput.addEventListener('input', function() {
            const username = this.value.trim();
            
            clearTimeout(checkTimeout);
            
            if (username.length >= 3) {
                checkTimeout = setTimeout(() => {
                    checkUsernameAvailability(username);
                }, 500);
            }
        });
    }
}

async function checkUsernameAvailability(username) {
    try {
        const response = await fetch('/api/auth/check-username', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username })
        });
        
        const result = await response.json();
        
        if (!result.available) {
            showFieldError('username', 'Username is already taken');
        } else {
            clearFieldError('username');
        }
        
    } catch (error) {
        console.error('Username check error:', error);
    }
}

// Initialize username check
document.addEventListener('DOMContentLoaded', initializeUsernameCheck);