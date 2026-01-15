// New Homepage JavaScript

// Initialize homepage when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeNavigation();
    initializeAnimations();
    initializeDashboardPreview();
    initializeFeatureInteractions();
    startFloatingElements();
});

// Theme management
function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Set initial theme from localStorage or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    
    // Update theme toggle icons
    updateThemeIcons(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcons(newTheme);
}

function updateThemeIcons(theme) {
    const sunIcon = document.querySelector('.theme-toggle .fa-sun');
    const moonIcon = document.querySelector('.theme-toggle .fa-moon');
    
    if (sunIcon && moonIcon) {
        if (theme === 'dark') {
            sunIcon.style.opacity = '1';
            sunIcon.style.transform = 'translate(-50%, -50%) scale(1)';
            moonIcon.style.opacity = '0';
            moonIcon.style.transform = 'translate(-50%, -50%) scale(0)';
        } else {
            sunIcon.style.opacity = '0';
            sunIcon.style.transform = 'translate(-50%, -50%) scale(0)';
            moonIcon.style.opacity = '1';
            moonIcon.style.transform = 'translate(-50%, -50%) scale(1)';
        }
    }
}

// Navigation
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    // Smooth scrolling for anchor links
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            
            if (href && href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    
                    // Update active state
                    navLinks.forEach(l => l.classList.remove('active'));
                    link.classList.add('active');
                }
            }
        });
    });
    
    // Mobile menu toggle
    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            mobileToggle.classList.toggle('active');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
        if (navMenu && !navMenu.contains(e.target) && !mobileToggle.contains(e.target)) {
            navMenu.classList.remove('active');
            mobileToggle.classList.remove('active');
        }
    });
    
    // Update navbar on scroll
    window.addEventListener('scroll', updateNavbarOnScroll);
}

function updateNavbarOnScroll() {
    const navbar = document.querySelector('.navbar');
    const scrollY = window.scrollY;
    
    if (scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
}

// Animations
function initializeAnimations() {
    // Initialize Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements that should animate on scroll
    const animateElements = document.querySelectorAll('.feature-card, .stat, .hero-content');
    animateElements.forEach(element => {
        observer.observe(element);
    });
}

// Floating elements animation
function startFloatingElements() {
    const elements = document.querySelectorAll('.element');
    
    elements.forEach((element, index) => {
        // Add random delay for more natural movement
        const delay = Math.random() * 2000;
        
        setTimeout(() => {
            element.style.animation = `float ${6 + Math.random() * 2}s ease-in-out infinite`;
            element.style.animationDelay = `${index * 0.5}s`;
        }, delay);
    });
}

// Dashboard preview interactions
function initializeDashboardPreview() {
    const preview = document.querySelector('.dashboard-preview');
    const chartCanvas = document.querySelector('.preview-chart canvas');
    
    if (preview) {
        // Add hover effects
        preview.addEventListener('mouseenter', () => {
            preview.style.transform = 'perspective(1000px) rotateY(0deg) rotateX(0deg) scale(1.02)';
        });
        
        preview.addEventListener('mouseleave', () => {
            preview.style.transform = 'perspective(1000px) rotateY(-5deg) rotateX(5deg) scale(1)';
        });
    }
    
    // Animate preview chart
    if (chartCanvas) {
        animatePreviewChart(chartCanvas);
    }
    
    // Animate preview metrics
    animatePreviewMetrics();
}

function animatePreviewChart(canvas) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Mock data points
    const dataPoints = [30, 45, 35, 60, 55, 40, 65, 50, 75, 60];
    const maxValue = Math.max(...dataPoints);
    
    let animationProgress = 0;
    const animationDuration = 2000; // 2 seconds
    
    function drawChart() {
        ctx.clearRect(0, 0, width, height);
        
        // Draw grid lines
        ctx.strokeStyle = 'rgba(99, 102, 241, 0.1)';
        ctx.lineWidth = 1;
        
        for (let i = 0; i <= 4; i++) {
            const y = (i / 4) * height;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        
        // Draw data line
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 3;
        ctx.beginPath();
        
        const visiblePoints = Math.floor(dataPoints.length * animationProgress);
        
        dataPoints.slice(0, visiblePoints + 1).forEach((value, index) => {
            const x = (index / (dataPoints.length - 1)) * width;
            const y = height - (value / maxValue) * height;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
        
        // Draw data points
        ctx.fillStyle = '#6366f1';
        dataPoints.slice(0, visiblePoints + 1).forEach((value, index) => {
            const x = (index / (dataPoints.length - 1)) * width;
            const y = height - (value / maxValue) * height;
            
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fill();
        });
    }
    
    function animate() {
        animationProgress = Math.min(animationProgress + 0.02, 1);
        drawChart();
        
        if (animationProgress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    // Start animation after a delay
    setTimeout(() => {
        animate();
    }, 1000);
}

function animatePreviewMetrics() {
    const metrics = document.querySelectorAll('.metric-value');
    
    metrics.forEach((metric, index) => {
        const targetValue = parseInt(metric.textContent);
        let currentValue = 0;
        const increment = targetValue / 60; // 60 frames
        
        setTimeout(() => {
            const animateValue = () => {
                currentValue += increment;
                
                if (currentValue >= targetValue) {
                    currentValue = targetValue;
                } else {
                    requestAnimationFrame(animateValue);
                }
                
                metric.textContent = Math.floor(currentValue).toLocaleString();
            };
            
            animateValue();
        }, 1500 + (index * 200)); // Stagger animations
    });
}

// Feature interactions
function initializeFeatureInteractions() {
    const featureCards = document.querySelectorAll('.feature-card');
    
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            const icon = card.querySelector('.feature-icon');
            if (icon) {
                icon.style.transform = 'scale(1.1) rotate(5deg)';
            }
        });
        
        card.addEventListener('mouseleave', () => {
            const icon = card.querySelector('.feature-icon');
            if (icon) {
                icon.style.transform = 'scale(1) rotate(0deg)';
            }
        });
    });
}

// Intelligence preview filters
function initializeIntelligenceFilters() {
    const filterOptions = document.querySelectorAll('.filter-option');
    const sentimentBtns = document.querySelectorAll('.sentiment-btn');
    
    filterOptions.forEach(option => {
        option.addEventListener('click', () => {
            const checkbox = option.querySelector('input[type="checkbox"]');
            checkbox.checked = !checkbox.checked;
            
            // Trigger filter update
            updateIntelligenceFeed();
        });
    });
    
    sentimentBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Toggle active state
            sentimentBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Trigger filter update
            updateIntelligenceFeed();
        });
    });
}

