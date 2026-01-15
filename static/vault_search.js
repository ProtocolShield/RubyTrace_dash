/**
 * Breach/Leak Vault Search Interface
 * Provides advanced search and filtering for breach and leak data
 */

class VaultSearch {
  constructor(apiBaseUrl) {
    this.apiBaseUrl = apiBaseUrl;
    this.currentPage = 1;
    this.searchType = 'breaches'; // 'breaches' or 'leaks'
    this.filters = {};
    this.init();
  }

  init() {
    this.renderUI();
    this.attachEventListeners();
    this.loadStats();
  }

  renderUI() {
    const container = document.getElementById('vault-search-container');
    if (!container) return;

    container.innerHTML = `
      <h2>Breach & Leak Data Vault</h2>

      <!-- Statistics Section -->
      <div id="vault-stats" class="stats-section">
        <h3>Vault Statistics</h3>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">Total Breaches:</span>
            <span class="stat-value" id="total-breaches">-</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Total Records:</span>
            <span class="stat-value" id="total-records">-</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Total Leaks:</span>
            <span class="stat-value" id="total-leaks">-</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Recent (30 days):</span>
            <span class="stat-value" id="recent-activity">-</span>
          </div>
        </div>
      </div>

      <!-- Search Controls -->
      <div class="search-controls">
        <div class="search-type-toggle">
          <button id="search-breaches" class="active">Search Breaches</button>
          <button id="search-leaks">Search Leaks</button>
        </div>

        <div class="search-inputs">
          <input type="text" id="search-query" placeholder="Search by name, description, or keywords..." />
          <button id="search-btn">Search</button>
          <button id="clear-filters-btn">Clear Filters</button>
        </div>

        <!-- Advanced Filters -->
        <div id="advanced-filters" class="advanced-filters">
          <h4>Advanced Filters</h4>
          <div class="filter-row">
            <label for="min-records">Min Records:</label>
            <input type="number" id="min-records" placeholder="1000" />
            <label for="max-records">Max Records:</label>
            <input type="number" id="max-records" placeholder="1000000" />
          </div>
          <div class="filter-row">
            <label for="date-from">From Date:</label>
            <input type="date" id="date-from" />
            <label for="date-to">To Date:</label>
            <input type="date" id="date-to" />
          </div>
          <div class="filter-row">
            <label for="data-types">Data Types:</label>
            <input type="text" id="data-types" placeholder="email,password,phone" />
            <label for="organizations">Organizations:</label>
            <input type="text" id="organizations" placeholder="company names" />
          </div>
          <div class="filter-row">
            <label for="sort-by">Sort By:</label>
            <select id="sort-by">
              <option value="discovery_date">Discovery Date</option>
              <option value="name">Name</option>
              <option value="records_affected">Records Affected</option>
            </select>
            <label for="sort-order">Order:</label>
            <select id="sort-order">
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Results Section -->
      <div id="search-results" class="search-results">
        <div id="results-header">
          <h3>Search Results</h3>
          <span id="results-count">No results</span>
        </div>
        <div id="results-list"></div>
        <div id="pagination-controls" class="pagination">
          <button id="prev-page" disabled>Previous</button>
          <span id="page-info">Page 1</span>
          <button id="next-page">Next</button>
        </div>
      </div>

      <div id="vault-message" style="color: red; margin-top: 10px;"></div>
    `;
  }

  attachEventListeners() {
    // Search type toggle
    document.getElementById('search-breaches').addEventListener('click', () => {
      this.setSearchType('breaches');
    });
    document.getElementById('search-leaks').addEventListener('click', () => {
      this.setSearchType('leaks');
    });

    // Search button
    document.getElementById('search-btn').addEventListener('click', () => {
      this.performSearch();
    });

    // Clear filters
    document.getElementById('clear-filters-btn').addEventListener('click', () => {
      this.clearFilters();
    });

    // Pagination
    document.getElementById('prev-page').addEventListener('click', () => {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.performSearch();
      }
    });
    document.getElementById('next-page').addEventListener('click', () => {
      this.currentPage++;
      this.performSearch();
    });

