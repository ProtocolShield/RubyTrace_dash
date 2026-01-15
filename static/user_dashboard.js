/**
 * User Dashboard Script
 * Handles user dashboard functionality, search, alerts, watchlists, graph, and export
 */

class UserDashboard {
    constructor() {
        this.currentSection = 'overview';
        this.searchResults = [];
        this.alerts = [];
        this.watchlists = [];
        this.graphData = null;
        this.breachLeakData = [];
        this.currentCves = [];
        this.filteredCves = [];
        this.cases = [];
        this.currentTab = 'alerts'; // for alerts-watchlists section

        this.init();
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    init() {
        this.setupEventListeners();
        this.loadOverviewStats();
        this.loadFullStats();
        // Do not auto-load alerts/watchlists here to avoid triggering failing endpoints on page load
        this.setActiveNavLink();
        this.setupSearch();
        this.setupExport();
    }

    setupEventListeners() {
        // Sidebar navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('data-section');
                this.switchSection(section);
            });
        });

        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Logout
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }

        // Refresh buttons
        document.getElementById('refresh-alerts')?.addEventListener('click', () => this.loadAlerts());
        document.getElementById('refresh-watchlists')?.addEventListener('click', () => this.loadWatchlists());
        document.getElementById('refresh-graph')?.addEventListener('click', () => this.loadGraph());
        document.getElementById('refresh-breach-leak')?.addEventListener('click', () => this.loadBreachLeakData());
        document.getElementById('refresh-cve-btn')?.addEventListener('click', () => this.loadUserCVEs());
        document.getElementById('refresh-cases')?.addEventListener('click', () => this.loadCases());
        document.getElementById('refresh-alerts-watchlists')?.addEventListener('click', () => {
            this.loadAlerts();
            this.loadWatchlists();
        });

        // CVE buttons
        document.getElementById('cve-filter-btn')?.addEventListener('click', () => this.applyUserCveFilters());

        // CVE search input
        const cveSearch = document.getElementById('cve-search');
        if (cveSearch) {
            cveSearch.addEventListener('input', this.debounce(() => this.applyUserCveFilters(), 300));
        }

        // Modal controls
        document.getElementById('item-details-close')?.addEventListener('click', () => this.closeItemDetailsModal());
        document.getElementById('create-watchlist-close')?.addEventListener('click', () => this.closeCreateWatchlistModal());
        document.getElementById('create-alert-close')?.addEventListener('click', () => this.closeCreateAlertModal());
        document.getElementById('cancel-watchlist')?.addEventListener('click', () => this.closeCreateWatchlistModal());
        document.getElementById('cancel-alert')?.addEventListener('click', () => this.closeCreateAlertModal());

        // Create buttons
        document.getElementById('create-watchlist-btn')?.addEventListener('click', () => this.openCreateWatchlistModal());
        document.getElementById('create-alert-btn')?.addEventListener('click', () => this.openCreateAlertModal());
        document.getElementById('create-case-btn')?.addEventListener('click', () => this.openCreateCaseModal());

        // Form submissions
        document.getElementById('create-watchlist-form')?.addEventListener('submit', (e) => this.handleCreateWatchlist(e));

        // Export type change
        document.getElementById('export-type')?.addEventListener('change', (e) => {
            const queryGroup = document.getElementById('query-group');
            if (e.target.value === 'search_results') {
                queryGroup.style.display = 'block';
            } else {
                queryGroup.style.display = 'none';
            }
        });

        // Quick actions
        document.querySelectorAll('.action-btn[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.closest('.action-btn').getAttribute('data-action');
                if (action === 'search') {
                    this.switchSection('search');
                } else if (action === 'create-watchlist') {
                    this.openCreateWatchlistModal();
                } else if (action === 'view-alerts') {
                    this.switchSection('alerts-watchlists');
                    this.switchTab('alerts');
                }
            });
        });

        // Top bar export quick button
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) exportBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchSection('export');
        });
    }

    switchSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-section') === sectionName) {
                link.classList.add('active');
            }
        });

        this.currentSection = sectionName;

        // Load section-specific data
        switch (sectionName) {
            case 'graph':
                this.loadGraph();
                break;
            case 'alerts-watchlists':
                this.loadAlerts();
                this.loadWatchlists();
                break;
            case 'breach-leak':
                this.loadBreachLeakData();
                break;
            case 'cves':
                this.loadUserCVEs();
                break;
            case 'cases':
                this.loadCases();
                break;
        }
    }

    switchTab(tabName) {
        this.currentTab = tabName;

        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Show selected tab content
        const targetContent = document.getElementById(`${tabName}-tab`);
        if (targetContent) {
            targetContent.classList.add('active');
        }

        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-tab') === tabName) {
                btn.classList.add('active');
            }
        });

        // Load tab-specific data if needed
        switch (tabName) {
            case 'alerts':
                this.loadAlerts();
                break;
            case 'watchlists':
                this.loadWatchlists();
                break;
        }
    }

    async loadOverviewStats() {
        try {
            const response = await fetch('/stats/simple');
            const data = await response.json();

            if (data.success) {
                const stats = data.stats;

                document.getElementById('total-items').textContent =
                    stats.totalItemsCollected;

                document.getElementById('new-items-24h').textContent =
                    stats.newItemsFromLast24Hours;

                document.getElementById('high-risk-items').textContent =
                    stats.highRiskItems;
            } else {
                document.getElementById('total-items').textContent = 'Error';
                document.getElementById('new-items-24h').textContent = 'Error';
                document.getElementById('high-risk-items').textContent = 'Error';
            }
        } catch (error) {
            console.error("Failed to load simple stats:", error);
            document.getElementById('total-items').textContent = 'Error';
            document.getElementById('new-items-24h').textContent = 'Error';
            document.getElementById('high-risk-items').textContent = 'Error';
        }
    }

    async loadFullStats() {
        try {
            const response = await fetch('/api/user/stats');
            const data = await response.json();

            if (data.success) {
                this.renderOverviewCharts(data.charts);
            } else {
                console.error('Failed to load full stats:', data.error);
            }
        } catch (error) {
            console.error('Failed to load full stats:', error);
        }
    }
    

    renderOverviewCharts(charts) {
        // Timeline Chart
        this.renderTimelineChart(charts.timeline);

        // Top Domains Chart
        this.renderTopDomainsChart(charts.top_domains);

        // Top Keywords Chart
        this.renderTopKeywordsChart(charts.top_keywords);
    }

    renderTimelineChart(timelineData) {
        const container = document.getElementById('timeline-chart');
        if (!container || !timelineData) return;

        // Clear previous chart
        container.innerHTML = '';

        const ctx = document.createElement('canvas');
        ctx.width = container.clientWidth;
        ctx.height = 200;
        container.appendChild(ctx);

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: timelineData.map(d => new Date(d.date).toLocaleDateString()),
                datasets: [{
                    label: 'Activity',
                    data: timelineData.map(d => d.count),
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#fff'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#fff'
                        }
                    }
                }
            }
        });
    }

    renderTopDomainsChart(domainsData) {
        const container = document.getElementById('domains-chart');
        if (!container || !domainsData) return;

        container.innerHTML = '';

        const ctx = document.createElement('canvas');
        ctx.width = container.clientWidth;
        ctx.height = 200;
        container.appendChild(ctx);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: domainsData.map(d => d.name),
                datasets: [{
                    label: 'Count',
                    data: domainsData.map(d => d.count),
                    backgroundColor: '#e74c3c',
                    borderColor: '#c0392b',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#fff'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#fff',
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    renderTopKeywordsChart(keywordsData) {
        const container = document.getElementById('keywords-chart');
        if (!container || !keywordsData) return;

        container.innerHTML = '';

        const ctx = document.createElement('canvas');
        ctx.width = container.clientWidth;
        ctx.height = 200;
        container.appendChild(ctx);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: keywordsData.map(d => d.keyword),
                datasets: [{
                    label: 'Count',
                    data: keywordsData.map(d => d.count),
                    backgroundColor: '#f39c12',
                    borderColor: '#e67e22',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#fff'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#fff',
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    async loadAlerts() {
        try {
            const response = await fetch('/api/user/alerts');
            const data = await response.json();

            if (data.success) {
                this.alerts = data.alerts;
                this.updateAlertsUI();
                this.updateAlertsPreview();
            }
        } catch (error) {
            console.error('Failed to load alerts:', error);
        }
    }

    updateAlertsUI() {
        const container = document.getElementById('alerts-list');
        if (!container) return;

        if (this.alerts.length === 0) {
            container.innerHTML = '<div class="no-data">No alerts found</div>';
            return;
        }

        container.innerHTML = this.alerts.map(alert => `
            <div class="alert-item">
                <div class="alert-header">
                    <span class="alert-type ${alert.alert_type}">${alert.alert_type.replace('_', ' ')}</span>
                    <span class="alert-time">${this.formatDate(alert.created_at)}</span>
                </div>
                <div class="alert-content">
                    <h4>${alert.title}</h4>
                    <p>Risk Score: ${alert.risk_score}</p>
                    <p>Source: ${alert.source_type}</p>
                </div>
            </div>
        `).join('');

        // Update badge count
        const badge = document.getElementById('alerts-count');
        if (badge) {
            badge.textContent = this.alerts.length;
            badge.style.display = this.alerts.length > 0 ? 'inline' : 'none';
        }
    }

    updateAlertsPreview() {
        const container = document.getElementById('alerts-preview');
        if (!container) return;

        const recentAlerts = this.alerts.slice(0, 5);
        if (recentAlerts.length === 0) {
            container.innerHTML = '<div class="no-data">No recent alerts</div>';
            return;
        }

        container.innerHTML = recentAlerts.map(alert => `
            <div class="preview-item">
                <div class="preview-title">${alert.title}</div>
                <div class="preview-meta">Risk: ${alert.risk_score} • ${this.formatDate(alert.created_at)}</div>
            </div>
        `).join('');
    }

    async loadWatchlists() {
        try {
            const response = await fetch('/api/user/watchlists');
            const data = await response.json();

            if (data.success) {
                this.watchlists = data.watchlists;
                this.updateWatchlistsUI();
                this.updateWatchlistPreview();
            }
        } catch (error) {
            console.error('Failed to load watchlists:', error);
        }
    }

    updateWatchlistsUI() {
        const container = document.getElementById('watchlists-list');
        if (!container) return;

        if (this.watchlists.length === 0) {
            container.innerHTML = '<div class="no-data">No watchlist items found</div>';
            return;
        }

        container.innerHTML = this.watchlists.map(item => `
            <div class="watchlist-item">
                <div class="watchlist-content">
                    <h4>${item.query}</h4>
                    <p>Type: ${item.search_type}</p>
                    <p>Last searched: ${this.formatDate(item.last_searched)}</p>
                </div>
                <div class="watchlist-actions">
                    <button class="btn btn-sm" onclick="dashboard.searchAgain('${item.query}', '${item.search_type}')">
                        Search Again
                    </button>
                </div>
            </div>
        `).join('');
    }

    updateWatchlistPreview() {
        const container = document.getElementById('watchlist-preview');
        if (!container) return;

        const recentItems = this.watchlists.slice(0, 5);
        if (recentItems.length === 0) {
            container.innerHTML = '<div class="no-data">No watchlist items</div>';
            return;
        }

        container.innerHTML = recentItems.map(item => `
            <div class="preview-item">
                <div class="preview-title">${item.query}</div>
                <div class="preview-meta">${item.search_type} • ${this.formatDate(item.last_searched)}</div>
            </div>
        `).join('');
    }

    async loadGraph() {
        try {
            const response = await fetch('/api/user/graph');
            const data = await response.json();

            if (data.success) {
                this.graphData = data.graph;
                this.renderGraph();
            }
        } catch (error) {
            console.error('Failed to load graph:', error);
        }
    }

    renderGraph() {
        const container = document.getElementById('graph-canvas');
        if (!container || !this.graphData) return;

        // Clear previous graph
        container.innerHTML = '';

        // Simple D3.js graph rendering
        const svg = d3.select('#graph-canvas')
            .append('svg')
            .attr('width', container.clientWidth)
            .attr('height', 400);

        // Create nodes
        const nodes = this.graphData.nodes.map(node => ({
            ...node,
            x: Math.random() * (container.clientWidth - 100) + 50,
            y: Math.random() * 300 + 50
        }));

        // Create links
        const links = this.graphData.edges;

        // Draw links
        svg.selectAll('line')
            .data(links)
            .enter()
            .append('line')
            .attr('stroke', '#666')
            .attr('stroke-width', 1);

        // Draw nodes
        const nodeGroups = svg.selectAll('g')
            .data(nodes)
            .enter()
            .append('g')
            .attr('transform', d => `translate(${d.x}, ${d.y})`);

        nodeGroups.append('circle')
            .attr('r', 20)
            .attr('fill', d => this.getNodeColor(d.type));

        nodeGroups.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', 30)
            .attr('font-size', '10px')
            .text(d => d.label.substring(0, 15) + (d.label.length > 15 ? '...' : ''));

        // Simple force simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(container.clientWidth / 2, 200));

        simulation.on('tick', () => {
            svg.selectAll('line')
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            nodeGroups.attr('transform', d => `translate(${d.x}, ${d.y})`);
        });
    }

    getNodeColor(type) {
        const colors = {
            raw_data: '#3498db',
            cve: '#e74c3c',
            breach: '#f39c12'
        };
        return colors[type] || '#95a5a6';
    }

    setupSearch() {
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        }

        // Top search
        const topSearchForm = document.getElementById('top-bar-search');
        if (topSearchForm) {
            topSearchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.switchSection('search');
                const query = document.getElementById('top-search-input').value;
                if (query) {
                    document.getElementById('search-query').value = query;
                    this.handleSearch(new Event('submit'));
                }
            });
        }
    }

    async handleSearch(e) {
        e.preventDefault();

        const query = document.getElementById('search-query').value.trim();
        const type = document.getElementById('search-type').value;
        const limit = document.getElementById('search-limit').value;

        if (!query) {
            this.showToast('Please enter a search query', 'error');
            return;
        }

        try {
            const response = await fetch('/api/user/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    type: type,
                    limit: parseInt(limit)
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displaySearchResults(data.results);
            } else {
                this.showToast(data.error || 'Search failed', 'error');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showToast('Search failed', 'error');
        }
    }

    displaySearchResults(results) {
        const container = document.getElementById('search-results');
        if (!container) return;

        if (results.length === 0) {
            container.innerHTML = '<div class="no-data">No results found</div>';
            return;
        }

        // Create table structure
        const tableHTML = `
            <table class="search-results-table">
                <thead>
                    <tr>
                        <th onclick="dashboard.sortResults('title')">Title <i class="fas fa-sort"></i></th>
                        <th onclick="dashboard.sortResults('type')">Type <i class="fas fa-sort"></i></th>
                        <th>Description</th>
                        <th onclick="dashboard.sortResults('risk_score')">Risk Score <i class="fas fa-sort"></i></th>
                        <th onclick="dashboard.sortResults('created_at')">Date <i class="fas fa-sort"></i></th>
                    </tr>
                </thead>
                <tbody>
                    ${results.map(result => `
                        <tr onclick="dashboard.openItemDetailsModal(${JSON.stringify(result).replace(/"/g, '"')})">
                            <td>${result.title || 'No Title'}</td>
                            <td><span class="result-type">${result.type || 'Unknown'}</span></td>
                            <td>${(result.description || result.content || 'No description available').substring(0, 100)}${(result.description || result.content || '').length > 100 ? '...' : ''}</td>
                            <td>${result.risk_score || 'N/A'}</td>
                            <td>${result.created_at ? this.formatDate(result.created_at) : 'Unknown'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.innerHTML = tableHTML;
    }

    sortResults(column) {
        if (!this.searchResults || this.searchResults.length === 0) return;

        // Simple sort implementation
        this.searchResults.sort((a, b) => {
            let aVal = a[column] || '';
            let bVal = b[column] || '';

            if (column === 'created_at') {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            } else if (column === 'risk_score') {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            }

            if (aVal < bVal) return -1;
            if (aVal > bVal) return 1;
            return 0;
        });

        this.displaySearchResults(this.searchResults);
    }

    setupExport() {
        const exportForm = document.getElementById('export-form');
        if (exportForm) exportForm.addEventListener('submit', (e) => this.handleExport(e));

        const exportTypeSelect = document.getElementById('export-type');
        const queryGroup = document.getElementById('query-group');
        if (exportTypeSelect) {
            exportTypeSelect.addEventListener('change', (e) => {
                if (e.target.value === 'search_results') queryGroup.style.display = 'block';
                else queryGroup.style.display = 'none';
            });
        }
    }

    async handleExport(e) {
        e.preventDefault();

        const exportType = document.getElementById('export-type').value;
        const format = document.getElementById('export-format').value;
        const query = document.getElementById('export-query').value;
        const dateRange = document.getElementById('export-date-range').value;
        const maskSensitive = document.getElementById('mask-sensitive').checked;

        const limit = 1000; // max items to request in one go from APIs

        try {
            let items = [];

            switch (exportType) {
                case 'cves': {
                    const res = await fetch(`/api/cve?limit=${limit}`);
                    if (!res.ok) throw new Error('Failed to fetch CVEs');
                    items = await res.json();
                    break;
                }
                case 'threat_news': {
                    let res = await fetch(`/api/posts?type=threat&limit=${limit}`);
                    if (!res.ok) res = await fetch(`/api/posts?limit=${limit}`);
                    if (!res.ok) throw new Error('Failed to fetch Threat News');
                    items = await res.json();
                    break;
                }
                case 'bot_data': {
                    const res = await fetch(`/api/data/raw?page=1&per_page=${limit}`);
                    if (!res.ok) throw new Error('Failed to fetch Bot Data');
                    const payload = await res.json();
                    items = payload.data || payload.results || payload.items || payload || [];
                    if (!Array.isArray(items)) items = [];
                    break;
                }
                case 'search_results': {
                    if (!query) {
                        this.showToast('Please enter a search query to export search results', 'error');
                        return;
                    }
                    const params = new URLSearchParams({ q: query, limit });
                    const res = await fetch(`/api/search?${params.toString()}`);
                    if (!res.ok) throw new Error('Failed to fetch search results');
                    const data = await res.json();
                    items = data.results || data || [];
                    break;
                }
                default:
                    this.showToast('Please select a valid export type', 'error');
                    return;
            }

            // Apply date range filter
            if (dateRange && dateRange !== 'all') {
                const now = Date.now();
                let cutoff = 0;
                if (dateRange === '24h') cutoff = now - 24 * 60 * 60 * 1000;
                else if (dateRange === '7d') cutoff = now - 7 * 24 * 60 * 60 * 1000;
                else if (dateRange === '30d') cutoff = now - 30 * 24 * 60 * 60 * 1000;
                else if (dateRange === '90d') cutoff = now - 90 * 24 * 60 * 60 * 1000;

                items = items.filter(it => {
                    const dateFields = ['published_at', 'created_at', 'timestamp', 'created', 'date'];
                    for (const f of dateFields) {
                        if (it && it[f]) {
                            const t = new Date(it[f]).getTime();
                            if (!isNaN(t) && t >= cutoff) return true;
                        }
                    }
                    return false;
                });
            }

            // Simple masking for common sensitive fields
            function maskItem(obj) {
                if (!obj || typeof obj !== 'object') return obj;
                const out = Object.assign({}, obj);
                const fieldsToMask = ['email', 'emails', 'password', 'passwords', 'ip', 'ips', 'hash', 'hashes'];
                fieldsToMask.forEach(k => {
                    if (out[k]) {
                        if (Array.isArray(out[k])) out[k] = out[k].map(() => 'REDACTED');
                        else out[k] = 'REDACTED';
                    }
                });
                // Also attempt to redact common nested properties
                if (out.metadata && typeof out.metadata === 'object') {
                    const meta = Object.assign({}, out.metadata);
                    ['emails', 'ips', 'passwords', 'hashes'].forEach(k => { if (meta[k]) meta[k] = Array.isArray(meta[k]) ? meta[k].map(()=>'REDACTED') : 'REDACTED'; });
                    out.metadata = meta;
                }
                return out;
            }

            if (maskSensitive) {
                items = items.map(maskItem);
            }

            // Prepare filename
            const nowStr = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `export-${exportType}-${nowStr}.${format === 'csv' ? 'csv' : 'json'}`;

            // Helpers: convert to CSV and trigger download
            function toCSV(arr) {
                if (!Array.isArray(arr) || arr.length === 0) return '';
                const keys = new Set();
                arr.forEach(o => { if (o && typeof o === 'object') Object.keys(o).forEach(k => keys.add(k)); });
                const cols = Array.from(keys);
                const escape = (v) => `"${String(v === undefined || v === null ? '' : v).replace(/"/g, '""')}"`;
                const rows = [];
                rows.push(cols.map(escape).join(','));
                arr.forEach(o => {
                    const row = cols.map(k => {
                        let v = o[k];
                        if (Array.isArray(v)) v = v.join('; ');
                        else if (typeof v === 'object' && v !== null) v = JSON.stringify(v);
                        return escape(v);
                    });
                    rows.push(row.join(','));
                });
                return rows.join('\r\n');
            }

            function downloadBlob(blob, filename) {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                setTimeout(() => URL.revokeObjectURL(url), 1000);
            }

            if (format === 'json') {
                const blob = new Blob([JSON.stringify(items, null, 2)], { type: 'application/json' });
                downloadBlob(blob, filename);
            } else {
                const csv = toCSV(items);
                const blob = new Blob([csv], { type: 'text/csv' });
                downloadBlob(blob, filename);
            }

            this.showToast('Export started — your download should begin shortly', 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.showToast('Export failed', 'error');
        }
    }

    async loadRecentIntelligence() {
        try {
            const response = await fetch('/api/osint-feed/data?limit=5');
            const data = await response.json();

            if (data.success) {
                this.updateRecentIntelligenceUI(data.data);
            }
        } catch (error) {
            console.error('Failed to load recent intelligence:', error);
        }
    }

    updateRecentIntelligenceUI(data) {
        const container = document.getElementById('recent-intelligence');
        if (!container) return;

        if (!data || data.length === 0) {
            container.innerHTML = '<div class="no-data">No recent intelligence found</div>';
            return;
        }

        container.innerHTML = data.map(item => `
            <div class="intelligence-item">
                <div class="intelligence-header">
                    <h4>${item.title || 'No Title'}</h4>
                    <span class="intelligence-type">${item.type || 'Unknown'}</span>
                </div>
                <div class="intelligence-content">
                    <p>${(item.description || item.content || 'No description available').substring(0, 100)}${(item.description || item.content || '').length > 100 ? '...' : ''}</p>
                    <p>Risk Score: ${item.risk_score || 'N/A'}</p>
                    <p>Date: ${this.formatDate(item.created_at)}</p>
                </div>
            </div>
        `).join('');
    }

    async loadSourceActivity() {
        try {
            const response = await fetch('/api/bot/status');
            const data = await response.json();

            if (data.success) {
                this.updateSourceActivityUI(data.statuses);
            } else {
                console.error('Failed to fetch bot statuses:', data.error);
            }
        } catch (error) {
            console.error('Failed to load source activity:', error);
        }
    }

    updateSourceActivityUI(botStatuses) {
        const container = document.getElementById('source-activity-list');
        if (!container) return;

        const sources = Object.entries(botStatuses).map(([type, status]) => ({
            name: type.charAt(0).toUpperCase() + type.slice(1) + ' Web Bot',
            status: status.status || 'unknown',
            last_run: status.last_run,
            next_run: status.next_run
        }));

        if (sources.length === 0) {
            container.innerHTML = '<div class="no-data">No source activity data</div>';
            return;
        }

        container.innerHTML = sources.map(source => `
            <div class="source-item">
                <div class="source-header">
                    <h4>${source.name}</h4>
                    <span class="source-status ${source.status}">${source.status}</span>
                </div>
                <div class="source-content">
                    <p>Last Run: ${source.last_run ? this.formatDate(source.last_run) : 'Never'}</p>
                    <p>Next Run: ${source.next_run ? this.formatDate(source.next_run) : 'Not scheduled'}</p>
                </div>
            </div>
        `).join('');
    }

    async loadBreachLeakData() {
        try {
            const response = await fetch('/api/user/breach-leak-data');
            const data = await response.json();

            if (data.success) {
                this.breachLeakData = data.data;
                this.updateBreachLeakUI();
            }
        } catch (error) {
            console.error('Failed to load breach-leak data:', error);
        }
    }

    updateBreachLeakUI() {
        const container = document.getElementById('breach-leak-list');
        if (!container) return;

        if (this.breachLeakData.length === 0) {
            container.innerHTML = '<div class="no-data">No breach-leak data found</div>';
            return;
        }

        container.innerHTML = this.breachLeakData.map(item => `
            <div class="data-item">
                <div class="data-header">
                    <h4>${item.title}</h4>
                    <span class="data-type">${item.type}</span>
                </div>
                <div class="data-content">
                    <p>${item.description}</p>
                    <p>Risk Score: ${item.risk_score}</p>
                    <p>Date: ${this.formatDate(item.created_at)}</p>
                </div>
            </div>
        `).join('');
    }


    updateCVEsUI() {
        const container = document.getElementById('cves-body');
        if (!container) return;

        if (this.cveData.length === 0) {
            container.innerHTML = '<tr><td colspan="7">No CVEs found</td></tr>';
            return;
        }

        container.innerHTML = this.cveData.map(cve => `
            <tr>
                <td>${cve.cve_id || 'N/A'}</td>
                <td>${this.formatDate(cve.published_date)}</td>
                <td><span class="severity-badge ${cve.severity || 'unknown'}">${cve.severity || 'Unknown'}</span></td>
                <td>${cve.cvss_score || 'N/A'}</td>
                <td>${cve.affected_products || 'N/A'}</td>
                <td>${(cve.description || 'No description available').substring(0, 100)}${(cve.description || '').length > 100 ? '...' : ''}</td>
                <td>
                    <button class="btn btn-sm" onclick="dashboard.viewCVE('${cve.cve_id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `).join('');
    }

    async loadCases() {
        try {
            const response = await fetch('/api/user/cases');
            const data = await response.json();

            if (data.success) {
                this.cases = data.cases;
                this.updateCasesUI();
            }
        } catch (error) {
            console.error('Failed to load cases:', error);
        }
    }

    updateCasesUI() {
        const container = document.getElementById('cases-list');
        if (!container) return;

        if (this.cases.length === 0) {
            container.innerHTML = '<div class="no-data">No cases found</div>';
            return;
        }

        container.innerHTML = this.cases.map(caseItem => `
            <div class="case-item">
                <div class="case-header">
                    <h4>${caseItem.title}</h4>
                    <span class="case-status ${caseItem.status}">${caseItem.status}</span>
                </div>
                <div class="case-content">
                    <p>${caseItem.description}</p>
                    <p>Priority: ${caseItem.priority}</p>
                    <p>Created: ${this.formatDate(caseItem.created_at)}</p>
                </div>
            </div>
        `).join('');
    }

    // Modal methods
    openItemDetailsModal(item) {
        const modal = document.getElementById('item-details-modal');
        if (!modal) return;

        document.getElementById('item-details-title').textContent = item.title;
        document.getElementById('item-details-content').innerHTML = `
            <p><strong>Type:</strong> ${item.type}</p>
            <p><strong>Description:</strong> ${item.description}</p>
            <p><strong>Risk Score:</strong> ${item.risk_score}</p>
            <p><strong>Date:</strong> ${this.formatDate(item.created_at)}</p>
        `;

        // Show modal
        modal.classList.add('active');
    }

    closeItemDetailsModal() {
        const modal = document.getElementById('item-details-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    openCreateWatchlistModal() {
        const modal = document.getElementById('create-watchlist-modal');
        if (modal) {
            modal.classList.add('active');
        }
    }

    closeCreateWatchlistModal() {
        const modal = document.getElementById('create-watchlist-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    openCreateAlertModal() {
        const modal = document.getElementById('create-alert-modal');
        if (modal) {
            modal.classList.add('active');
        }
    }

    closeCreateAlertModal() {
        const modal = document.getElementById('create-alert-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    openCreateCaseModal() {
        const modal = document.getElementById('create-case-modal');
        if (modal) {
            modal.classList.add('active');
        }
    }

    closeCreateCaseModal() {
        const modal = document.getElementById('create-case-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    async handleCreateWatchlist(e) {
        e.preventDefault();

        const name = document.getElementById('watchlist-name').value.trim();
        const description = document.getElementById('watchlist-description').value.trim();
        const query = document.getElementById('watchlist-query').value.trim();
        const tags = document.getElementById('watchlist-tags').value.trim().split(',').map(t => t.trim()).filter(t => t !== '');

        if (!name || !query) {
            this.showToast('Name and query are required', 'error');
            return;
        }

        try {
            const response = await fetch('/api/user/watchlists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name,
                    description,
                    query,
                    tags
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Watchlist created successfully', 'success');
                this.closeCreateWatchlistModal();
                this.loadWatchlists();
            } else {
                this.showToast(data.error || 'Failed to create watchlist', 'error');
            }
        } catch (error) {
            console.error('Error creating watchlist:', error);
            this.showToast('Failed to create watchlist', 'error');
        }
    }

    async handleCreateAlert(e) {
        e.preventDefault();

        const title = document.getElementById('alert-title').value.trim();
        const description = document.getElementById('alert-description').value.trim();
        const query = document.getElementById('alert-query').value.trim();
        const severity = document.getElementById('alert-severity').value;
        const type = document.getElementById('alert-type').value;
        const tags = document.getElementById('alert-tags').value.trim().split(',').map(t => t.trim()).filter(t => t !== '');

        if (!title || !query) {
            this.showToast('Title and query are required', 'error');
            return;
        }

        try {
            const response = await fetch('/api/user/alerts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title,
                    description,
                    query,
                    severity,
                    type,
                    tags
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Alert created successfully', 'success');
                this.closeCreateAlertModal();
                this.loadAlerts();
            } else {
                this.showToast(data.error || 'Failed to create alert', 'error');
            }
        } catch (error) {
            console.error('Error creating alert:', error);
            this.showToast('Failed to create alert', 'error');
        }
    }

    async handleCreateCase(e) {
        e.preventDefault();

        const title = document.getElementById('case-title').value.trim();
        const description = document.getElementById('case-description').value.trim();
        const severity = document.getElementById('case-severity').value;
        const status = document.getElementById('case-status').value;
        const tags = document.getElementById('case-tags').value.trim().split(',').map(t => t.trim()).filter(t => t !== '');

        if (!title) {
            this.showToast('Title is required', 'error');
            return;
        }

        try {
            const response = await fetch('/api/user/cases', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title,
                    description,
                    severity,
                    status,
                    tags
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Case created successfully', 'success');
                this.closeCreateCaseModal();
                this.loadCases();
            } else {
                this.showToast(data.error || 'Failed to create case', 'error');
            }
        } catch (error) {
            console.error('Error creating case:', error);
            this.showToast('Failed to create case', 'error');
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }

    formatDate(dateString) {
        const options = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        };
        return new Intl.DateTimeFormat('en-US', options).format(new Date(dateString));
    }

    toggleTheme() {
        const body = document.body;
        body.classList.toggle('dark-theme');

        // Save preference to local storage
        const isDark = body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }

    logout() {
        // Perform logout logic, e.g., invalidate session, redirect to login page, etc.
        console.log('Logging out...');
        // Redirect to login page (for example)
        window.location.href = '/login';
    }

    setActiveNavLink() {
        const links = document.querySelectorAll('.nav-link');
        links.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-section') === this.currentSection) {
                link.classList.add('active');
            }
        });
    }
}

// Initialize dashboard
const dashboard = new UserDashboard();
