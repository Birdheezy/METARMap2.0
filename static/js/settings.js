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
                    
                    if (lastUpdated !== "Weather data not available") {
                        const parts = lastUpdated.split(' ');
                        const dateParts = parts[0].split('-');
                        const timeParts = parts[1].split(':');
                        
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
                        
                        const updateTime = new Date(
                            year,
                            month,
                            day,
                            parseInt(timeParts[0]), // hour
                            parseInt(timeParts[1]), // minute
                            parseInt(timeParts[2])  // second
                        );
                        
                        const now = new Date();
                        const diffMinutes = (now - updateTime) / (1000 * 60);
                        
                        // Use a default threshold if WEATHER_UPDATE_THRESHOLD is not defined
                        const staleThreshold = typeof WEATHER_UPDATE_THRESHOLD !== 'undefined' ? WEATHER_UPDATE_THRESHOLD : 10;
                        
                        // Update all status dots
                        statusDots.forEach(dot => {
                            if (diffMinutes < staleThreshold) {
                                dot.style.backgroundColor = 'green';
                            } else {
                                dot.style.backgroundColor = 'red';
                            }
                        });
                    } else {
                        // If weather data is not available, set dots to red
                        statusDots.forEach(dot => {
                            dot.style.backgroundColor = 'red';
                        });
                    }
                } catch (e) {
                    console.error("Error parsing date:", e);
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

// Airport Map Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize map if the element exists
    const mapElement = document.getElementById('airport-map');
    if (mapElement) {
        let map = null;

        // Load saved map settings
        fetch('/map-settings')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load map settings');
                }
                return response.json();
            })
            .then(settings => {
                map = L.map('airport-map').setView(settings.center, settings.zoom);
                
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);

                // Add save button event listener
                document.getElementById('save-map-view').addEventListener('click', function() {
                    const center = map.getCenter();
                    const zoom = map.getZoom();

                    fetch('/map-settings', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            center: [center.lat, center.lng],
                            zoom: zoom
                        })
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Failed to save map settings');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.success) {
                            showToast('Map view saved successfully!', 'success');
                        } else {
                            showToast(data.error || 'Failed to save map view', 'danger');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showToast('Error saving map view: ' + error.message, 'danger');
                    });
                });

                // Function to convert RGB tuple to hex color
                function rgbToHex(r, g, b) {
                    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
                }

                // Function to get color based on flight category
                function getMarkerColor(fltCat) {
                    // Return colors directly for map display without LED conversion
                    switch (fltCat ? fltCat.toLowerCase() : 'missing') {
                        case 'vfr':
                            return VFR_COLOR;
                        case 'mvfr':
                            return MVFR_COLOR;
                        case 'ifr':
                            return IFR_COLOR;
                        case 'lifr':
                            return LIFR_COLOR;
                        case 'missing':
                        default:
                            return MISSING_COLOR;
                    }
                }

                // Store markers in a layer group for easy removal
                let markersLayer = L.layerGroup().addTo(map);

                function updateAirportMarkers() {
                    fetch('/airport-conditions')
                        .then(response => response.json())
                        .then(data => {
                            // Clear existing markers
                            markersLayer.clearLayers();

                            data.airports.forEach(airport => {
                                const marker = L.circleMarker([airport.lat, airport.lon], {
                                    radius: 8,
                                    fillColor: getMarkerColor(airport.fltCat),
                                    color: '#000',
                                    weight: 1,
                                    opacity: 1,
                                    fillOpacity: 0.8
                                });

                                // Add popup with airport info
                                marker.bindPopup(`
                                    <b>${airport.icao}</b><br>
                                    <b>${airport.site}</b><br>
                                    Flight Category: ${airport.fltCat}<br>
                                    <hr>
                                    <small>${airport.raw_observation}</small>
                                `);

                                markersLayer.addLayer(marker);
                            });
                        })
                        .catch(error => console.error('Error updating airport markers:', error));
                }

                // Add airport markers
                updateAirportMarkers();
            })
            .catch(error => {
                console.error('Error loading map settings:', error);
                // Fallback to default settings if loading fails
                map = L.map('airport-map').setView([37.0902, -99.7558], 4);
                
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);
                updateAirportMarkers();
            });
    }
});

