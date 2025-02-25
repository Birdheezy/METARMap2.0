document.addEventListener('DOMContentLoaded', function() {
    let timeLeft = 600; // 10 minutes
    let activeTimeout = null;
    const timerDisplay = document.getElementById('countdown');
    const airportInput = document.getElementById('airport-input');
    const resetButton = document.getElementById('reset-button');
    const applyButton = document.getElementById('apply-filters');
    const clearButton = document.getElementById('clear-input');
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const statusMessage = document.getElementById('status-message');
    const airportCount = document.getElementById('airport-count');

    // Major airports preset
    const MAJOR_AIRPORTS = [
        'KATL', 'KLAX', 'KDFW', 'KORD', 'KDEN',
        'KJFK', 'KSFO', 'KLAS', 'KMIA', 'KPHX'
    ];

    // Cache preview elements
    const windyPreview = document.getElementById('windy-preview');
    const lightningPreview = document.getElementById('lightning-preview');
    const snowPreview = document.getElementById('snow-preview');
    const majorPreview = document.getElementById('major-preview');
    const manualPreview = document.getElementById('manual-preview');
    const totalPreview = document.getElementById('total-preview');

    function showMessage(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.style.display = 'block';
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, 5000);
    }

    function updateTimer() {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        if (timeLeft <= 0) {
            resetToNormal();
        } else {
            timeLeft--;
        }
    }

    function resetTimer() {
        timeLeft = 600; // Reset to 10 minutes
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
                clearActiveStates();
                resetTimer();
                showMessage('Reset to normal operation', 'success');
                airportCount.textContent = '';
                // Update the condition lists after reset
                updateConditionLists();
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('Failed to reset: ' + error.message, 'error');
                resetTimer();
            });
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
            resetTimer();
            showMessage('Filters applied successfully', 'success');
            airportCount.textContent = `Showing ${data.count} airports`;

            // Close the touch keyboard if open
            airportInput.blur();
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage(error.message, 'error');
        });
    }

    // Initialize timer
    setInterval(updateTimer, 1000);

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
});
