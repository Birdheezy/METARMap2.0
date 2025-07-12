// Save scroll position on form submission
// Global flag to prevent multiple simultaneous weather update calls
let isUpdatingWeather = false;
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

function saveScrollPosition() {
    sessionStorage.setItem('scrollPosition', window.scrollY);
}

function saveSettings() {
  // Just submit the form without restarting METAR service
  document.forms[0].submit();
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

// Attach saveScrollPosition to buttons that trigger navigation or page reload
document.querySelectorAll('a.btn-primary').forEach(button => {
    button.addEventListener('click', saveScrollPosition);
});

document.addEventListener("DOMContentLoaded", () => {
    // Only try to set up the restart button if it exists
    const restartButton = document.getElementById("restart-settings-button");
    if (restartButton) {
        restartButton.addEventListener("click", (event) => {
            event.preventDefault();

            // Disable the button to prevent double-clicks
            restartButton.disabled = true;

            const statusDiv = document.getElementById("restart-settings-status");

            // Update the status message if the div exists
            if (statusDiv) {
                statusDiv.textContent = "Restarting Settings Service...";
            }

            // Send a request to restart the service
            fetch('/restart_settings')
                .then((response) => {
                    if (response.ok) {
                        if (statusDiv) {
                            // Start a countdown before showing the refresh button
                            let countdown = 3; // Seconds
                            const countdownInterval = setInterval(() => {
                                statusDiv.textContent = `Please wait ${countdown} seconds before refreshing...`;
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
                                        location.reload();
                                    });

                                    // Append the button
                                    statusDiv.appendChild(refreshButton);
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
    // Prevent multiple simultaneous calls
    if (isUpdatingWeather) {
        return;
    }
    isUpdatingWeather = true;
    fetch('/weather-status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update all instances of the timestamp text
                const lastUpdatedElements = document.querySelectorAll('#map-weather-last-updated, #update-weather-last-updated');
                const statusDots = document.querySelectorAll('#map-weather-status-dot, #update-weather-status-dot');
                
                // Use the formatted_date if available, otherwise use last_updated
                const displayDate = data.formatted_date || data.last_updated;
                
                lastUpdatedElements.forEach(el => {
                    el.textContent = displayDate;
                });
                
                try {
                    const lastUpdated = data.last_updated;
                    
                    if (lastUpdated && lastUpdated !== "Weather data not available") {
                        let updateTime;
                        try {
                            const parts = lastUpdated.split(' ');
                            if (parts.length !== 2) throw new Error('Invalid date format');
                            
                            const dateParts = parts[0].split('-');
                            const timeParts = parts[1].split(':');
                            
                            if (dateParts.length !== 3 || timeParts.length !== 3) {
                                throw new Error('Invalid date/time parts');
                            }
                            
                            // Check if the date is in YYYY-MM-DD format (from API) or MM-DD-YYYY format (from UI)
                            let year, month, day;
                            if (dateParts[0].length === 4) {
                                // YYYY-MM-DD format
                                year = parseInt(dateParts[0]);
                                month = parseInt(dateParts[1]) - 1; // 0-indexed month
                                day = parseInt(dateParts[2]);
                            } else {
                                // MM-DD-YYYY format
                                year = parseInt(dateParts[2]);
                                month = parseInt(dateParts[0]) - 1; // 0-indexed month
                                day = parseInt(dateParts[1]);
                            }
                            
                            // Validate parsed values
                            if (isNaN(year) || isNaN(month) || isNaN(day)) {
                                throw new Error('Invalid date numbers');
                            }
                            
                            const hour = parseInt(timeParts[0]);
                            const minute = parseInt(timeParts[1]);
                            const second = parseInt(timeParts[2]);
                            
                            if (isNaN(hour) || isNaN(minute) || isNaN(second)) {
                                throw new Error('Invalid time numbers');
                            }
                            
                            updateTime = new Date(year, month, day, hour, minute, second);
                            
                            if (isNaN(updateTime.getTime())) {
                                throw new Error('Invalid date object');
                            }
                        } catch (dateError) {
                            console.error('Error parsing date:', dateError);
                            throw new Error('Failed to parse date: ' + dateError.message);
                        }
                        
                        const now = new Date();
                        const diffMinutes = (now - updateTime) / (1000 * 60);
                        
                        // Use a default threshold if WEATHER_UPDATE_THRESHOLD is not defined
                        const staleThreshold = typeof WEATHER_UPDATE_THRESHOLD !== 'undefined' ? WEATHER_UPDATE_THRESHOLD : 10;
                        
                        // Update all status dots
                        statusDots.forEach(dot => {
                            dot.style.backgroundColor = diffMinutes < staleThreshold ? 'green' : 'red';
                        });
                    } else {
                        // If weather data is not available or invalid, set dots to red
                        statusDots.forEach(dot => {
                            dot.style.backgroundColor = 'red';
                        });
                    }
                } catch (e) {
                    console.error("Error processing weather status:", e);
                    // Set dots to red on error
                    statusDots.forEach(dot => {
                        dot.style.backgroundColor = 'red';
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error fetching weather status:', error);
            // Set dots to red on error
            const statusDots = document.querySelectorAll('#map-weather-status-dot, #update-weather-status-dot');
            statusDots.forEach(dot => {
                dot.style.backgroundColor = 'red';
            });
        })
        .finally(() => {
            isUpdatingWeather = false;
        });
}

// Function to update all service statuses
function updateAllServiceStatuses() {
    ['metar', 'settings', 'scheduler'].forEach(service => {
        updateServiceStatus(service);
    });
}

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

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize map if the element exists
    const mapElement = document.getElementById('airport-map');
    if (mapElement) {
        // Initialize the map system with color configuration
        const colorConfig = {
            vfrColor: VFR_COLOR,
            mvfrColor: MVFR_COLOR,
            ifrColor: IFR_COLOR,
            lifrColor: LIFR_COLOR,
            missingColor: MISSING_COLOR,
            lighteningColor: LIGHTENING_COLOR,
            snowyColor: SNOWY_COLOR,
            weatherUpdateThreshold: WEATHER_UPDATE_THRESHOLD
        };
        
        initializeMapSystem(colorConfig);
    }
});

// Function to get marker color based on flight category
function getMarkerColor(fltCat) {
    // Handle null/undefined flight category
    if (!fltCat) {
        return MISSING_COLOR;
    }
    
    // Convert to uppercase for consistency with backend
    const category = fltCat.toUpperCase();
    
    switch (category) {
        case 'VFR':
            return VFR_COLOR;
        case 'MVFR':
            return MVFR_COLOR;
        case 'IFR':
            return IFR_COLOR;
        case 'LIFR':
            return LIFR_COLOR;
        case 'MISSING':
        default:
            return MISSING_COLOR;
    }
}

// LED Testing functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle LED mode selection
    const ledModeRadios = document.querySelectorAll('input[name="led-mode"]');
    const ledRangeInputs = document.getElementById('led-range-inputs');

    ledModeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            ledRangeInputs.style.display = this.value === 'range' ? 'block' : 'none';
        });
    });

    // Function to get current LED range based on mode
    function getLedRange() {
        const mode = document.querySelector('input[name="led-mode"]:checked').value;
        if (mode === 'all') {
            return { startPixel: null, endPixel: null };
        } else {
            const startPixel = document.getElementById('start-pixel').value;
            const endPixel = document.getElementById('end-pixel').value;
            
            // Convert from 1-based (user) to 0-based (system) indexing
            return {
                startPixel: startPixel ? Math.max(0, parseInt(startPixel) - 1) : null,
                endPixel: endPixel ? Math.max(0, parseInt(endPixel) - 1) : null
            };
        }
    }

    // Handle preset color buttons
    document.querySelectorAll('.led-test-btn').forEach(button => {
        button.addEventListener('click', function() {
            const color = this.dataset.color;
            const { startPixel, endPixel } = getLedRange();
            testLEDs(color, startPixel, endPixel);
        });
    });

    // Handle custom color test
    document.getElementById('test-custom-color')?.addEventListener('click', function() {
        const color = document.getElementById('custom-led-color').value;
        const { startPixel, endPixel } = getLedRange();
        testLEDs(color, startPixel, endPixel);
    });

    // Handle turn off button
    document.getElementById('turn-off-leds')?.addEventListener('click', function() {
        // Create a promise for stopping the service
        const stopServicePromise = fetch('/led-test-service/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.warn('Failed to stop LED test service:', data.error);
            }
        })
        .catch(error => {
            console.error('Error stopping LED test service:', error);
        });

        // Create a promise for turning off LEDs
        const turnOffLedsPromise = fetch('/turn-off-leds', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                showToast('Failed to turn off LEDs: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            showToast('Error turning off LEDs: ' + error, 'danger');
        });

        // Execute both promises in parallel
        Promise.all([stopServicePromise, turnOffLedsPromise])
            .then(() => {
                showToast('LEDs turned off', 'success');
            })
            .catch(error => {
                console.error('Error during LED turn off:', error);
            });
    });

    // Handle automated test
    let currentIndex = -1;
    const runAutoTest = document.getElementById('run-auto-test');
    const stopAutoTest = document.getElementById('stop-auto-test');
    const metarControlBtn = document.getElementById('metar-control-btn');
    const testStatus = document.getElementById('test-status');
    let isTestRunning = false;

    const colors = [
        { name: 'Red', color: '#ff0000' },
        { name: 'Green', color: '#00ff00' },
        { name: 'Blue', color: '#0000ff' },
        { name: 'White', color: '#ffffff' },
        { name: 'VFR', color: document.querySelector('[data-color="' + VFR_COLOR + '"]').dataset.color },
        { name: 'MVFR', color: document.querySelector('[data-color="' + MVFR_COLOR + '"]').dataset.color },
        { name: 'IFR', color: document.querySelector('[data-color="' + IFR_COLOR + '"]').dataset.color },
        { name: 'LIFR', color: document.querySelector('[data-color="' + LIFR_COLOR + '"]').dataset.color },
        { name: 'Lightning', color: document.querySelector('[data-color="' + LIGHTENING_COLOR + '"]').dataset.color },
        { name: 'Snow', color: document.querySelector('[data-color="' + SNOWY_COLOR + '"]').dataset.color }
    ];

    if (runAutoTest && stopAutoTest && metarControlBtn) {
        runAutoTest.addEventListener('click', function() {
            if (!isTestRunning) {
                // First check if METAR service is running and stop it if needed
                fetch('/service/status/metar')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'running') {
                            // Stop METAR service first
                            return fetch('/service/control/metar/stop', {
                                method: 'POST',
                            }).then(() => {
                                showToast('METAR service stopped', 'info');
                            });
                        }
                    })
                    .then(() => {
                        // Start the LED test service
                        return fetch('/led-test-service/start', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        });
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            currentIndex = -1; // Reset to start
                            isTestRunning = true;
                            // Update button states
                            runAutoTest.textContent = 'Next Color';
                            stopAutoTest.style.visibility = 'visible';
                            metarControlBtn.style.visibility = 'hidden';
                            showNextColor();
                        } else {
                            showToast('Failed to start LED test service: ' + data.error, 'danger');
                        }
                    })
                    .catch(error => {
                        showToast('Error starting LED test service: ' + error, 'danger');
                    });
            } else {
                // Just show next color if test is already running
                showNextColor();
            }
        });

        stopAutoTest.addEventListener('click', stopTest);
        
        function stopTest() {
            // Reset UI state immediately
            isTestRunning = false;
            runAutoTest.textContent = 'Start Test';
            stopAutoTest.style.visibility = 'hidden';
            metarControlBtn.style.visibility = 'visible';
            metarControlBtn.textContent = 'Stop METAR';
            metarControlBtn.onclick = (event) => {
                event.preventDefault();
                controlService('metar', 'stop');
            };
            currentIndex = -1;
            testStatus.textContent = 'Testing: Not Started';

            // Create a promise for stopping the service
            const stopServicePromise = fetch('/led-test-service/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    console.warn('Failed to stop LED test service:', data.error);
                }
            })
            .catch(error => {
                console.error('Error stopping LED test service:', error);
            });

            // Create a promise for turning off LEDs
            const turnOffLedsPromise = fetch('/turn-off-leds', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    showToast('Failed to turn off LEDs: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                showToast('Error turning off LEDs: ' + error, 'danger');
            });

            // Execute both promises in parallel
            Promise.all([stopServicePromise, turnOffLedsPromise])
                .then(() => {
                    showToast('Test stopped', 'success');
                })
                .catch(error => {
                    console.error('Error during test stop:', error);
                });
        }

        function showNextColor() {
            currentIndex++;
            if (currentIndex >= colors.length) {
                currentIndex = 0;
            }

            const currentColor = colors[currentIndex];
            const { startPixel, endPixel } = getLedRange();
            testLEDs(currentColor.color, startPixel, endPixel);
            testStatus.textContent = `Testing: ${currentColor.name}`;
        }
    }
});

