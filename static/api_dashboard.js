/**
 * API Dashboard - Status Monitoring and Data Flow Control
 * Provides real-time monitoring of API integrations and data flow controls
 */

class APIDashboard {
  constructor(apiBaseUrl) {
    this.apiBaseUrl = apiBaseUrl;
    this.integrations = [];
    this.dataFlows = {};
    this.statusInterval = null;
    this.init();
  }

  async init() {
    await this.loadDashboardData();
    this.renderUI();
    this.attachEventListeners();
    this.startStatusMonitoring();
  }

  async loadDashboardData() {
    try {
      // Load integrations status
      const statusResponse = await fetch(`${this.apiBaseUrl}/api/integrations/status`);
      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        this.integrations = Object.values(statusData);
      }

      // Load data flow configurations
      const flowResponse = await fetch(`${this.apiBaseUrl}/api/data-flow/config`);
      if (flowResponse.ok) {
        this.dataFlows = await flowResponse.json();
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      this.integrations = [];
      this.dataFlows = {};
    }
  }

  renderUI() {
    const container = document.getElementById('api-dashboard-container');
    if (!container) return;

    container.innerHTML = `
      <h2>API Dashboard</h2>

      <!-- Status Overview -->
      <div class="dashboard-section">
        <h3>Integration Status</h3>
        <div id="status-overview" class="status-grid">
          ${this.renderStatusOverview()}
        </div>
      </div>

      <!-- Detailed Status Cards -->
      <div class="dashboard-section">
        <h3>API Integration Details</h3>
        <div id="integration-cards" class="cards-grid">
          ${this.integrations.map(integration => this.renderIntegrationCard(integration)).join('')}
        </div>
      </div>

      <!-- Data Flow Controls -->
      <div class="dashboard-section">
        <h3>Data Flow Control</h3>
        <div id="data-flow-controls" class="flow-controls">
          ${this.renderDataFlowControls()}
        </div>
      </div>

      <!-- Pipeline Status -->
      <div class="dashboard-section">
        <h3>Pipeline Status</h3>
        <div id="pipeline-status" class="pipeline-status">
          ${this.renderPipelineStatus()}
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="dashboard-section">
        <h3>Quick Actions</h3>
        <div class="quick-actions">
          <button id="test-all-integrations" class="action-btn">Test All Integrations</button>
          <button id="refresh-status" class="action-btn">Refresh Status</button>
          <button id="reset-pipeline" class="action-btn warning">Reset Pipeline</button>
        </div>
      </div>

      <div id="dashboard-message" style="color: blue; margin-top: 10px;"></div>
    `;
  }

  renderStatusOverview() {
    const total = this.integrations.length;
    const connected = this.integrations.filter(i => i.connected).length;
    const errors = this.integrations.filter(i => !i.connected).length;

    return `
      <div class="status-item">
        <span class="status-label">Total APIs:</span>
        <span class="status-value">${total}</span>
      </div>
      <div class="status-item">
        <span class="status-label">Connected:</span>
        <span class="status-value connected">${connected}</span>
      </div>
      <div class="status-item">
        <span class="status-label">Errors:</span>
        <span class="status-value error">${errors}</span>
      </div>
      <div class="status-item">
        <span class="status-label">Uptime:</span>
        <span class="status-value" id="uptime-percent">--</span>
      </div>
    `;
  }

  renderIntegrationCard(integration) {
    const statusClass = integration.connected ? 'connected' : 'error';
    const statusText = integration.connected ? 'Connected' : 'Error';

    return `
      <div class="integration-card ${statusClass}" data-name="${integration.name}">
        <div class="card-header">
          <h4>${integration.name}</h4>
          <span class="status-badge ${statusClass}">${statusText}</span>
        </div>
        <div class="card-content">
          <div class="capabilities">
            <strong>Capabilities:</strong>
            <div class="capability-list">
              ${integration.capabilities.map(cap => `<span class="capability">${cap}</span>`).join('')}
            </div>
          </div>
          <div class="last-tested">
            <strong>Last Tested:</strong> ${integration.last_tested || 'Never'}
          </div>
          <div class="rate-limits">
            <strong>Rate Limits:</strong>
            <span>${integration.config?.rate_limits?.requests_per_minute || 'N/A'}/min</span>
          </div>
        </div>
        <div class="card-actions">
          <button class="test-btn" data-name="${integration.name}">Test</button>
          <button class="configure-btn" data-name="${integration.name}">Configure</button>
        </div>
      </div>
    `;
  }

