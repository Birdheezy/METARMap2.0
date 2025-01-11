console.log('settings.js loaded');
// Save scroll position on form submission
function saveScrollPosition() {
    sessionStorage.setItem('scrollPosition', window.scrollY);
}

    // Restore scroll position on page reload
    document.addEventListener('DOMContentLoaded', function () {
        const scrollPosition = sessionStorage.getItem('scrollPosition');
        if (scrollPosition) {
            window.scrollTo(0, parseInt(scrollPosition));
            sessionStorage.removeItem('scrollPosition');
        }
    });

    // Scan for networks when the "Scan" button is clicked
    document.getElementById('scan-button').addEventListener('click', function () {
        let scanButton = document.getElementById('scan-button');
        let ssidSelect = document.getElementById('ssid-select');
        let connectionStatus = document.getElementById('connection-status');

        // Disable the button and show a loading message
        scanButton.disabled = true;
        connectionStatus.textContent = 'Scanning for networks...';

        fetch('/scan-networks')
            .then(response => response.json())
            .then(data => {
                ssidSelect.innerHTML = '<option value="">Select a network</option>';

                if (data.networks && data.networks.length > 0) {
                    data.networks.forEach(network => {
                        let option = document.createElement('option');
                        option.value = network.ssid;
                        option.textContent = `${network.ssid} (Signal: ${network.signal}%)`;
                        ssidSelect.appendChild(option);
                    });
                    connectionStatus.textContent = 'Scan complete. Select a network.';
                } else {
                    connectionStatus.textContent = 'No networks found. Try scanning again.';
                }
            })
            .catch(error => {
                console.error('Error scanning networks:', error);
                connectionStatus.textContent = 'An error occurred while scanning.';
            })
            .finally(() => {
                // Re-enable the button after the scan completes
                scanButton.disabled = false;
            });
    });

    // Connect to the selected network when "Connect" is clicked
    document.getElementById('connect-button').addEventListener('click', function () {
        let ssid = document.getElementById('ssid-select').value;
        let password = document.getElementById('wifi-password').value;
        let connectionStatus = document.getElementById('connection-status');

        if (!ssid) {
            connectionStatus.textContent = 'Please select a network.';
            return;
        }

        fetch('/connect-to-network', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ssid: ssid, password: password })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    connectionStatus.textContent = 'Connected successfully!';
                } else {
                    connectionStatus.textContent = `Error: ${data.error}`;
                }
            })
            .catch(error => {
                console.error('Error connecting to network:', error);
                connectionStatus.textContent = 'An error occurred while connecting.';
            });
    });

    document.addEventListener('DOMContentLoaded', function() {
        const textarea = document.getElementById('airportsText');
        const lineNumbers = document.getElementById('line-numbers');

        function updateLineNumbers() {
            const lines = textarea.value.split('\n').length;
            let lineNumbersHtml = '';
            for (let i = 1; i <= lines; i++) {
                lineNumbersHtml += `${i}<br>`;
            }
            lineNumbers.innerHTML = lineNumbersHtml;
        }

        // Sync scrolling between the textarea and the line numbers
        textarea.addEventListener('scroll', function () {
            lineNumbers.style.transform = `translateY(-${textarea.scrollTop}px)`;
        });

        // Update line numbers on input
        textarea.addEventListener('input', updateLineNumbers);

        // Initial update on page load
        updateLineNumbers();
    });

function saveScrollPosition() {
    sessionStorage.setItem('scrollPosition', window.scrollY);
}

function saveAndRestart() {
  // Trigger the form submission first
  document.forms[0].submit();

  // After a slight delay, make a request to restart the metar service
  setTimeout(() => {
    fetch('/restart_metar')
      .then(response => {
        if (response.ok) {
          return response.json();
        }
        throw new Error('Failed to restart METAR service');
      })
      .then(data => {
        if (data.success) {
          alert('Settings saved and METAR service restarted successfully!');
        } else {
          console.error('Settings saved but failed to restart METAR service.');
        }
      })
      .catch(error => {
        console.error('Error restarting METAR service:', error);
      });
  }, 500); // Delay to allow settings to save
}


// Restore the scroll position after the page reloads
document.addEventListener('DOMContentLoaded', function() {
    const scrollPosition = sessionStorage.getItem('scrollPosition');
    if (scrollPosition) {
        window.scrollTo(0, parseInt(scrollPosition));
        sessionStorage.removeItem('scrollPosition');
    }
});

// JavaScript for toast notifications
function showToast(message, category) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerText = message;
    toast.classList.add(category);
    document.body.appendChild(toast);
    setTimeout(function() {
        toast.classList.add('show');
    }, 100);
    setTimeout(function() {
        toast.classList.remove('show');
        document.body.removeChild(toast);
    }, 8000);
}

