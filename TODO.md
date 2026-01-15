# TODO List for OSINT Platform

## Current Task: Populate CVEs in User Dashboard using cve_manager.js functions

### Steps:
- [ ] Add `loadUserCVEs()` method to the `UserDashboard` class in `static/user_dashboard.js` that fetches from `/api/user/cves`, sets `currentCves` and `filteredCves`, updates statistics, and calls `renderCves()`.
- [ ] Update the `switchSection` method to call `loadUserCVEs()` when switching to 'cves' section.
- [ ] Update the refresh button event listener for CVEs to use `loadUserCVEs()`.
- [ ] Integrate CVE filter and search event listeners using functions from `cve_monitor.js` (e.g., `applyCveFilters()`).
- [ ] Remove conflicting table-based CVE rendering code: `loadCVEs()`, `updateCVEsUI()`, `viewCVE()`, `openAddCVEModal()`, `closeAddCVEModal()`, `handleAddCVE()`, `applyCVEFilters()` (the table version).
- [ ] Initialize CVE monitor for user dashboard by calling `initCveMonitor()` adapted for user context.
- [ ] Test CVE loading, rendering, filtering, and statistics in the user dashboard.

## Previous Tasks
*(Existing TODO items can be added here if needed)*
