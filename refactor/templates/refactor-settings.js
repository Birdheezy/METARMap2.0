// Simple tooltip functionality for now
document.addEventListener('DOMContentLoaded', function() {
    const tooltipIcons = document.querySelectorAll('.tooltip-icon');
    
    tooltipIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            const content = this.nextElementSibling;
            if (content.style.display === 'none') {
                content.style.display = 'block';
            } else {
                content.style.display = 'none';
            }
        });
    });

    // Handle form submission
    const form = document.getElementById('settings-form');
    const saveBtn = document.getElementById('save-btn');
    const saveStatus = document.getElementById('save-status');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading state
        saveBtn.textContent = 'Saving...';
        saveBtn.disabled = true;
        saveStatus.style.display = 'block';
        saveStatus.innerHTML = '<span style="color: #ffc107;">Saving settings...</span>';
        
        // Get form data
        const formData = new FormData(form);
        
        // Send POST request
        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                saveStatus.innerHTML = '<span style="color: #28a745;">✓ ' + data.message + '</span>';
                // Reset button
                saveBtn.textContent = 'Save Settings';
                saveBtn.disabled = false;
                
                // Hide success message after 3 seconds
                setTimeout(() => {
                    saveStatus.style.display = 'none';
                }, 3000);
            } else {
                throw new Error(data.message);
            }
        })
        .catch(error => {
            saveStatus.innerHTML = '<span style="color: #dc3545;">✗ Error: ' + error.message + '</span>';
            saveBtn.textContent = 'Save Settings';
            saveBtn.disabled = false;
        });
    });
});
