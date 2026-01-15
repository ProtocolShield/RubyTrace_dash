// Item Details functionality for user panel
class ItemDetailsManager {
    constructor() {
        this.modal = null;
        this.init();
    }

    init() {
        // Create modal structure if not exists
        this.createModal();
        // Listen for global events if needed
        document.addEventListener('showItemDetails', (e) => {
            this.showDetails(e.detail.id, e.detail.type);
        });
    }

    createModal() {
        if (document.getElementById('item-details-modal')) return;

        const modal = document.createElement('div');
        modal.id = 'item-details-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3 id="modal-title">Item Details</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body" id="modal-body">
                    <div class="loading">Loading details...</div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" id="close-details">Close</button>
                    <button class="btn btn-primary" id="add-to-watchlist">Add to Watchlist</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Event listeners
        modal.querySelector('.close-modal').addEventListener('click', () => this.closeModal());
        modal.querySelector('#close-details').addEventListener('click', () => this.closeModal());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeModal();
        });

        modal.querySelector('#add-to-watchlist').addEventListener('click', () => {
            this.addToWatchlist(this.currentItemId, this.currentItemType);
        });

        this.modal = modal;
    }

    async showDetails(id, type) {
        if (!id || !type) return;

        this.currentItemId = id;
        this.currentItemType = type;

        const modalBody = this.modal.querySelector('#modal-body');
        modalBody.innerHTML = '<div class="loading">Loading details...</div>';

        this.modal.classList.add('active');

        try {
            const response = await fetch(`/api/user/item/${id}?type=${type}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load item details: ${response.status}`);
            }

            const data = await response.json();
            this.displayDetails(data, type);

        } catch (error) {
            console.error('Error loading item details:', error);
            modalBody.innerHTML = '<div class="error">Failed to load details. Please try again.</div>';
            this.showToast('Failed to load item details', 'error');
        }
    }

    displayDetails(item, type) {
        const modalTitle = this.modal.querySelector('#modal-title');
        const modalBody = this.modal.querySelector('#modal-body');

        let title = 'Item Details';
        let content = '';

        switch (type) {
            case 'emails':
                title = `Email Details: ${this.maskEmail(item.email)}`;
                content = `
                    <div class="detail-section">
                        <h4>Email</h4>
                        <p>${this.maskEmail(item.email)}</p>
                    </div>
                    <div class="detail-section">
                        <h4>Breach Information</h4>
                        <p><strong>Breach:</strong> ${item.breach || 'N/A'}</p>
                        <p><strong>Date:</strong> ${item.date || 'N/A'}</p>
                        <p><strong>Password (masked):</strong> ${item.password ? '****' : 'N/A'}</p>
                    </div>
                    ${item.associated_data ? `
                    <div class="detail-section">
                        <h4>Associated Data</h4>
                        <ul>
                            ${Object.entries(item.associated_data).map(([key, value]) => 
                                `<li><strong>${key}:</strong> ${typeof value === 'string' ? this.maskSensitive(value) : JSON.stringify(value)}</li>`
                            ).join('')}
                        </ul>
                    </div>` : ''}
                `;
                break;
            case 'phones':
                title = `Phone Details: ${this.maskPhone(item.phone)}`;
                content = `
                    <div class="detail-section">
                        <h4>Phone</h4>
                        <p>${this.maskPhone(item.phone)}</p>
                    </div>
                    <div class="detail-section">
                        <h4>Carrier Info</h4>
                        <p><strong>Carrier:</strong> ${item.carrier || 'N/A'}</p>
                        <p><strong>Date:</strong> ${item.date || 'N/A'}</p>
                    </div>
                `;
                break;
            case 'cves':
                title = `CVE Details: ${item.cve_id}`;
                content = `
                    <div class="detail-section">
                        <h4>CVE ID</h4>
                        <p>${item.cve_id}</p>
                    </div>
                    <div class="detail-section">
                        <h4>Severity & Score</h4>
                        <p><strong>Severity:</strong> ${item.severity}</p>
                        <p><strong>CVSS Score:</strong> ${item.cvss_score}</p>
                    </div>
                    <div class="detail-section">
                        <h4>Description</h4>
                        <p>${item.description || 'N/A'}</p>
                    </div>
                    ${item.references ? `
                    <div class="detail-section">
                        <h4>References</h4>
                        <ul>
                            ${item.references.map(ref => `<li><a href="${ref}" target="_blank">${ref}</a></li>`).join('')}
                        </ul>
                    </div>` : ''}
                `;
                break;
            case 'breaches':
                title = `Breach Details: ${item.name}`;
                content = `
                    <div class="detail-section">
                        <h4>Breach Name</h4>
                        <p>${item.name}</p>
                    </div>
                    <div class="detail-section">
                        <h4>Details</h4>
                        <p><strong>Records Affected:</strong> ${item.records_affected}</p>
                        <p><strong>Breach Date:</strong> ${item.breach_date}</p>
                        <p><strong>Description:</strong> ${item.description || 'N/A'}</p>
                    </div>
                `;
                break;
            case 'keywords':
                title = `Keyword Details: ${item.keyword}`;
                content = `
                    <div class="detail-section">
                        <h4>Keyword</h4>
                        <p>${item.keyword}</p>
                    </div>
                    <div class="detail-section">
                        <h4>Source Info</h4>
                        <p><strong>Source:</strong> ${item.source}</p>
                        <p><strong>Date:</strong> ${item.date}</p>
                        <p><strong>Context:</strong> ${item.context || 'N/A'}</p>
                    </div>
                `;
                break;
            default:
                content = '<div class="error">Unknown item type</div>';
        }

        modalTitle.textContent = title;
        modalBody.innerHTML = content;
    }

    closeModal() {
        this.modal.classList.remove('active');
    }

    async addToWatchlist(id, type) {
        try {
            const response = await fetch('/api/user/watchlists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    item_id: id,
                    item_type: type,
                    name: `Watchlist for ${type} ${id}`
                })
            });

            if (response.ok) {
                this.showToast('Added to watchlist', 'success');
                this.closeModal();
                // Trigger watchlist refresh if manager exists
                if (window.watchlistsManager) {
                    window.watchlistsManager.loadWatchlists();
                }
            } else {
                throw new Error('Failed to add to watchlist');
            }

        } catch (error) {
            console.error('Error adding to watchlist:', error);
            this.showToast('Failed to add to watchlist', 'error');
        }
    }

    maskEmail(email) {
        if (!email) return 'N/A';
        const [local, domain] = email.split('@');
        return local.length > 2 ? `${local.substring(0, 2)}***@${domain}` : `${local}***@${domain}`;
    }

    maskPhone(phone) {
        if (!phone) return 'N/A';
        return phone.replace(/\d(?=\d{4})/g, '*');
    }

    maskSensitive(value) {
        // Basic masking for sensitive strings like passwords, keys
        if (typeof value !== 'string') return value;
        if (value.includes('@') && value.includes('.')) return this.maskEmail(value);
        if (/^\+?\d{10,15}$/.test(value)) return this.maskPhone(value);
        if (value.length > 6 && (value.includes('pass') || value.includes('key'))) {
            return value.substring(0, 4) + '****';
        }
        return value;
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
    window.itemDetailsManager = new ItemDetailsManager();
});
