// Main JavaScript file for Wingman Flight Logbook

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any JavaScript functionality here
    
    // Add confirmation for delete buttons
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });
    
    // Add tooltips to elements with data-toggle="tooltip"
    const tooltipElements = document.querySelectorAll('[data-toggle="tooltip"]');
    tooltipElements.forEach(element => {
        element.setAttribute('title', element.getAttribute('data-original-title') || element.textContent);
    });
});