    // Enter key for search
    document.getElementById('search-query').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.performSearch();
      }
    });
  }

  setSearchType(type) {
    this.searchType = type;
    this.currentPage = 1;

    // Update button states
    document.getElementById('search-breaches').classList.toggle('active', type === 'breaches');
    document.getElementById('search-leaks').classList.toggle('active', type === 'leaks');

    // Clear results
    document.getElementById('results-list').innerHTML = '';
    document.getElementById('results-count').textContent = 'No results';
  }

  async loadStats() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/vault/stats`);
      if (!response.ok) throw new Error('Failed to load stats');
      const stats = await response.json();

      document.getElementById('total-breaches').textContent = stats.breach_stats?.total_breaches || 0;
      document.getElementById('total-records').textContent = stats.breach_stats?.total_records_affected || 0;
      document.getElementById('total-leaks').textContent = stats.leak_stats?.total_leaks || 0;
      document.getElementById('recent-activity').textContent =
        (stats.recent_activity?.breaches_last_30_days || 0) + ' breaches, ' +
        (stats.recent_activity?.leaks_last_30_days || 0) + ' leaks';
    } catch (error) {
      console.error('Error loading vault stats:', error);
    }
  }

  collectFilters() {
    this.filters = {
      min_records: document.getElementById('min-records').value || null,
      max_records: document.getElementById('max-records').value || null,
      date_from: document.getElementById('date-from').value || null,
      date_to: document.getElementById('date-to').value || null,
      data_types: document.getElementById('data-types').value.split(',').map(s => s.trim()).filter(s => s) || null,
      organizations: document.getElementById('organizations').value.split(',').map(s => s.trim()).filter(s => s) || null,
      sort_by: document.getElementById('sort-by').value || 'discovery_date',
      sort_order: document.getElementById('sort-order').value || 'desc'
    };
  }

  async performSearch() {
    const query = document.getElementById('search-query').value.trim();
    this.collectFilters();

    const messageDiv = document.getElementById('vault-message');
    messageDiv.textContent = 'Searching...';

    try {
      const params = new URLSearchParams({
        query: query,
        page: this.currentPage,
        per_page: 20,
        ...Object.fromEntries(
          Object.entries(this.filters).filter(([_, v]) => v !== null && v !== '')
        )
      });

      const endpoint = this.searchType === 'breaches' ? 'search_breaches' : 'search_leaks';
      const response = await fetch(`${this.apiBaseUrl}/api/vault/${endpoint}?${params}`);

      if (!response.ok) throw new Error('Search failed');
      const results = await response.json();

      this.displayResults(results);
      messageDiv.textContent = '';

    } catch (error) {
      messageDiv.textContent = `Error: ${error.message}`;
      console.error('Search error:', error);
    }
  }

  displayResults(results) {
    const resultsList = document.getElementById('results-list');
    const resultsCount = document.getElementById('results-count');
    const pageInfo = document.getElementById('page-info');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');

    if (results.error) {
      resultsList.innerHTML = `<p class="error">${results.error}</p>`;
      resultsCount.textContent = 'Error';
      return;
    }

    const items = results.results || [];
    resultsCount.textContent = `Found ${results.total} results`;

    if (items.length === 0) {
      resultsList.innerHTML = '<p>No results found.</p>';
    } else {
      resultsList.innerHTML = items.map(item => this.renderResultItem(item)).join('');
    }

    // Update pagination
    pageInfo.textContent = `Page ${results.page} of ${results.total_pages}`;
    prevBtn.disabled = results.page <= 1;
    nextBtn.disabled = results.page >= results.total_pages;
  }

  renderResultItem(item) {
    if (this.searchType === 'breaches') {
      return `
        <div class="result-item breach-item">
          <h4>${item.name}</h4>
          <p class="description">${item.description || 'No description available'}</p>
          <div class="item-meta">
            <span class="meta-item">Records: ${item.records_affected?.toLocaleString() || 'Unknown'}</span>
            <span class="meta-item">Discovered: ${item.discovery_date || 'Unknown'}</span>
            <span class="meta-item">Data Types: ${item.data_types_exposed?.join(', ') || 'Unknown'}</span>
          </div>
          <div class="item-actions">
            <a href="${item.source_url}" target="_blank" rel="noopener">View Source</a>
          </div>
        </div>
      `;
    } else {
      return `
        <div class="result-item leak-item">
          <h4>${item.source}</h4>
          <p class="description">${item.data_content || 'No content preview available'}</p>
          <div class="item-meta">
            <span class="meta-item">Status: ${item.verification_status || 'Unknown'}</span>
            <span class="meta-item">Created: ${item.created_at || 'Unknown'}</span>
          </div>
        </div>
      `;
    }
  }

  clearFilters() {
    document.getElementById('search-query').value = '';
    document.getElementById('min-records').value = '';
    document.getElementById('max-records').value = '';
    document.getElementById('date-from').value = '';
    document.getElementById('date-to').value = '';
    document.getElementById('data-types').value = '';
    document.getElementById('organizations').value = '';
    document.getElementById('sort-by').value = 'discovery_date';
    document.getElementById('sort-order').value = 'desc';

    this.filters = {};
    this.currentPage = 1;
    document.getElementById('results-list').innerHTML = '';
    document.getElementById('results-count').textContent = 'No results';
  }
}

// Initialize Vault Search on page load
document.addEventListener('DOMContentLoaded', () => {
  const apiBaseUrl = ''; // Set base URL if needed
  new VaultSearch(apiBaseUrl);
});
