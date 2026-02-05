document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('mobile-sidebar-toggle');
    var sidebar = document.getElementById('sidebar');
    if (!toggle || !sidebar) return;

    // create overlay
    var overlay = document.createElement('div');
    overlay.className = 'mobile-sidebar-overlay';
    document.body.appendChild(overlay);

    function openSidebar() {
        sidebar.classList.add('open');
        document.body.classList.add('sidebar-open');
        overlay.style.display = 'block';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        document.body.classList.remove('sidebar-open');
        overlay.style.display = 'none';
    }

    toggle.addEventListener('click', function (e) {
        e.preventDefault();
        if (sidebar.classList.contains('open')) closeSidebar(); else openSidebar();
    });

    overlay.addEventListener('click', function () { closeSidebar(); });

    window.addEventListener('resize', function () {
        if (window.innerWidth > 900) {
            closeSidebar();
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeSidebar();
    });
});