  renderDataFlowControls() {
    return `
      <div class="flow-control-item">
        <label for="auto-restructure">Auto Pipeline Restructure:</label>
        <input type="checkbox" id="auto-restructure" checked />
        <span class="control-desc">Automatically restructure pipeline when APIs change</span>
      </div>
      <div class="flow-control-item">
        <label for="data-validation">Data Validation:</label>
        <input type="checkbox" id="data-validation" checked />
        <span class="control-desc">Validate data before processing</span>
      </div>
      <div class="flow-control-item">
        <label for="error-handling">Enhanced Error Handling:</label>
        <input type="checkbox" id="error-handling" checked />
        <span class="control-desc">Use advanced error handling and retry logic</span>
      </div>
      <div class="flow-control-item">
        <label for="rate-limiting">Global Rate Limiting:</label>
        <input type="checkbox" id="rate-limiting" checked />
        <span class="control-desc">Apply global rate limiting across all APIs</span>
      </div>
      <div class="flow-control-item">
        <label for="caching">Response Caching:</label>
        <input type="checkbox" id="caching" />
        <span class="control-desc">Cache API responses to reduce load</span>
      </div>
    `;
  }

  renderPipelineStatus() {
    return `
      <div class="pipeline-metrics">
        <div class="metric">
          <span class="metric-label">Active Pipelines:</span>
          <span class="metric-value" id="active-pipelines">3</span>
        </div>
        <div class="metric">
          <span class="metric-label">Data Processed:</span>
          <span class="metric-value" id="data-processed">1.2M</span>
        </div>
        <div class="metric">
          <span class="metric-label">Error Rate:</span>
          <span class="metric-value" id="error-rate">0.5%</span>
        </div>
        <div class="metric">
          <span class="metric-label">Avg Response Time:</span>
          <span class="metric-value" id="avg-response">245ms</span>
        </div>
      </div>
      <div class="pipeline-visualization">
        <div class="pipeline-stage">
          <div class="stage-name">Data Collection</div>
          <div class="stage-status active">Active</div>
        </div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-stage">
          <div class="stage-name">Processing</div>
          <div class="stage-status active">Active</div>
        </div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-stage">
          <div class="stage-name">Storage</div>
          <div class="stage-status active">Active</div>
        </div>
      </div>
    `;
  }

  attachEventListeners() {
    // Test individual integrations
    const cardsContainer = document.getElementById('integration-cards');
    if (cardsContainer) {
      cardsContainer.addEventListener('click', (event) => {
        const target = event.target;
        const integrationName = target.getAttribute('data-name');

        if (target.classList.contains('test-btn')) {
          this.testIntegration(integrationName);
        } else if (target.classList.contains('configure-btn')) {
          this.configureIntegration(integrationName);
        }
      });
    }

    // Quick actions
    document.getElementById('test-all-integrations').addEventListener('click', () => {
      this.testAllIntegrations();
    });

    document.getElementById('refresh-status').addEventListener('click', () => {
      this.refreshStatus();
    });

    document.getElementById('reset-pipeline').addEventListener('click', () => {
      this.resetPipeline();
    });

    // Data flow controls
    const flowControls = document.querySelectorAll('#data-flow-controls input[type="checkbox"]');
    flowControls.forEach(control => {
      control.addEventListener('change', (e) => {
        this.updateDataFlowControl(e.target.id, e.target.checked);
      });
    });
  }

