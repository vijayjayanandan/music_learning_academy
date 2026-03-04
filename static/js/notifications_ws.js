/**
 * WebSocket client for real-time notifications.
 * Connects to Django Channels NotificationConsumer.
 * Falls back to existing HTMX polling if WebSocket unavailable.
 */
(function () {
    "use strict";

    var academySlug = document.body.getAttribute("data-academy-slug");
    if (!academySlug) return;

    var MAX_RETRIES = 5;
    var BASE_DELAY = 2000; // 2 seconds
    var retryCount = 0;
    var ws = null;

    function getWsUrl() {
        var protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        return protocol + "//" + window.location.host + "/ws/notifications/" + academySlug + "/";
    }

    function showToast(message) {
        // Create a DaisyUI toast notification
        var container = document.getElementById("ws-toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "ws-toast-container";
            container.className = "toast toast-end toast-top z-[100]";
            container.style.top = "80px";
            document.body.appendChild(container);
        }

        var alert = document.createElement("div");
        alert.className = "alert alert-info shadow-lg";
        alert.innerHTML =
            '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">' +
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />' +
            "</svg>" +
            '<span>' + escapeHtml(message) + '</span>';
        container.appendChild(alert);

        // Auto-remove after 5 seconds
        setTimeout(function () {
            alert.style.opacity = "0";
            alert.style.transition = "opacity 0.3s";
            setTimeout(function () {
                alert.remove();
                if (container.children.length === 0) container.remove();
            }, 300);
        }, 5000);
    }

    function escapeHtml(text) {
        var div = document.createElement("div");
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    function refreshBadge() {
        // Trigger HTMX reload on the notification badge
        var badge = document.querySelector("[hx-get*='notification-badge']");
        if (badge && typeof htmx !== "undefined") {
            htmx.trigger(badge, "load");
        }
    }

    function connect() {
        if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
            return;
        }

        try {
            ws = new WebSocket(getWsUrl());
        } catch (e) {
            console.log("[WS] WebSocket not available, using HTMX polling fallback");
            return;
        }

        ws.onopen = function () {
            console.log("[WS] Connected to notification channel");
            retryCount = 0;
        };

        ws.onmessage = function (event) {
            try {
                var data = JSON.parse(event.data);
                var message = data.message || data.title || "New notification";
                showToast(message);
                refreshBadge();
            } catch (e) {
                console.warn("[WS] Failed to parse message:", e);
            }
        };

        ws.onclose = function (event) {
            ws = null;
            if (retryCount < MAX_RETRIES) {
                var delay = BASE_DELAY * Math.pow(2, retryCount);
                console.log("[WS] Disconnected. Reconnecting in " + (delay / 1000) + "s (attempt " + (retryCount + 1) + "/" + MAX_RETRIES + ")");
                retryCount++;
                setTimeout(connect, delay);
            } else {
                console.log("[WS] Max retries reached. Falling back to HTMX polling.");
            }
        };

        ws.onerror = function () {
            // onclose will fire after this, handling reconnection
        };
    }

    // Start connection
    connect();
})();
