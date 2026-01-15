document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('apiManagerModal');
    const container = document.getElementById('api-manager-container');
    const refreshBtn = document.getElementById('refresh-api-manager-btn');
    const closeBtn = modal.querySelector('.btn-close');

    function showModal() {
        modal.classList.add('show');
        modal.style.display = 'block';
        loadApiIntegrations();
    }

    function hideModal() {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }

    async function loadApiIntegrations() {
        container.innerHTML = '<p>Loading API integrations...</p>';
        try {
            // Load integrated APIs
            const response = await fetch('/api/config/integrated_apis');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();

            if (!data.success || Object.keys(data.integrated_apis).length === 0) {
                container.innerHTML = '<p>No API integrations found.</p>';
                return;
            }

            let html = '<h3>Integrated APIs</h3><table style="width:100%; border-collapse: collapse;">';
            html += '<thead><tr><th>Name</th><th>Status</th><th>Actions</th></tr></thead><tbody>';

            for (const [name, api] of Object.entries(data.integrated_apis)) {
                html += `<tr style="border-bottom: 1px solid #9370db;">
                    <td>${name}</td>
                    <td>${api.enabled ? '<span style="color: #48bb78;">Enabled</span>' : '<span style="color: #6c757d;">Disabled</span>'}</td>
                    <td>
                        <button style="margin-right: 8px;" onclick="toggleApi('${name}', ${api.enabled})">${api.enabled ? 'Disable' : 'Enable'}</button>
                        <button onclick="removeApi('${name}')">Remove</button>
                    </td>
                </tr>`;
            }

            html += '</tbody></table>';

            // Add vault search section
            html += '<h3>Vault Search</h3>';
            html += '<div id="vault-search-section">';
            html += '<input type="text" id="vault-query" placeholder="Search breaches/leaks" style="width: 70%;">';
            html += '<button onclick="searchVault()">Search</button>';
            html += '<div id="vault-results"></div>';
            html += '</div>';

            // Add vault stats
            html += '<h3>Vault Stats</h3>';
            html += '<div id="vault-stats"></div>';

            container.innerHTML = html;
            loadVaultStats();
        } catch (error) {
            container.innerHTML = `<p style="color: red;">Error loading API integrations: ${error.message}</p>`;
        }
    }

    async function loadVaultStats() {
        try {
            const response = await fetch('/vault/stats');
            const stats = await response.json();
            const statsDiv = document.getElementById('vault-stats');
            if (stats.success) {
                statsDiv.innerHTML = `
                    <p>Total Breaches: ${stats.total_breaches}</p>
                    <p>Total Leaks: ${stats.total_leaks}</p>
                    <p>Last Updated: ${stats.last_updated}</p>
                `;
            } else {
                statsDiv.innerHTML = '<p>Error loading stats</p>';
            }
        } catch (error) {
            document.getElementById('vault-stats').innerHTML = '<p>Error loading stats</p>';
        }
    }

    window.searchVault = async function() {
        const query = document.getElementById('vault-query').value;
        const resultsDiv = document.getElementById('vault-results');
        resultsDiv.innerHTML = '<p>Searching...</p>';
        try {
            const response = await fetch(`/vault/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            if (data.success && data.results.length > 0) {
                let html = '<ul>';
                data.results.forEach(item => {
                    html += `<li>${item.title} - ${item.description}</li>`;
                });
                html += '</ul>';
                resultsDiv.innerHTML = html;
            } else {
                resultsDiv.innerHTML = '<p>No results found</p>';
            }
        } catch (error) {
            resultsDiv.innerHTML = `<p style="color: red;">Error searching vault: ${error.message}</p>`;
        }
    };

    window.toggleApi = async function(name, currentlyEnabled) {
        try {
            const response = await fetch('/api/config/integrated_apis');
            const data = await response.json();
            if (data.success && data.integrated_apis[name]) {
                const api = data.integrated_apis[name];
                api.enabled = !currentlyEnabled;
                const updateResponse = await fetch('/api/config/integrate_api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(api)
                });
                if (updateResponse.ok) {
                    await loadApiIntegrations();
                } else {
                    throw new Error('Failed to update API');
                }
            }
        } catch (error) {
            alert(`Error toggling API: ${error.message}`);
        }
    };

    window.removeApi = async function(name) {
        if (!confirm(`Are you sure you want to remove API integration "${name}"?`)) return;
        try {
            const response = await fetch('/api/config/integrate_api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service: name, action: 'remove' })
            });
            if (response.ok) {
                await loadApiIntegrations();
            } else {
                throw new Error('Failed to remove API');
            }
        } catch (error) {
            alert(`Error removing API: ${error.message}`);
        }
    };

    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadApiIntegrations);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', hideModal);
    }

    // Attach event to API Manager button
    const apiManagerBtn = document.getElementById('dynamic-api-manager-btn');
    if (apiManagerBtn) {
        apiManagerBtn.addEventListener('click', showModal);
    }
});