function convertColor(color, colorOrder) {
    // Convert hex color to RGB components
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);

    // Return color components in the specified order
    if (colorOrder === 'GRB') {
        return `#${g.toString(16).padStart(2, '0')}${r.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }
    return color; // Return original color for RGB order
}

function testLEDs(color, startPixel = null, endPixel = null) {
    const colorOrder = document.getElementById('test-led-color-order').value;
    const adjustedColor = convertColor(color, colorOrder);

    fetch('/test-leds', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            color: adjustedColor,
            color_order: colorOrder,
            brightness: 0.3,  // Fixed brightness at 0.3
            start_pixel: startPixel,
            end_pixel: endPixel
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            showToast('Failed to test LEDs: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showToast('Error testing LEDs: ' + error, 'danger');
    });
}

// Smooth scrolling for navbar links
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.navbar a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').slice(1);
            const target = document.getElementById(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                // Optionally update the URL hash
                history.replaceState(null, null, '#' + targetId);
            }
        });
    });
});

// Single DOMContentLoaded event listener for all initializations
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipIcons = document.querySelectorAll('.tooltip-icon');
    tooltipIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            toggleTooltip(this);
        });
    });

    // Initialize LED test section toggle
    const ledTestToggle = document.getElementById('led-test-toggle');
    const ledTestContent = document.getElementById('led-test-content');
    if (ledTestToggle && ledTestContent) {
        ledTestToggle.addEventListener('click', function() {
            const isVisible = ledTestContent.classList.contains('show');
            ledTestContent.classList.toggle('show');
            this.querySelector('.info-toggle').textContent = isVisible ? '▼' : '▲';
        });
    }

    // Initialize all status updates
    updateAllServiceStatuses();
    
    // Set up intervals for status updates
    setInterval(updateAllServiceStatuses, 10000);  // Update service statuses every 10 seconds
   
    // Initialize timezone dropdown
    populateTimezones();

    // Initialize line numbers for airports textarea
    const textarea = document.getElementById('airportsText');
    const lineNumbers = document.getElementById('line-numbers');
    if (textarea && lineNumbers) {
        updateLineNumbers(textarea, lineNumbers);
        textarea.addEventListener('input', () => updateLineNumbers(textarea, lineNumbers));
        textarea.addEventListener('scroll', () => {
            lineNumbers.style.transform = `translateY(-${textarea.scrollTop}px)`;
        });
    }

    // Restore scroll position if saved
    const scrollPosition = sessionStorage.getItem('scrollPosition');
    if (scrollPosition) {
        window.scrollTo(0, parseInt(scrollPosition));
        sessionStorage.removeItem('scrollPosition');
    }

    // Add color order change handler
    const colorOrderSelect = document.getElementById('test-led-color-order');
    if (colorOrderSelect) {
        colorOrderSelect.addEventListener('change', function() {
            // If a test is currently running, update with the new color order
            const testStatus = document.getElementById('test-status');
            if (testStatus && testStatus.textContent !== 'Testing: Not Started') {
                const currentColor = document.getElementById('custom-led-color').value;
                const { startPixel, endPixel } = getLedRange();
                testLEDs(currentColor, startPixel, endPixel);
            }
        });
    }
});

// Function to update line numbers
function updateLineNumbers(textarea, lineNumbers) {
    const lines = textarea.value.split('\n');
    lineNumbers.innerHTML = lines.map((_, index) => `<div>${index + 1}</div>`).join('');
}

// Function to manually update weather
async function updateWeatherManually() {
    try {
        // Show a loading toast
        showToast('Updating weather data...', 'info');

        const response = await fetch('/update-weather', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.status === 'success') {
            showToast('Weather updated successfully', 'success');
            // Update the weather status display
            updateWeatherStatus();
            // If we're on the map page, update the markers
            if (typeof updateAirportMarkers === 'function') {
                updateAirportMarkers();
            }
        } else {
            showToast(data.message || 'Failed to update weather', 'danger');
        }
    } catch (error) {
        console.error('Error updating weather:', error);
        showToast('Error updating weather: ' + error.message, 'danger');
    }
}

// Function to confirm and execute system shutdown
function confirmShutdown() {
    if (confirm("WARNING: This will stop all services, turn off the LEDs, and shut down the controller.\n\nA manual power cycle will be required to restart the map. \n\nAre you sure you want to proceed with the shutdown?")) {
        const countdownDiv = document.getElementById('shutdown-countdown');
        const countdownTimer = document.getElementById('countdown-timer');
        countdownDiv.style.display = 'block';
        // Disable the shutdown button to prevent multiple clicks
        const shutdownButton = document.querySelector('.shutdown-panel .btn-danger');
        shutdownButton.disabled = true;
        // Set shutdown-specific overlay text
        countdownDiv.innerHTML = `
            <div class="shutdown-countdown">
                <p>System will shut down in <span id="countdown-timer">30</span> seconds...</p>
                <p>It is safe to remove power when the countdown reaches zero.</p>
                <p style="font-size: 1.2em; color: #f44336;">Shutting down...</p>
            </div>
        `;
        const countdownTimerElem = document.getElementById('countdown-timer');
        let secondsLeft = 30;
        const countdownInterval = setInterval(() => {
            secondsLeft--;
            if (countdownTimerElem) countdownTimerElem.textContent = secondsLeft;
            if (secondsLeft <= 0) {
                clearInterval(countdownInterval);
            }
        }, 1000);
        fetch('/shutdown', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                throw new Error('Server returned non-JSON response');
            }
        })
        .then(data => {
            if (data.success) {
                showToast('System is shutting down...', 'info');
            } else {
                showToast('Error initiating shutdown: ' + (data.error || 'Unknown error'), 'danger');
                shutdownButton.disabled = false;
                countdownDiv.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error during shutdown:', error);
            showToast('Error during shutdown: ' + error.message, 'danger');
            shutdownButton.disabled = false;
            countdownDiv.style.display = 'none';
        });
    }
}

function confirmRestart() {
    if (confirm("This will restart your Raspberry Pi. All services will stop and the device will reboot.\n\nAre you sure you want to restart?")) {
        const countdownDiv = document.getElementById('shutdown-countdown');
        const countdownTimer = document.getElementById('countdown-timer');
        countdownDiv.style.display = 'block';
        // Disable the restart button to prevent multiple clicks
        const restartButton = document.querySelector('.shutdown-panel .btn-warning');
        restartButton.disabled = true;
        // Set restart-specific overlay text
        countdownDiv.innerHTML = `
            <div class="shutdown-countdown">
                <p>System will restart in <span id="countdown-timer">60</span> seconds...</p>
                <p>Do NOT remove power during restart</p>
                <p>When the lights come back on, you can refresh this page</p>
            </div>
        `;
        const countdownTimerElem = document.getElementById('countdown-timer');
        let secondsLeft = 60;
        const countdownInterval = setInterval(() => {
            secondsLeft--;
            if (countdownTimerElem) countdownTimerElem.textContent = secondsLeft;
            if (secondsLeft <= 0) {
                clearInterval(countdownInterval);
            }
        }, 1000);
        fetch('/restart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                throw new Error('Server returned non-JSON response');
            }
        })
        .then(data => {
            if (data.success) {
                showToast('System is restarting...', 'info');
            } else {
                showToast('Error initiating restart: ' + (data.error || 'Unknown error'), 'danger');
                restartButton.disabled = false;
                countdownDiv.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error during restart:', error);
            showToast('Error during restart: ' + error.message, 'danger');
            restartButton.disabled = false;
            countdownDiv.style.display = 'none';
        });
    }
}

// Add input validation for LED range
document.addEventListener('DOMContentLoaded', function() {
    const startPixelInput = document.getElementById('start-pixel');
    const endPixelInput = document.getElementById('end-pixel');

    function validateRange(input) {
        let value = parseInt(input.value);
        if (isNaN(value)) {
            input.value = '';
        } else {
            value = Math.min(Math.max(value, 1), 50);
            input.value = value;
        }
    }

    if (startPixelInput && endPixelInput) {
        startPixelInput.addEventListener('change', function() {
            validateRange(this);
            if (endPixelInput.value && parseInt(endPixelInput.value) < parseInt(this.value)) {
                endPixelInput.value = this.value;
            }
        });

        endPixelInput.addEventListener('change', function() {
            validateRange(this);
            if (startPixelInput.value && parseInt(startPixelInput.value) > parseInt(this.value)) {
                startPixelInput.value = this.value;
            }
        });
    }
});

// Function to start METAR service after stopping LED test service
async function startMetarWithCleanup() {
    // Stop the LED test service first
    await fetch('/led-test-service/stop', { method: 'POST' });
    // Now start the METAR service
    controlService('metar', 'start');
}

// Sunrise/Sunset functionality
document.addEventListener('DOMContentLoaded', function() {
    const daytimeDimmingToggle = document.getElementById('daytime_dimming');
    const sunriseSunsetToggle = document.getElementById('use_sunrise_sunset');
    const sunriseSunsetSection = document.getElementById('sunrise-sunset-section');
    const citySelection = document.getElementById('city-selection');
    const manualTimeSettings = document.getElementById('manual-time-settings');
    const citySelect = document.getElementById('city-select');
    const calculatedTimes = document.getElementById('calculated-times');

    // Handle daytime dimming toggle
    if (daytimeDimmingToggle) {
        daytimeDimmingToggle.addEventListener('change', function() {
            if (this.checked) {
                sunriseSunsetSection.style.display = 'block';
            } else {
                sunriseSunsetSection.style.display = 'none';
                // Uncheck sunrise/sunset toggle when daytime dimming is disabled
                if (sunriseSunsetToggle) {
                    sunriseSunsetToggle.checked = false;
                    citySelection.style.display = 'none';
                    manualTimeSettings.style.opacity = '1';
                    manualTimeSettings.style.pointerEvents = 'auto';
                }
            }
        });
    }

    // Handle sunrise/sunset toggle
    if (sunriseSunsetToggle) {
        sunriseSunsetToggle.addEventListener('change', function() {
            if (this.checked) {
                citySelection.style.display = 'block';
                // Only grey out bright/dim time selects
                document.querySelectorAll('.bright-dim-select').forEach(function(el) {
                    el.style.opacity = '0.5';
                    el.style.pointerEvents = 'none';
                });
            } else {
                citySelection.style.display = 'none';
                // Restore bright/dim time selects
                document.querySelectorAll('.bright-dim-select').forEach(function(el) {
                    el.style.opacity = '1';
                    el.style.pointerEvents = 'auto';
                });
                calculatedTimes.innerHTML = '';
            }
            // On page load, set correct state
            if (sunriseSunsetToggle.checked) {
                document.querySelectorAll('.bright-dim-select').forEach(function(el) {
                    el.style.opacity = '0.5';
                    el.style.pointerEvents = 'none';
                });
            } else {
                document.querySelectorAll('.bright-dim-select').forEach(function(el) {
                    el.style.opacity = '1';
                    el.style.pointerEvents = 'auto';
                });
            }
        });
    }

    // Handle city selection
    if (citySelect) {
        citySelect.addEventListener('change', function() {
            const selectedCity = this.value;
            if (selectedCity && sunriseSunsetToggle && sunriseSunsetToggle.checked) {
                calculateSunTimes(selectedCity);
            } else {
                calculatedTimes.innerHTML = '';
            }
        });
    }
});

// Function to calculate sun times for a selected city
async function calculateSunTimes(cityName) {
    const calculatedTimes = document.getElementById('calculated-times');
    
    try {
        calculatedTimes.innerHTML = 'Calculating times...';
        
        const response = await fetch('/calculate-sun-times', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ city: cityName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            calculatedTimes.innerHTML = `
                📍 Calculated times for ${cityName}:<br>
                Bright time start: ${data.bright_time_start} (sunrise)<br>
                Dim time start: ${data.dim_time_start} (sunset)
            `;
        } else {
            calculatedTimes.innerHTML = `Error: ${data.error}`;
        }
    } catch (error) {
        console.error('Error calculating sun times:', error);
        calculatedTimes.innerHTML = 'Error calculating times. Please try again.';
    }
}

// Function to toggle tooltip visibility
function toggleTooltip(element) {
    const dropdownContent = element.nextElementSibling;
    if (dropdownContent && dropdownContent.classList.contains('dropdown-content')) {
        const isVisible = dropdownContent.style.display === 'block';
        dropdownContent.style.display = isVisible ? 'none' : 'block';
        
        // Update aria-expanded attribute for accessibility
        element.setAttribute('aria-expanded', !isVisible);
        
        // Close other tooltips when opening a new one
        if (!isVisible) {
            document.querySelectorAll('.dropdown-content').forEach(content => {
                if (content !== dropdownContent) {
                    content.style.display = 'none';
                }
            });
            document.querySelectorAll('.tooltip-icon').forEach(icon => {
                if (icon !== element) {
                    icon.setAttribute('aria-expanded', 'false');
                }
            });
        }
    }
}

// Function to close all tooltips when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.classList.contains('tooltip-icon')) {
        document.querySelectorAll('.dropdown-content').forEach(content => {
            content.style.display = 'none';
        });
        document.querySelectorAll('.tooltip-icon').forEach(icon => {
            icon.setAttribute('aria-expanded', 'false');
        });
    }
});