function updateIntelligenceFeed() {
    const feedContainer = document.querySelector('.intelligence-feed');
    if (!feedContainer) return;
    
    // Show loading state
    feedContainer.innerHTML = `
        <div class="feed-loading">
            <div class="loading-spinner"></div>
            <p>Filtering intelligence data...</p>
        </div>
    `;
    
    // Simulate data loading
    setTimeout(() => {
        feedContainer.innerHTML = `
            <div class="feed-loading">
                <p>Intelligence feed preview available after login</p>
            </div>
        `;
    }, 1500);
}

// Stats animation
function animateStats() {
    const stats = document.querySelectorAll('.stat-number');
    
    stats.forEach(stat => {
        const targetText = stat.textContent;
        const isPercentage = targetText.includes('%');
        const targetValue = parseFloat(targetText.replace(/[,%]/g, ''));
        
        let currentValue = 0;
        const increment = targetValue / 100;
        
        const animateValue = () => {
            currentValue += increment;
            
            if (currentValue >= targetValue) {
                currentValue = targetValue;
            } else {
                requestAnimationFrame(animateValue);
            }
            
            if (isPercentage) {
                stat.textContent = currentValue.toFixed(1) + '%';
            } else {
                stat.textContent = Math.floor(currentValue).toLocaleString();
            }
        };
        
        // Use Intersection Observer to trigger animation when visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateValue();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(stat.parentElement);
    });
}

// API status indicator
function updateAPIStatus() {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    if (statusDot && statusText) {
        // Simulate API status check
        fetch('/api/status')
            .then(response => {
                if (response.ok) {
                    statusDot.style.background = '#10b981'; // green
                    statusText.textContent = 'API Online';
                } else {
                    statusDot.style.background = '#ef4444'; // red
                    statusText.textContent = 'API Issues';
                }
            })
            .catch(() => {
                statusDot.style.background = '#f59e0b'; // yellow
                statusText.textContent = 'Checking...';
            });
    }
}

// Smooth scroll for internal links
function smoothScrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K for search (future feature)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        // Future: Open search modal
    }
    
    // Ctrl/Cmd + / for theme toggle
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        toggleTheme();
    }
});

// Initialize additional features when page loads
window.addEventListener('load', () => {
    animateStats();
    updateAPIStatus();
    initializeIntelligenceFilters();
    
    // Periodically update API status
    setInterval(updateAPIStatus, 30000); // Every 30 seconds
});

// Particle system for hero background (optional enhancement)
function createParticleSystem() {
    const canvas = document.createElement('canvas');
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '1';
    
    const hero = document.querySelector('.hero');
    if (hero) {
        hero.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        canvas.width = hero.offsetWidth;
        canvas.height = hero.offsetHeight;
        
        const particles = [];
        const particleCount = 50;
        
        // Create particles
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1,
                opacity: Math.random() * 0.5 + 0.1
            });
        }
        
        function animateParticles() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            particles.forEach(particle => {
                // Update position
                particle.x += particle.vx;
                particle.y += particle.vy;
                
                // Wrap around edges
                if (particle.x < 0) particle.x = canvas.width;
                if (particle.x > canvas.width) particle.x = 0;
                if (particle.y < 0) particle.y = canvas.height;
                if (particle.y > canvas.height) particle.y = 0;
                
                // Draw particle
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.size, 0, 2 * Math.PI);
                ctx.fillStyle = `rgba(99, 102, 241, ${particle.opacity})`;
                ctx.fill();
            });
            
            requestAnimationFrame(animateParticles);
        }
        
        animateParticles();
    }
}

// Error handling for missing elements
function safeQuerySelector(selector, callback) {
    const element = document.querySelector(selector);
    if (element && callback) {
        callback(element);
    }
    return element;
}

// Export functions for global access
window.homepage = {
    toggleTheme,
    smoothScrollToSection,
    updateAPIStatus,
    createParticleSystem
};