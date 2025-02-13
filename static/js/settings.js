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
        let connectButton = document.getElementById('connect-button');

        if (!ssid) {
            connectionStatus.textContent = 'Please select a network.';
            return;
        }

        // Disable button and show connecting message
        connectButton.disabled = true;
        connectionStatus.textContent = 'Connecting to network... Please wait, this may take a few moments.';

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
                    connectionStatus.textContent = 'Connected successfully! Network connection established.';
                } else {
                    // Even if we get an error, the connection might still be successful
                    connectionStatus.textContent = 'Connection attempt completed. If your device is not connected, please try again.';
                }
            })
            .catch(error => {
                console.error('Error connecting to network:', error);
                connectionStatus.textContent = 'Connection attempt completed. Please check your network settings.';
            })
            .finally(() => {
                // Re-enable the button after attempt completes
                setTimeout(() => {
                    connectButton.disabled = false;
                }, 3000);  // Wait 3 seconds before re-enabling
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
            // First try to find dropdown content as next sibling of parent
            let tooltipContent = icon.parentElement.nextElementSibling;

            // If not found, try to find it within the same container
            if (!tooltipContent || !tooltipContent.classList.contains('dropdown-content')) {
                tooltipContent = icon.parentElement.querySelector('.dropdown-content');
            }

            // If still not found, look for it in the parent's parent
            if (!tooltipContent) {
                tooltipContent = icon.parentElement.parentElement.querySelector('.dropdown-content');
            }

            if (tooltipContent) {
                const isExpanded = icon.getAttribute('aria-expanded') === 'true';

                // Hide any other visible tooltips first
                document.querySelectorAll('.dropdown-content').forEach(content => {
                    if (content !== tooltipContent) {
                        content.style.display = 'none';
                        const otherIcon = content.parentElement.querySelector('.tooltip-icon');
                        if (otherIcon) {
                            otherIcon.setAttribute('aria-expanded', 'false');
                        }
                    }
                });

                if (isExpanded) {
                    tooltipContent.style.display = 'none';
                    icon.setAttribute('aria-expanded', 'false');
                } else {
                    tooltipContent.style.display = 'block';
                    icon.setAttribute('aria-expanded', 'true');
                }
            }
        }
    });


// Attach saveScrollPosition to buttons that trigger navigation or page reload
document.querySelectorAll('a.btn-primary').forEach(button => {
    button.addEventListener('click', saveScrollPosition);
});