  async testIntegration(name) {
    const messageDiv = document.getElementById('dashboard-message');
    messageDiv.textContent = `Testing ${name} integration...`;

    try {
      const response = await fetch(`${this.apiBaseUrl}/api/integrations/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ integration_name: name })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        messageDiv.style.color = 'green';
        messageDiv.textContent = `${name} integration test successful.`;
        await this.loadDashboardData();
        this.renderUI();
        this.attachEventListeners();
      } else {
        messageDiv.style.color = 'red';
        messageDiv.textContent = `Test failed: ${result.error || 'Unknown error'}`;
      }
    } catch (error) {
      messageDiv.style.color = 'red';
      messageDiv.textContent = `Error testing ${name}: ${error.message}`;
    }
  }

  async testAllIntegrations() {
    const messageDiv = document.getElementById('dashboard-message');
    messageDiv.textContent = 'Testing all integrations...';

    try {
      const response = await fetch(`${this.apiBaseUrl}/api/integrations/test-all`, {
        method: 'POST'
      });

      const result = await response.json();

      if (response.ok && result.success) {
        messageDiv.style.color = 'green';
        messageDiv.textContent = `All integrations tested. ${result.passed}/${result.total} passed.`;
        await this.loadDashboardData();
        this.renderUI();
        this.attachEventListeners();
      } else {
        messageDiv.style.color = 'red';
        messageDiv.textContent = `Test failed: ${result.error || 'Unknown error'}`;
      }
    } catch (error) {
      messageDiv.style.color = 'red';
      messageDiv.textContent = `Error testing integrations: ${error.message}`;
    }
  }

  async refreshStatus() {
    const messageDiv = document.getElementById('dashboard-message');
    messageDiv.textContent = 'Refreshing status...';

    await this.loadDashboardData();
    this.renderUI();
    this.attachEventListeners();

    messageDiv.style.color = 'green';
    messageDiv.textContent = 'Status refreshed successfully.';
  }

  async resetPipeline() {
    if (!confirm('Are you sure you want to reset the pipeline? This may interrupt ongoing processes.')) {
      return;
    }

    const messageDiv = document.getElementById('dashboard-message');
    messageDiv.textContent = 'Resetting pipeline...';

    try {
      const response = await fetch(`${this.apiBaseUrl}/api/pipeline/reset`, {
        method: 'POST'
      });

      const result = await response.json();

      if (response.ok && result.success) {
        messageDiv.style.color = 'green';
        messageDiv.textContent = 'Pipeline reset successfully.';
        await this.loadDashboardData();
        this.renderUI();
        this.attachEventListeners();
      } else {
        messageDiv.style.color = 'red';
        messageDiv.textContent = `Reset failed: ${result.error || 'Unknown error'}`;
      }
    } catch (error) {
      messageDiv.style.color = 'red';
      messageDiv.textContent = `Error resetting pipeline: ${error.message}`;
    }
  }

  async updateDataFlowControl(controlId, enabled) {
    const messageDiv = document.getElementById('dashboard-message');
    messageDiv.textContent = `Updating ${controlId}...`;

    try {
      const response = await fetch(`${this.apiBaseUrl}/api/data-flow/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ control: controlId, enabled: enabled })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        messageDiv.style.color = 'green';
        messageDiv.textContent = `${controlId} updated successfully.`;
      } else {
        messageDiv.style.color = 'red';
        messageDiv.textContent = `Update failed: ${result.error || 'Unknown error'}`;
      }
    } catch (error) {
      messageDiv.style.color = 'red';
      messageDiv.textContent = `Error updating ${controlId}: ${error.message}`;
    }
  }

  configureIntegration(name) {
    // Open configuration modal or redirect to config page
    alert(`Configuration for ${name} integration would open here.`);
  }

  startStatusMonitoring() {
    // Update status every 30 seconds
    this.statusInterval = setInterval(async () => {
      try {
        await this.loadDashboardData();
        this.updateStatusDisplay();
      } catch (error) {
        console.error('Error updating status:', error);
      }
    }, 30000);
  }

  updateStatusDisplay() {
    // Update uptime percentage
    const uptimeElement = document.getElementById('uptime-percent');
    if (uptimeElement) {
      const connected = this.integrations.filter(i => i.connected).length;
      const total = this.integrations.length;
      const uptime = total > 0 ? Math.round((connected / total) * 100) : 0;
      uptimeElement.textContent = `${uptime}%`;
    }

    // Update integration cards
    this.integrations.forEach(integration => {
      const card = document.querySelector(`.integration-card[data-name="${integration.name}"]`);
      if (card) {
        const statusBadge = card.querySelector('.status-badge');
        const statusClass = integration.connected ? 'connected' : 'error';
        const statusText = integration.connected ? 'Connected' : 'Error';

        card.className = `integration-card ${statusClass}`;
        if (statusBadge) {
          statusBadge.className = `status-badge ${statusClass}`;
          statusBadge.textContent = statusText;
        }
      }
    });
  }

  destroy() {
    if (this.statusInterval) {
      clearInterval(this.statusInterval);
    }
  }
}

// Initialize API Dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
  const apiBaseUrl = ''; // Set base URL if needed
  new APIDashboard(apiBaseUrl);
});
