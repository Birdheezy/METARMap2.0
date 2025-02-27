document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const TIMER_DURATION = 600; // Timer duration in seconds

    let timeLeft = TIMER_DURATION;
    let timerInterval = null; // Store the interval ID
    const timerDisplay = document.getElementById('countdown');
    const airportInput = document.getElementById('airport-input');
    const resetButton = document.getElementById('reset-button');
    const applyButton = document.getElementById('apply-filters');
    const clearButton = document.getElementById('clear-input');
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const statusMessage = document.getElementById('status-message');
    const airportCount = document.getElementById('airport-count');

    // Toggle info panel
    document.getElementById('info-toggle').addEventListener('click', function() {
        const content = document.getElementById('info-content');
        const toggle = document.querySelector('.info-toggle');

        if (content.classList.contains('show')) {
            content.classList.remove('show');
            toggle.textContent = '▼';
        } else {
            content.classList.add('show');
            toggle.textContent = '▲';
        }
    });

    // Major airports preset
    const MAJOR_AIRPORTS = [
        'KATL', 'KLAX', 'KDFW', 'KORD', 'KDEN',
        'KJFK', 'KSFO', 'KLAS', 'KMIA', 'KPHX',
        'KLGA', 'KSEA',
    ];

    // Cache preview elements
    const windyPreview = document.getElementById('windy-preview');
    const lightningPreview = document.getElementById('lightning-preview');
    const snowPreview = document.getElementById('snow-preview');
    const majorPreview = document.getElementById('major-preview');
    const manualPreview = document.getElementById('manual-preview');
    const totalPreview = document.getElementById('total-preview');

    // Map variables
    let airportMap;
    let allAirports = [];

    function showMessage(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.style.display = 'block';
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, 5000);
    }

    function startTimer() {
        // Clear any existing timer first
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }

        // Reset the time
        timeLeft = TIMER_DURATION;

        // Update display immediately
        updateTimer();

        // Start a new timer with a slight delay to ensure clean start
        setTimeout(() => {
            timerInterval = setInterval(updateTimer, 1000);
            console.log("Timer started with interval ID:", timerInterval);
        }, 100);
    }

    function updateTimer() {
        console.log("Timer update, timeLeft:", timeLeft);
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        if (timeLeft <= 0) {
            console.log("Timer reached zero, resetting...");
            clearInterval(timerInterval); // Stop the timer
            resetToNormal();
        } else {
            timeLeft--;
        }
    }

    function resetTimer() {
        timeLeft = TIMER_DURATION; // Reset to 10 minutes
        updateTimer();
    }

    function resetToNormal() {
        fetch('/kiosk/reset', { method: 'POST' })
            .then(response => {
                if (!response.ok) throw new Error('Failed to reset');
                return response.json();
            })
            .then(data => {
                // After successful reset, update weather
                return fetch('/update-weather', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
            })
            .then(response => {
                if (!response.ok) throw new Error('Failed to update weather');

                // Clear all checkboxes and input field
                clearActiveStates();

                // Reset the preview displays
                resetPreviewDisplays();

                // Reset the map to show all airports
                resetMap();

                // Restart the timer instead of just resetting the time
                startTimer();

                showMessage('Reset to normal operation', 'success');
                airportCount.textContent = '';

                // Update the condition lists after reset
                updateConditionLists();
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('Failed to reset: ' + error.message, 'error');
                // Still restart the timer even if there was an error
                startTimer();
            });
    }

    // Add a new function to reset all preview displays
    function resetPreviewDisplays() {
        windyPreview.textContent = '';
        lightningPreview.textContent = '';
        snowPreview.textContent = '';
        majorPreview.textContent = '';
        manualPreview.textContent = '';
        totalPreview.textContent = '0';
    }

    function clearActiveStates() {
        checkboxes.forEach(checkbox => checkbox.checked = false);
        airportInput.value = '';
    }

    function applyCurrentSelection() {
        const selectedTypes = Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.dataset.type);

        // Get manual airport entries
        const manualAirports = airportInput.value
            .toUpperCase()
            .split(/[\s,]+/)
            .filter(code => code.length === 4);

        // Basic format validation (K + 3 letters)
        const invalidFormat = manualAirports.filter(code => !code.match(/^K[A-Z]{3}$/));
        if (invalidFormat.length > 0) {
            showMessage(`Invalid airport code format: ${invalidFormat.join(', ')}. Must be K followed by 3 letters.`, 'error');
            return;
        }

        // Prepare the request data
        const requestData = {
            filters: selectedTypes,
            majorAirports: selectedTypes.includes('major') ? MAJOR_AIRPORTS : [],
            manualAirports: manualAirports
        };

        // Send the request to apply filters
        fetch('/kiosk/apply-filters', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json().then(data => ({status: response.ok, data: data})))
        .then(({status, data}) => {
            if (!status) {
                throw new Error(data.error || 'Failed to apply filters');
            }
            startTimer();
            showMessage('Filters applied successfully', 'success');
            airportCount.textContent = `Showing ${data.count} airports`;

            // Update the map with selected airports
            const selectedAirports = [...allAirports]; // Convert Set to Array
            updateMapWithSelection(selectedAirports);

            // Close the touch keyboard if open
            airportInput.blur();
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage(error.message, 'error');
        });
    }

    // Start the timer when the page loads
    console.log("Starting timer...");
    startTimer();
    console.log("Timer started, interval ID:", timerInterval);

    // Handle apply filters button click
    applyButton.addEventListener('click', applyCurrentSelection);

    // Handle clear button
    clearButton.addEventListener('click', () => {
        airportInput.value = '';
        airportInput.focus();
    });

    // Handle reset button
    resetButton.addEventListener('click', resetToNormal);

    // Handle Enter key in input field
    airportInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            applyCurrentSelection();
        }
    });

    // Function to update condition airport lists
    function updateConditionLists() {
        // We don't need to show the active airports in the checkboxes anymore
        // since we have the selection preview section
        document.querySelector('.windy-airports').textContent = '';
        document.querySelector('.lightning-airports').textContent = '';
        document.querySelector('.snow-airports').textContent = '';
    }

    // Update lists initially and every minute
    updateConditionLists();
    setInterval(updateConditionLists, 60000);

    // Add CSS for the condition airport lists
    const style = document.createElement('style');
    style.textContent = `
        .condition-airports {
            font-size: 0.8em;
            color: #aaa;
            margin-top: 4px;
        }
    `;
    document.head.appendChild(style);

    // Update preview when checkboxes change
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updatePreview);
    });

    // Update preview when manual input changes
    airportInput.addEventListener('input', updatePreview);

    function updatePreview() {
        // Clear all previews
        windyPreview.textContent = '';
        lightningPreview.textContent = '';
        snowPreview.textContent = '';
        majorPreview.textContent = '';
        manualPreview.textContent = '';

        let totalAirports = new Set();

        // Fetch all condition data at once
        fetch('/kiosk/condition-airports')
            .then(response => response.json())
            .then(data => {
                // Update windy preview if checked
                if (document.getElementById('windy').checked) {
                    const windyAirports = Object.keys(data.windy || {});
                    windyPreview.textContent = windyAirports.join(', ') || 'None';
                    windyAirports.forEach(airport => totalAirports.add(airport));
                }

                // Update lightning preview if checked
                if (document.getElementById('lightning').checked) {
                    const lightningAirports = Object.keys(data.lightning || {});
                    lightningPreview.textContent = lightningAirports.join(', ') || 'None';
                    lightningAirports.forEach(airport => totalAirports.add(airport));
                }

                // Update snow preview if checked
                if (document.getElementById('snow').checked) {
                    const snowyAirports = Object.keys(data.snowy || {});
                    snowPreview.textContent = snowyAirports.join(', ') || 'None';
                    snowyAirports.forEach(airport => totalAirports.add(airport));
                }

                updateTotalCount();
            });

        // Update major hubs preview if checked
        if (document.getElementById('major').checked) {
            majorPreview.textContent = MAJOR_AIRPORTS.join(', ');
            MAJOR_AIRPORTS.forEach(airport => totalAirports.add(airport));
        }

        // Update manual entry preview
        const manualAirports = airportInput.value
            .toUpperCase()
            .split(/[\s,]+/)
            .filter(code => code.length === 4 && code.match(/^K[A-Z]{3}$/));

        if (manualAirports.length > 0) {
            manualPreview.textContent = manualAirports.join(', ');
            manualAirports.forEach(airport => totalAirports.add(airport));
        }

        updateTotalCount();

        function updateTotalCount() {
            totalPreview.textContent = totalAirports.size;
        }
    }

    // Function to update the weather status
    function updateWeatherStatus() {
        const lastUpdatedElement = document.getElementById('weather-last-updated');
        const statusDot = document.getElementById('weather-status-dot');
        
        if (lastUpdatedElement && lastUpdatedElement.textContent !== "Weather data not available") {
            try {
                // Parse the date in MM-DD-YYYY HH:MM:SS format
                const lastUpdated = lastUpdatedElement.textContent;
                const parts = lastUpdated.split(' ');
                const dateParts = parts[0].split('-');
                const timeParts = parts[1].split(':');
                
                // Create date object (months are 0-indexed in JS)
                const updateTime = new Date(
                    parseInt(dateParts[2]), // year
                    parseInt(dateParts[0]) - 1, // month (0-indexed)
                    parseInt(dateParts[1]), // day
                    parseInt(timeParts[0]), // hour
                    parseInt(timeParts[1]), // minute
                    parseInt(timeParts[2])  // second
                );
                
                const now = new Date();
                const diffMinutes = (now - updateTime) / (1000 * 60);
                
                // Debug information
                console.log("Weather update time:", updateTime);
                console.log("Current time:", now);
                console.log("Difference in minutes:", diffMinutes);
                console.log("WEATHER_UPDATE_THRESHOLD:", WEATHER_UPDATE_THRESHOLD);
                
                if (diffMinutes < WEATHER_UPDATE_THRESHOLD) {
                    console.log("Setting dot to green");
                    statusDot.style.backgroundColor = 'green';
                } else {
                    console.log("Setting dot to red");
                    statusDot.style.backgroundColor = 'red';
                }
            } catch (e) {
                console.error("Error parsing date:", e);
                statusDot.style.backgroundColor = 'red';
            }
        } else {
            statusDot.style.backgroundColor = 'red';
        }
    }

    // Call initially and set interval
    updateWeatherStatus();
    setInterval(updateWeatherStatus, 30000); // Update every 30 seconds

    // Function to initialize map after Leaflet is loaded
    function initMap() {
        if (typeof L !== 'undefined' && typeof initializeAirportMap !== 'undefined') {
            // Access the color variables directly 
            const colorConfig = {
                vfr: VFR_COLOR,
                mvfr: MVFR_COLOR,
                ifr: IFR_COLOR,
                lifr: LIFR_COLOR,
                missing: MISSING_COLOR
            };
            
            // Fetch map settings from the server
            fetch('/map-settings')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to load map settings');
                    }
                    return response.json();
                })
                .then(settings => {
                    // Initialize the map with fetched settings
                    airportMap = initializeAirportMap('airport-map', colorConfig, settings.center, settings.zoom);
                    
                    // Load airports
                    loadAirportMap();
                })
                .catch(error => {
                    console.error('Error loading map settings:', error);
                    // Fallback to default settings if loading fails
                    airportMap = initializeAirportMap('airport-map', colorConfig);
                    
                    // Load airports even if map settings failed
                    loadAirportMap();
                });
        } else {
            // If dependencies aren't loaded yet, wait for them
            setTimeout(initMap, 100);
        }
    }

    // Function to load all airports
    function loadAirportMap() {
        fetch('/weather-status')
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    console.error("Failed to get weather status");
                    return;
                }
                
                // Fetch weather data
                return fetch('/get-weather-data');
            })
            .then(response => response.json())
            .then(weatherData => {
                // Load airports using the shared function
                allAirports = airportMap.loadAirports(weatherData);
            })
            .catch(error => {
                console.error("Error loading airport map:", error);
            });
    }

    // Function to update map based on selected airports
    function updateMapWithSelection(selectedAirports) {
        if (airportMap) {
            airportMap.updateSelection(selectedAirports);
        }
    }

    // Function to reset map to show all airports
    function resetMap() {
        if (airportMap) {
            airportMap.resetMap();
        }
    }

    // Initialize map when document is ready
    initMap();
});