document.addEventListener("DOMContentLoaded", () => {
    console.log("settings.js is running");

    // Only try to set up the restart button if it exists
    const restartButton = document.getElementById("restart-settings-button");
    if (restartButton) {
        restartButton.addEventListener("click", (event) => {
            event.preventDefault();
            console.log("Restart Settings button clicked");

            // Disable the button to prevent double-clicks
            restartButton.disabled = true;
            console.log("Restart Settings button disabled.");

            const statusDiv = document.getElementById("restart-settings-status");

            // Update the status message if the div exists
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
    }
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

// Function to format date as MM-DD-YYYY HH:MM:SS
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${month}-${day}-${year} ${hours}:${minutes}:${seconds}`;
}

// Function to update weather status
function updateWeatherStatus() {
    fetch('/weather-status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const statusContainer = document.querySelector('.weather-status .service-status');
                const statusDot = statusContainer.querySelector('.status-dot');
                const statusText = statusContainer.querySelector('.status-text');

                const lastUpdated = new Date(data.last_updated);
                const now = new Date();
                const minutesSinceUpdate = Math.floor((now - lastUpdated) / (1000 * 60));

                // Get the update interval from the input field (in minutes)
                const updateIntervalInput = document.querySelector('input[name="weather_update_interval"]');
                const expectedInterval = updateIntervalInput ? parseInt(updateIntervalInput.value) : 5;

                // Update status dot and text - turn red after 2x the expected interval
                if (minutesSinceUpdate > (expectedInterval * 2)) {
                    statusDot.classList.add('stale');
                } else {
                    statusDot.classList.remove('stale');
                }

                statusText.textContent = `WX Last Updated: ${formatDate(data.last_updated)}`;
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

// Function to populate timezone dropdown
function populateTimezones() {
    const select = document.getElementById('timezone-select');
    const status = document.getElementById('timezone-status');

    fetch('/get_timezones')
        .then(response => response.json())
        .then(data => {
            if (data.timezones) {
                select.innerHTML = ''; // Clear loading option
                data.timezones.forEach(tz => {
                    const option = document.createElement('option');
                    option.value = tz;
                    option.textContent = tz;
                    if (tz === data.current) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading timezones:', error);
            status.textContent = 'Error loading timezones';
        });
}

// Function to update timezone
function updateTimezone(timezone) {
    const status = document.getElementById('timezone-status');
    status.textContent = 'Updating timezone...';

    fetch('/set_timezone', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ timezone: timezone })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            status.textContent = data.message;
            showToast('Timezone updated successfully', 'success');
        } else {
            status.textContent = data.error || 'Failed to update timezone';
            showToast('Failed to update timezone', 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating timezone:', error);
        status.textContent = 'Error updating timezone';
        showToast('Error updating timezone', 'danger');
    });
}

// Add event listeners when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Existing event listeners...

    // Populate timezone dropdown
    populateTimezones();

    // Add change event listener for timezone select
    const timezoneSelect = document.getElementById('timezone-select');
    if (timezoneSelect) {
        timezoneSelect.addEventListener('change', (event) => {
            if (event.target.value) {
                if (confirm('Are you sure you want to change the timezone? This will restart the scheduler service.')) {
                    updateTimezone(event.target.value);
                } else {
                    // Reset to previous selection
                    populateTimezones();
                }
            }
        });
    }
});

function confirmSettingsStop() {
    if (confirm("Warning: Stopping the settings service will take this settings website offline.\n\nYou will need to power cycle your METARMap to restore access to the settings website.\n\nAre you sure you want to stop the settings service?")) {
        controlService('settings', 'stop');
    }
}

// Function to check for updates
async function checkForUpdates() {
    const updateStatus = document.getElementById('update-status');
    const updateButtonContainer = document.getElementById('update-button-container');

    try {
        updateStatus.textContent = 'Checking for updates...';
        updateButtonContainer.innerHTML = '';

        const response = await fetch('/check_for_updates');
        const data = await response.json();

        if (data.error) {
            updateStatus.textContent = `Error checking for updates: ${data.error}`;
            return;
        }

        if (data.has_updates) {
            let statusHtml = `
                <div>Updates available on ${data.branch} branch (${data.commits_behind} commits behind)</div>
                <div style="margin-top: 10px;">The following files will be updated:</div>
                <ul style="list-style-type: none; padding-left: 0;">
            `;

            data.files.forEach(file => {
                statusHtml += `<li>${file}</li>`;
            });

            statusHtml += `</ul>
                <div style="margin-top: 10px; font-style: italic;">
                    Note: Your local configuration files will be preserved during the update.
                </div>`;

            updateStatus.innerHTML = statusHtml;

            // Add the Update Now button
            const updateNowButton = document.createElement('button');
            updateNowButton.textContent = 'Update Now';
            updateNowButton.className = 'btn btn-primary';
            updateNowButton.onclick = function() {
                if (confirm('Are you sure you want to apply these updates? A backup will be created before updating.')) {
                    applyUpdate();
                }
            };
            updateButtonContainer.appendChild(updateNowButton);
        } else {
            updateStatus.textContent = data.message;
        }
    } catch (error) {
        updateStatus.textContent = 'Error checking for updates: ' + error;
    }
}

// Function to apply update
async function applyUpdate() {
    const updateStatus = document.getElementById('update-status');
    const updateButtonContainer = document.getElementById('update-button-container');

    try {
        updateStatus.textContent = 'Applying update... Please wait.';
        updateButtonContainer.innerHTML = '';

        const response = await fetch('/apply_update', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            updateStatus.innerHTML = `
                <div style="color: green;">
                    ${data.message}<br>
                    The page will refresh in 5 seconds...
                </div>
            `;
            setTimeout(() => {
                window.location.reload();
            }, 5000);
        } else {
            updateStatus.innerHTML = `
                <div style="color: red;">
                    Error applying update: ${data.error}<br>
                    Your local files have been preserved.
                </div>
            `;
        }
    } catch (error) {
        updateStatus.innerHTML = `
            <div style="color: red;">
                Error applying update: ${error}<br>
                Your local files have been preserved.
            </div>
        `;
    }
}
