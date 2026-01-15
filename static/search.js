// Search functionality for user panel
class SearchManager {
    constructor() {
        this.searchForm = document.getElementById('search-form');
        this.searchQuery = document.getElementById('search-query');
        this.searchType = document.getElementById('search-type');
        this.searchLimit = document.getElementById('search-limit');
        this.searchResults = document.getElementById('search-results');
        this.currentResults = {};

        this.init();
    }

    init() {
        if (this.searchForm) {
            this.searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.performSearch();
            });
        }
    }

    async performSearch() {
        const query = this.searchQuery.value.trim();
        if (!query) {
            this.showToast('Please enter a search query', 'warning');
            return;
        }

        const type = this.searchType.value;
        const limit = parseInt(this.searchLimit.value) || 20;

        this.showLoading();

        try {
            const params = new URLSearchParams({
                query: query,
                limit: limit
            });

            if (type !== 'all') {
                params.append('type', type);
            }

            const response = await fetch(`/api/user/search?${params}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (!response.ok) {
                throw new Error(`Search failed: ${response.status}`);
            }

            const data = await response.json();
            this.currentResults = data.results;
            this.displayResults(data.results, data.total);

        } catch (error) {
            console.error('Search error:', error);
            this.showToast('Search failed. Please try again.', 'error');
            this.showError();
        }
    }

    displayResults(results, total) {
        if (!this.searchResults) return;

        let html = `<div class="search-summary">Found ${total} results</div>`;

        // Create tabs for different result types
        const types = ['emails', 'phones', 'cves', 'breaches', 'keywords'];
        const activeTypes = types.filter(type => results[type] && results[type].length > 0);

        if (activeTypes.length === 0) {
            html += '<div class="no-results">No results found</div>';
        } else {
            html += '<div class="search-tabs">';
            html += '<div class="tab-buttons">';
            activeTypes.forEach((type, index) => {
                const label = type.charAt(0).toUpperCase() + type.slice(1);
                const count = results[type].length;
                html += `<button class="tab-btn ${index === 0 ? 'active' : ''}" data-tab="${type}">${label} (${count})</button>`;
            });
            html += '</div>';

            html += '<div class="tab-content">';
            activeTypes.forEach((type, index) => {
                html += `<div class="tab-pane ${index === 0 ? 'active' : ''}" id="tab-${type}">`;
                html += this.renderResultsList(results[type], type);
                html += '</div>';
            });
            html += '</div></div>';
        }

        this.searchResults.innerHTML = html;

        // Add tab switching
        this.searchResults.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Add click handlers for item details
        this.searchResults.querySelectorAll('.result-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = item.dataset.id;
                const type = item.dataset.type;
                this.showItemDetails(id, type);
            });
        });
    }

    renderResultsList(items, type) {
        if (!items || items.length === 0) return '<div class="no-results">No results</div>';

        let html = '<div class="results-list">';

        items.forEach(item => {
            html += `<div class="result-item" data-id="${item.id}" data-type="${type}">`;

            switch (type) {
                case 'emails':
                    html += `<div class="result-title">${this.maskEmail(item.email)}</div>`;
                    html += `<div class="result-meta">Breach: ${item.breach} | Date: ${item.date}</div>`;
                    break;
                case 'phones':
                    html += `<div class="result-title">${this.maskPhone(item.phone)}</div>`;
                    html += `<div class="result-meta">Carrier: ${item.carrier || 'Unknown'} | Date: ${item.date}</div>`;
                    break;
                case 'cves':
                    html += `<div class="result-title">${item.cve_id}</div>`;
                    html += `<div class="result-meta">Severity: ${item.severity} | Score: ${item.cvss_score}</div>`;
                    break;
                case 'breaches':
                    html += `<div class="result-title">${item.name}</div>`;
                    html += `<div class="result-meta">Records: ${item.records_affected} | Date: ${item.breach_date}</div>`;
                    break;
                case 'keywords':
                    html += `<div class="result-title">${item.keyword}</div>`;
                    html += `<div class="result-meta">Source: ${item.source} | Date: ${item.date}</div>`;
                    break;
            }

            html += '</div>';
        });

        html += '</div>';
        return html;
    }

    switchTab(tabName) {
        // Update tab buttons
        this.searchResults.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab content
        this.searchResults.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `tab-${tabName}`);
        });
    }

    showItemDetails(id, type) {
        // This will be handled by ItemDetailsManager
        if (window.itemDetailsManager) {
            window.itemDetailsManager.showDetails(id, type);
        }
    }

    maskEmail(email) {
        if (!email) return 'N/A';
        const [local, domain] = email.split('@');
        if (local.length <= 2) return `${local}***@${domain}`;
        return `${local.substring(0, 2)}***@${domain}`;
    }

    maskPhone(phone) {
        if (!phone) return 'N/A';
        return phone.replace(/(\d{3})\d{4}(\d{3})/, '$1****$2');
    }

    showLoading() {
        this.searchResults.innerHTML = '<div class="loading">Searching...</div>';
    }

    showError() {
        this.searchResults.innerHTML = '<div class="error">Search failed. Please try again.</div>';
    }

    showToast(message, type = 'info') {
        // Assuming toast system exists
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
    window.searchManager = new SearchManager();
});
