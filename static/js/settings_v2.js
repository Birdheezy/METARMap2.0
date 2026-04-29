// settings_v2.js

// Global flag to prevent multiple simultaneous weather update calls
let isUpdatingWeather = false;
const logIntervals = {};

// Toast Notifications
function showToast(message, category) {
    const toast = document.createElement('div');
    toast.className = `toast ${category}`;
    toast.innerText = message;
    document.body.appendChild(toast);
    
    // Trigger reflow
    toast.offsetHeight;
    
    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => document.body.removeChild(toast), 500);
    }, 5000);
}

// Floating Save Button
function initializeFloatingSaveButton() {
    const btn = document.querySelector('.floating-save-btn');
    if (!btn) return;

    let formChanged = false;
    
    // Show button on any input change
    document.querySelector('form').addEventListener('input', () => {
        if (!formChanged) {
            formChanged = true;
            btn.classList.add('show');
        }
    });

    // Also catch change events (for checkboxes/selects)
    document.querySelector('form').addEventListener('change', () => {
        if (!formChanged) {
            formChanged = true;
            btn.classList.add('show');
        }
    });
}

// Legend Collapsing
function initializeLegendCollapsing() {
    const toggle = document.getElementById('legend');
    const section = document.querySelector('.legend-items-section');
    
    if (toggle && section) {
        toggle.addEventListener('change', function() {
            if (this.checked) {
                section.classList.remove('collapsed');
            } else {
                section.classList.add('collapsed');
            }
        });
    }
}

// Service Control
async function controlService(serviceName, action) {
    const statusDiv = document.getElementById(`${serviceName}-service-status`);
    if (statusDiv) {
        statusDiv.querySelector('.status-text').textContent = `${action}ing...`;
        statusDiv.querySelector('.dot').className = 'dot warning';
    }

    try {
        const response = await fetch(`/service/control/${serviceName}/${action}`, { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            showToast(`${serviceName} ${action} successful`, 'success');
            setTimeout(() => updateServiceStatus(serviceName), 2000);
        } else {
            showToast(`Error: ${data.error}`, 'danger');
            updateServiceStatus(serviceName);
        }
    } catch (error) {
        showToast(`Error: ${error.message}`, 'danger');
        updateServiceStatus(serviceName);
    }
}

// Update Service Status
async function updateServiceStatus(serviceName) {
    const statusDiv = document.getElementById(`${serviceName}-service-status`);
    if (!statusDiv) return;

    try {
        const response = await fetch(`/service/status/${serviceName}`);
        const data = await response.json();
        
        const dot = statusDiv.querySelector('.dot');
        const text = statusDiv.querySelector('.status-text');
        
        if (data.status === 'running') {
            dot.className = 'dot active';
            text.textContent = 'Running';
        } else {
            dot.className = 'dot inactive';
            text.textContent = 'Stopped';
        }
    } catch (error) {
        console.error(error);
    }
}

function updateAllServiceStatuses() {
    ['metar', 'settings', 'scheduler'].forEach(service => {
        updateServiceStatus(service);
    });
}

// System Control
function confirmRestart() {
    if (confirm("Are you sure you want to reboot the system?")) {
        fetch('/restart', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) showToast('System rebooting...', 'success');
                else showToast('Error rebooting', 'danger');
            })
            .catch(err => showToast('Error rebooting', 'danger'));
    }
}

function confirmShutdown() {
    if (confirm("WARNING: This will stop all services and shut down the controller. You will need to manually power cycle to restart.\n\nAre you sure?")) {
        fetch('/shutdown', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) showToast('System shutting down...', 'success');
                else showToast('Error shutting down', 'danger');
            })
            .catch(err => showToast('Error shutting down', 'danger'));
    }
}

function confirmSettingsStop() {
    if (confirm("Warning: Stopping the settings service will take this website offline. You will need to power cycle or SSH in to restart it.\n\nAre you sure?")) {
        controlService('settings', 'stop');
    }
}

async function startMetarWithCleanup() {
    // Stop the LED test service first (if we had one, but good practice to ensure clean state)
    // For now just start metar
    controlService('metar', 'start');
}

function updateWeatherManually() {
    if (isUpdatingWeather) return;
    isUpdatingWeather = true;
    
    const btn = document.getElementById('update-weather-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
    btn.disabled = true;

    fetch('/update-weather', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Weather updated successfully!', 'success');
                // Refresh the weather status immediately
                fetch('/weather-status')
                    .then(res => res.json())
                    .then(statusData => {
                        const statusDiv = document.getElementById('weather-status-display');
                        if (statusDiv && statusData.last_updated) {
                            statusDiv.textContent = `Last Updated: ${statusData.last_updated}`;
                            statusDiv.className = statusData.is_stale ? 'status-text stale' : 'status-text';
                        }
                    });
            } else {
                showToast(`Error: ${data.error}`, 'danger');
            }
        })
        .catch(error => {
            showToast(`Error: ${error.message}`, 'danger');
        })
        .finally(() => {
            isUpdatingWeather = false;
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

// Logs
function toggleLogs(serviceName) {
    const logsDiv = document.getElementById(`${serviceName}-service-logs`);
    const isVisible = logsDiv.style.display !== 'none';

    if (!isVisible) {
        if (logIntervals[serviceName]) clearInterval(logIntervals[serviceName]);
        
        fetchServiceLogs(serviceName);
        logsDiv.style.display = 'block';
        
        logIntervals[serviceName] = setInterval(() => {
            fetchServiceLogs(serviceName);
        }, 5000);
    } else {
        if (logIntervals[serviceName]) {
            clearInterval(logIntervals[serviceName]);
            delete logIntervals[serviceName];
        }
        logsDiv.style.display = 'none';
    }
}

function fetchServiceLogs(serviceName) {
    fetch(`/service/logs/${serviceName}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const logsContent = document.querySelector(`#${serviceName}-service-logs .logs-content`);
                if (logsContent) {
                    logsContent.textContent = data.logs || 'No logs available';
                }
            }
        })
        .catch(error => console.error('Error fetching logs:', error));
}

// Clean up intervals
window.addEventListener('beforeunload', () => {
    Object.values(logIntervals).forEach(interval => clearInterval(interval));
});

// Weather Status Auto-Update
function updateWeatherStatus() {
    fetch('/weather-status')
        .then(res => res.json())
        .then(statusData => {
            const statusDiv = document.getElementById('weather-status-display');
            if (statusDiv && statusData.last_updated) {
                statusDiv.textContent = `Last Updated: ${statusData.last_updated}`;
                statusDiv.className = statusData.is_stale ? 'status-text stale' : 'status-text';
            }
        })
        .catch(err => console.error("Error fetching weather status:", err));
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeFloatingSaveButton();
    initializeLegendCollapsing();
    updateAllServiceStatuses();
    
    // Initial weather status check and interval
    updateWeatherStatus();
    setInterval(updateWeatherStatus, 30000); // Update every 30 seconds
});
