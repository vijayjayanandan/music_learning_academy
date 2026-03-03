// HTMX configuration
document.body.addEventListener('htmx:configRequest', function(event) {
    // CSRF token is handled by hx-headers on body tag
});

// Show loading indicator for HTMX requests
document.body.addEventListener('htmx:beforeRequest', function(event) {
    const target = event.detail.target;
    if (target && !target.querySelector('.loading')) {
        // Don't add spinner to small inline elements
    }
});

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function() { alert.remove(); }, 500);
        }, 5000);
    });
});
