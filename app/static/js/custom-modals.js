function showCustomConfirmation(options) {
    const {
        title = 'Confirm Action',
        message = 'Are you sure?',
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        confirmClass = 'btn-primary',
        onConfirm = null,
        onCancel = null
    } = options;

    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="customConfirmModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${cancelText}</button>
                        <button type="button" class="btn ${confirmClass}" id="customConfirmBtn">${confirmText}</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('customConfirmModal');
    if (existingModal) existingModal.remove();

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('customConfirmModal'));
    modal.show();

    // Handle confirm click
    document.getElementById('customConfirmBtn').onclick = function() {
        modal.hide();
        if (onConfirm) onConfirm();
    };

    // Handle cancel (modal close)
    document.getElementById('customConfirmModal').addEventListener('hidden.bs.modal', function() {
        if (onCancel) onCancel();
        this.remove();
    });
}