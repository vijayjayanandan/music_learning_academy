/**
 * Delete confirmation dialog handler.
 * Usage: Add data-confirm="Are you sure?" to any form or button.
 */
(function () {
    var dialog = document.getElementById('confirm-dialog');
    if (!dialog) return;

    var messageEl = document.getElementById('confirm-dialog-message');
    var okBtn = document.getElementById('confirm-dialog-ok');
    var cancelBtn = document.getElementById('confirm-dialog-cancel');
    var pendingForm = null;

    document.addEventListener('submit', function (e) {
        var form = e.target;
        var confirmMsg = form.getAttribute('data-confirm');
        if (!confirmMsg) return;

        e.preventDefault();
        pendingForm = form;
        messageEl.textContent = confirmMsg;
        dialog.showModal();
    });

    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-confirm]');
        if (!btn || btn.tagName === 'FORM') return;
        if (btn.type === 'submit' && btn.form) {
            // Will be handled by form submit listener
            return;
        }
    });

    okBtn.addEventListener('click', function () {
        dialog.close();
        if (pendingForm) {
            pendingForm.removeAttribute('data-confirm');
            pendingForm.requestSubmit();
            pendingForm = null;
        }
    });

    cancelBtn.addEventListener('click', function () {
        dialog.close();
        pendingForm = null;
    });
})();
