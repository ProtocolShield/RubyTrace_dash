/**
 * Enhanced Data Viewer for Real OSINT Results
 */

let currentData = [];
let currentPage = 1;
const itemsPerPage = 10;

function initDataViewer() {
    loadRealData();
    setupDataViewerControls();
    
    // Auto-refresh every 30 seconds
    setInterval(loadRealData, 30000);
}

async function loadRealData() {
    try {
        const [postsResponse, sourcesResponse, statsResponse] = await Promise.all([
            fetch('/api/posts'),
            fetch('/api/sources'),
            fetch('/api/stats')
        ]);

        const posts = await postsResponse.json();
        const sources = await sourcesResponse.json();
        const stats = await statsResponse.json();

        currentData = posts;
        
        renderDataOverview(posts, sources, stats);
        renderDataTable(posts);
        renderSourcesTable(sources);
        
    } catch (error) {
        console.error('Error loading real data:', error);
        showError('data-viewer-container', 'Error loading real data');
    }
}

function renderDataOverview(posts, sources, stats) {
    const container = document.getElementById('data-overview');
    if (!container) return;

    container.innerHTML = `
        <div class="row">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6 class="card-title">Total Posts</h6>
                                <h3 class="mb-0">${posts.length || 0}</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-newspaper fa-2x opacity-50"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6 class="card-title">Sources</h6>
                                <h3 class="mb-0">${sources.length || 0}</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-globe fa-2x opacity-50"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6 class="card-title">Recent Posts</h6>
                                <h3 class="mb-0">${posts.filter(p => {
                                    const postDate = new Date(p.timestamp || p.created_at);
                                    const dayAgo = new Date();
                                    dayAgo.setDate(dayAgo.getDate() - 1);
                                    return postDate > dayAgo;
                                }).length}</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-clock fa-2x opacity-50"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6 class="card-title">Privacy Keywords</h6>
                                <h3 class="mb-0">${posts.filter(p => 
                                    p.title && (p.title.toLowerCase().includes('privacy') || 
                                              p.title.toLowerCase().includes('security') ||
                                              p.title.toLowerCase().includes('data'))
                                ).length}</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-key fa-2x opacity-50"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderDataTable(posts) {
    const container = document.getElementById('data-table-container');
    if (!container) return;

    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedPosts = posts.slice(startIndex, endIndex);

    let tableHTML = `
        <div class="card">
            <div class="card-header d-flex justify-content-between">
                <h5 class="mb-0">Real OSINT Data Collected</h5>
                <div>
                    <button class="btn btn-sm btn-outline-primary" onclick="loadRealData()">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="searchData()">
                        <i class="fas fa-search"></i> Search
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Title</th>
                                <th>Source</th>
                                <th>Content Preview</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
    `;

    paginatedPosts.forEach(post => {
        const truncatedTitle = (post.title || 'No title').substring(0, 50);
        const truncatedContent = (post.summary || post.content || 'No content').substring(0, 100);
        const date = post.timestamp || post.created_at || 'Unknown';
        const source = post.source || 'Unknown';
        
        tableHTML += `
            <tr>
                <td>
                    <strong>${truncatedTitle}${post.title && post.title.length > 50 ? '...' : ''}</strong>
                </td>
                <td>
                    <span class="badge bg-secondary">${source}</span>
                </td>
                <td>
                    <small class="text-muted">${truncatedContent}${(post.summary || post.content || '').length > 100 ? '...' : ''}</small>
                </td>
                <td>
                    <small>${new Date(date).toLocaleString()}</small>
                </td>
                <td>
                    <a href="${post.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </td>
            </tr>
        `;
    });

    tableHTML += `
                        </tbody>
                    </table>
                </div>
                ${renderPagination(posts.length)}
            </div>
        </div>
    `;

    container.innerHTML = tableHTML;
}

function renderSourcesTable(sources) {
    const container = document.getElementById('sources-table-container');
    if (!container) return;

    let tableHTML = `
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">Monitored Sources</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Source Name</th>
                                <th>URL</th>
                                <th>Type</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
    `;

    sources.forEach(source => {
        const sourceName = source.name || source;
        const sourceUrl = source.url || 'N/A';
        const sourceType = sourceUrl.includes('.onion') ? 'Dark Web' : 'Surface Web';
        const sourceStatus = sourceUrl.includes('.onion') ? 'Tor Required' : 'Active';
        
        tableHTML += `
            <tr>
                <td><strong>${sourceName}</strong></td>
                <td><code>${sourceUrl}</code></td>
                <td>
                    <span class="badge bg-${sourceType === 'Dark Web' ? 'dark' : 'info'}">${sourceType}</span>
                </td>
                <td>
                    <span class="badge bg-${sourceStatus === 'Active' ? 'success' : 'warning'}">${sourceStatus}</span>
                </td>
            </tr>
        `;
    });

    tableHTML += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = tableHTML;
}

function renderPagination(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    
    if (totalPages <= 1) return '';
    
    let paginationHTML = `
        <nav>
            <ul class="pagination justify-content-center">
                <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">Previous</a>
                </li>
    `;
    
    for (let i = 1; i <= totalPages; i++) {
        paginationHTML += `
            <li class="page-item ${currentPage === i ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    paginationHTML += `
                <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">Next</a>
                </li>
            </ul>
        </nav>
    `;
    
    return paginationHTML;
}

function changePage(newPage) {
    currentPage = newPage;
    renderDataTable(currentData);
}

function searchData() {
    const searchTerm = prompt('Enter search term:');
    if (searchTerm) {
        const filteredData = currentData.filter(post => 
            (post.title && post.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
            (post.summary && post.summary.toLowerCase().includes(searchTerm.toLowerCase())) ||
            (post.content && post.content.toLowerCase().includes(searchTerm.toLowerCase()))
        );
        
        renderDataTable(filteredData);
    }
}

function setupDataViewerControls() {
    // Add search functionality
    const searchInput = document.getElementById('data-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            if (searchTerm) {
                const filteredData = currentData.filter(post => 
                    (post.title && post.title.toLowerCase().includes(searchTerm)) ||
                    (post.summary && post.summary.toLowerCase().includes(searchTerm)) ||
                    (post.content && post.content.toLowerCase().includes(searchTerm))
                );
                renderDataTable(filteredData);
            } else {
                renderDataTable(currentData);
            }
        });
    }
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        `;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof initDataViewer === 'function') {
        initDataViewer();
    }
});