// LED Testing functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle preset color buttons
    document.querySelectorAll('.led-test-btn').forEach(button => {
        button.addEventListener('click', function() {
            const color = this.dataset.color;
            testLEDs(color);
        });
    });

    // Handle custom color test
    document.getElementById('test-custom-color')?.addEventListener('click', function() {
        const color = document.getElementById('custom-led-color').value;
        testLEDs(color);
    });

    // Brightness control
    const brightnessInput = document.getElementById('test-brightness');
    if (brightnessInput) {
        brightnessInput.addEventListener('change', async function() {
            const brightness = parseFloat(this.value);
            if (brightness >= 0.01 && brightness <= 1.0) {
                try {
                    const response = await fetch('/update-brightness', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ brightness: brightness })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to update brightness');
                    }
                    
                    const result = await response.json();
                    if (result.success) {
                        showNotification('Brightness updated successfully', 'success');
                    } else {
                        showNotification(result.error || 'Failed to update brightness', 'error');
                    }
                } catch (error) {
                    console.error('Error updating brightness:', error);
                    showNotification('Failed to update brightness: ' + error.message, 'error');
                }
            } else {
                showNotification('Brightness must be between 0.01 and 1.0', 'error');
                this.value = 0.5; // Reset to default if invalid
            }
        });
    }

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
    const nextColor = document.getElementById('next-color');
    const stopAutoTest = document.getElementById('stop-auto-test');
    const testProgress = document.getElementById('test-progress');
    const progressBar = document.querySelector('.progress-bar');
    const testStatus = document.getElementById('test-status');

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

    if (runAutoTest && stopAutoTest && nextColor) {
        runAutoTest.addEventListener('click', function() {
            // Start the LED test service
            fetch('/led-test-service/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentIndex = -1; // Reset to start
                    testProgress.style.display = 'block';
                    runAutoTest.style.display = 'none';
                    nextColor.style.display = 'inline-block';
                    stopAutoTest.style.display = 'inline-block';
                    showNextColor();
                } else {
                    showToast('Failed to start LED test service: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                showToast('Error starting LED test service: ' + error, 'danger');
            });
        });

        nextColor.addEventListener('click', function() {
            showNextColor();
        });

        stopAutoTest.addEventListener('click', function() {
            // Reset UI state immediately
            testProgress.style.display = 'none';
            runAutoTest.style.display = 'inline-block';
            nextColor.style.display = 'none';
            stopAutoTest.style.display = 'none';
            currentIndex = -1;

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
        });

        function showNextColor() {
            currentIndex++;
            if (currentIndex >= colors.length) {
                currentIndex = 0;
            }

            const currentColor = colors[currentIndex];
            testLEDs(currentColor.color);
            testStatus.textContent = `Testing: ${currentColor.name}`;
            progressBar.style.width = `${(currentIndex + 1) / colors.length * 100}%`;
        }
    }
});

function testLEDs(color) {
    fetch('/test-leds', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ color: color })
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

    // Initialize all status updates
    updateAllServiceStatuses();
    updateWeatherStatus();
    
    // Set up intervals for status updates
    setInterval(updateAllServiceStatuses, 10000);  // Update service statuses every 10 seconds
    setInterval(updateWeatherStatus, 30000);      // Update weather status every 30 seconds

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
});

// Function to update line numbers
function updateLineNumbers(textarea, lineNumbers) {
    const lines = textarea.value.split('\n');
    lineNumbers.innerHTML = lines.map((_, index) => `<div>${index + 1}</div>`).join('');
}