document.addEventListener('DOMContentLoaded', function() {
    if (typeof messages !== 'undefined' && messages.length > 0) {
        messages.forEach(function(msg) {
            showToast(msg.message, msg.category);
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
        // Add click and keypress event listener to tooltip icons
        const tooltipIcons = document.querySelectorAll('.tooltip-icon');

        tooltipIcons.forEach(icon => {
            icon.addEventListener('click', function() {
                toggleTooltip(this);
            });

            icon.addEventListener('keypress', function(event) {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    toggleTooltip(this);
                }
            });
        });

        function toggleTooltip(icon) {
            const tooltipContent = icon.parentElement.nextElementSibling;
            const isExpanded = icon.getAttribute('aria-expanded') === 'true';

            if (isExpanded) {
                tooltipContent.style.display = 'none';
                icon.setAttribute('aria-expanded', 'false');
            } else {
                tooltipContent.style.display = 'block';
                icon.setAttribute('aria-expanded', 'true');
            }
        }
    });


// Attach saveScrollPosition to buttons that trigger navigation or page reload
document.querySelectorAll('a.btn-primary').forEach(button => {
    button.addEventListener('click', saveScrollPosition);
});

document.addEventListener("DOMContentLoaded", () => {
    console.log("settings.js is running");

    const restartButton = document.getElementById("restart-settings-button");
    const statusDiv = document.getElementById("restart-settings-status");

    if (!restartButton) {
        console.error("Restart Settings button not found!");
        return;
    }

    restartButton.addEventListener("click", (event) => {
        event.preventDefault();
        console.log("Restart Settings button clicked");

        // Disable the button to prevent double-clicks
        restartButton.disabled = true;
        console.log("Restart Settings button disabled.");

        // Update the status message
        if (statusDiv) {
            statusDiv.textContent = "Restarting Settings Service...";
            console.log("Status updated to 'Restarting Settings Service...'");
        }

        // Send a request to restart the service
        fetch('/restart_settings')
            .then((response) => {
                if (response.ok) {
                    console.log("Settings service restarting...");

                    if (statusDiv) {
                        // Start a countdown before showing the refresh button
                        let countdown = 3; // Seconds
                        const countdownInterval = setInterval(() => {
                            statusDiv.textContent = `Please wait ${countdown} seconds before refreshing...`;
                            console.log(`Countdown: ${countdown}`);
                            countdown--;

                            if (countdown < 0) {
                                clearInterval(countdownInterval);

                                // Clear the status message
                                statusDiv.textContent = "";

                                // Add the "Refresh Page" button
                                const refreshButton = document.createElement("button");
                                refreshButton.textContent = "Refresh Page";
                                refreshButton.classList.add("btn", "btn-secondary", "mt-3");
                                refreshButton.addEventListener("click", () => {
                                    console.log("Refreshing the page...");
                                    location.reload();
                                });

                                // Append the button
                                statusDiv.appendChild(refreshButton);
                                console.log("Refresh button added.");
                            }
                        }, 1000); // 1 second interval
                    }
                } else {
                    console.error("Failed to restart settings service.");
                    if (statusDiv) {
                        statusDiv.textContent = "Failed to restart settings service.";
                    }
                }
            })
            .catch((error) => {
                console.error("Error restarting settings service:", error);
                if (statusDiv) {
                    statusDiv.textContent = "An error occurred while restarting the service.";
                }
            })
            .finally(() => {
                // Re-enable the restart button after 10 seconds
                setTimeout(() => {
                    restartButton.disabled = false;
                    console.log("Restart Settings button re-enabled.");
                }, 10000); // Adjust the delay as needed
            });
    });
});

document.getElementById('check-updates-button').addEventListener('click', function (event) {
    // Prevent the form from submitting and refreshing the page
    event.preventDefault();

    let updateStatus = document.getElementById('update-status');
    let updateButtonContainer = document.getElementById('update-button-container');

    updateStatus.textContent = 'Checking for updates...';

    fetch('/check_for_updates')
        .then(response => response.json())
        .then(data => {
            updateButtonContainer.innerHTML = ''; // Clear any existing button
            if (data.updates_available) {
                updateStatus.textContent = data.message;

                // Create the "Update Now" button
                let updateButton = document.createElement('button');
                updateButton.textContent = 'Update Now';
                updateButton.classList.add('btn', 'btn-secondary');
                updateButton.addEventListener('click', function (event) {
                    // Prevent page refresh on button click
                    event.preventDefault();

                    // Update status to "Updating..."
                    updateStatus.textContent = 'Updating...';

                    // Fetch the update endpoint to pull the latest updates
                    fetch('/apply_updates', { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            if (data.message) {
                                updateStatus.textContent = data.message;
                            } else if (data.error) {
                                updateStatus.textContent = 'Update failed: ' + data.error;
                            }
                        })
                        .catch(error => {
                            console.error('Error during update:', error);
                            updateStatus.textContent = 'An error occurred while updating.';
                        });

                });

                // Append the button to the container
                updateButtonContainer.appendChild(updateButton);
            } else if (data.message) {
                updateStatus.textContent = data.message;
            } else if (data.error) {
                updateStatus.textContent = 'Error: ' + data.error;
            }
        })
        .catch(error => {
            console.error('Error checking for updates:', error);
            updateStatus.textContent = 'An error occurred while checking for updates.';
        });
});

// Function to control services
async function controlService(serviceName, action) {
    try {
        const response = await fetch(`/service/control/${serviceName}/${action}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (response.ok) {
            if (data.special_case === "settings_restart") {
                showToast("Settings service is restarting... Please wait for the page to reload.", 'success');
                // Wait a few seconds then reload the page
                setTimeout(() => {
                    window.location.reload();
                }, 5000);
            } else {
                showToast(`${serviceName.toUpperCase()} service ${action} successful`, 'success');
                // Update status after a brief delay to allow service to change state
                setTimeout(() => updateServiceStatus(serviceName), 1000);
            }
        } else {
            showToast(`Failed to ${action} ${serviceName} service: ${data.error}`, 'danger');
        }
    } catch (error) {
        if (serviceName === 'settings' && action === 'restart') {
            showToast("Settings service is restarting... Please wait for the page to reload.", 'success');
            // Wait a few seconds then reload the page
            setTimeout(() => {
                window.location.reload();
            }, 5000);
        } else {
            showToast(`Error controlling service: ${error}`, 'danger');
        }
    }
}

// Function to update service status
async function updateServiceStatus(serviceName) {
    try {
        const response = await fetch(`/service/status/${serviceName}`);
        const data = await response.json();
        
        const statusElement = document.getElementById(`${serviceName}-service-status`);
        const dotElement = statusElement.querySelector('.status-dot');
        const textElement = statusElement.querySelector('.status-text');
        
        // Update status dot and text
        dotElement.className = `status-dot ${data.status}`;
        textElement.textContent = data.message;
        
    } catch (error) {
        console.error(`Error updating ${serviceName} status:`, error);
    }
}

// Function to update weather status
function updateWeatherStatus() {
    console.log('Fetching weather status...');
    fetch('/weather-status')
        .then(response => response.json())
        .then(data => {
            console.log('Weather status response:', data);
            if (data.success) {
                const weatherStatusSpan = document.querySelector('span[style*="color: grey"]');
                console.log('Found weather status span:', weatherStatusSpan);
                if (weatherStatusSpan) {
                    weatherStatusSpan.textContent = 'WX Last Updated: ' + data.last_updated;
                    console.log('Updated weather status text to:', data.last_updated);
                } else {
                    console.log('Weather status span not found');
                }
            }
        })
        .catch(error => console.error('Error updating weather status:', error));
}

// Function to update all service statuses
function updateAllServiceStatuses() {
    ['metar', 'settings', 'scheduler'].forEach(service => {
        updateServiceStatus(service);
    });
    updateWeatherStatus();  // Add weather status update
}

// Update statuses on page load and periodically
document.addEventListener('DOMContentLoaded', () => {
    updateAllServiceStatuses();
    // Update every 10 seconds
    setInterval(updateAllServiceStatuses, 10000);
});

// Add this at the top with other global variables
const logIntervals = {};

function toggleLogs(serviceName) {
    const logsDiv = document.getElementById(`${serviceName}-service-logs`);
    const isVisible = logsDiv.style.display !== 'none';

    if (!isVisible) {
        // Clear any existing interval first
        if (logIntervals[serviceName]) {
            clearInterval(logIntervals[serviceName]);
        }
        
        // Initial fetch
        fetchServiceLogs(serviceName);
        logsDiv.style.display = 'block';
        
        // Start new interval
        logIntervals[serviceName] = setInterval(() => {
            fetchServiceLogs(serviceName);
        }, 5000);
    } else {
        // Clear interval when hiding logs
        if (logIntervals[serviceName]) {
            clearInterval(logIntervals[serviceName]);
            delete logIntervals[serviceName];
        }
        logsDiv.style.display = 'none';
    }
}

// Clean up intervals when leaving the page
window.addEventListener('beforeunload', () => {
    Object.values(logIntervals).forEach(interval => clearInterval(interval));
});

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
