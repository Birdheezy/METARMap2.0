// Shared map functionality for both kiosk and settings pages

// Global variable to store the current map instance
let currentAirportMap;

// Add this at the top of the file with other global variables
let weatherUpdateInterval = null;
let isUpdatingWeather = false;

// Function to initialize map colors from config
function initializeMapColors(config) {
    // Set CSS variables for the legend colors
    document.documentElement.style.setProperty('--vfr-color', config.vfrColor);
    document.documentElement.style.setProperty('--mvfr-color', config.mvfrColor);
    document.documentElement.style.setProperty('--ifr-color', config.ifrColor);
    document.documentElement.style.setProperty('--lifr-color', config.lifrColor);
    document.documentElement.style.setProperty('--missing-color', config.missingColor);
    document.documentElement.style.setProperty('--lightening-color', config.lighteningColor);
    document.documentElement.style.setProperty('--snowy-color', config.snowyColor);
}

// Function to update the weather status
function updateWeatherStatus() {
    // Prevent multiple simultaneous calls
    if (window.isUpdatingWeather) {
        return;
    }
    
    window.isUpdatingWeather = true;
    
    fetch('/weather-status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update all instances of the timestamp text
                const lastUpdatedElements = document.querySelectorAll('[id$="weather-last-updated"]');
                lastUpdatedElements.forEach(el => {
                    el.textContent = data.last_updated;
                });
                
                // Update all status dots
                const statusDots = document.querySelectorAll('[id$="weather-status-dot"]');
                
                try {
                    const lastUpdated = data.last_updated;
                    if (lastUpdated !== "Weather data not available") {
                        const parts = lastUpdated.split(' ');
                        const dateParts = parts[0].split('-');
                        const timeParts = parts[1].split(':');
                        
                        const updateTime = new Date(
                            parseInt(dateParts[2]),
                            parseInt(dateParts[0]) - 1,
                            parseInt(dateParts[1]),
                            parseInt(timeParts[0]),
                            parseInt(timeParts[1]),
                            parseInt(timeParts[2])
                        );
                        
                        const now = new Date();
                        const diffMinutes = (now - updateTime) / (1000 * 60);
                        
                        statusDots.forEach(dot => {
                            dot.style.backgroundColor = (diffMinutes < data.threshold) ? 'green' : 'red';
                        });

                        // Always fetch and update weather data
                        fetch('/get-weather-data')
                            .then(response => response.json())
                            .then(weatherData => {
                                if (currentAirportMap) {
                                    currentAirportMap.loadAirports(weatherData);
                                }
                            })
                            .catch(error => {
                                console.error("Error updating airport markers:", error);
                            });
                    } else {
                        statusDots.forEach(dot => dot.style.backgroundColor = 'red');
                    }
                } catch (e) {
                    console.error("Error parsing date:", e);
                    statusDots.forEach(dot => dot.style.backgroundColor = 'red');
                }
            }
        })
        .catch(error => {
            console.error('Error fetching weather status:', error);
            const statusDots = document.querySelectorAll('[id$="weather-status-dot"]');
            statusDots.forEach(dot => dot.style.backgroundColor = 'red');
        })
        .finally(() => {
            window.isUpdatingWeather = false;
        });
}

// Make the function available globally
window.updateWeatherStatus = updateWeatherStatus;

// Start weather updates when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initial update
    updateWeatherStatus();
    
    // Set up interval for updates
    setInterval(updateWeatherStatus, 30000); // Update every 30 seconds
});

// Function to initialize the map system
function initializeMapSystem(config) {
    // Initialize colors first
    initializeMapColors(config);
    
    // Get map settings from the server
    fetch('/map-settings')
        .then(response => {
            if (!response.ok) throw new Error('Failed to load map settings');
            return response.json();
        })
        .then(settings => {
            // Create color configuration for markers
            const colorConfig = {
                vfr: config.vfrColor,
                mvfr: config.mvfrColor,
                ifr: config.ifrColor,
                lifr: config.lifrColor,
                missing: config.missingColor
            };
            
            // Initialize the map
            currentAirportMap = initializeAirportMap('airport-map', colorConfig, settings.center, settings.zoom);
            
            // Set up save map view button if it exists
            const saveButton = document.getElementById('save-map-view');
            if (saveButton) {
                saveButton.addEventListener('click', () => saveMapView(currentAirportMap));
            }
            
            // Load airports
            return fetch('/get-weather-data');
        })
        .then(response => response.json())
        .then(weatherData => {
            if (currentAirportMap) {
                currentAirportMap.loadAirports(weatherData);
            }
        })
        .catch(error => {
            console.error('Error initializing map system:', error);
        });
}

// Function to save the current map view
function saveMapView(airportMap) {
    if (!airportMap || !airportMap.map) return;
    
    const center = airportMap.map.getCenter();
    const zoom = airportMap.map.getZoom();
    
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
        if (!response.ok) throw new Error('Failed to save map settings');
        return response.json();
    })
    .then(() => {
        alert('Map view saved successfully!');
    })
    .catch(error => {
        console.error('Error saving map settings:', error);
        alert('Failed to save map view: ' + error.message);
    });
}

// Map initialization function
function initializeAirportMap(containerId, colorConfig, mapCenter, mapZoom) {
    // Check if map is already initialized
    if (currentAirportMap && currentAirportMap.map) {
        console.log('Map already initialized, returning existing instance');
        return currentAirportMap;
    }

    // Initialize map with configuration from settings
    // Default to US center if not provided
    const centerLat = mapCenter ? mapCenter[0] : 39.8283;
    const centerLon = mapCenter ? mapCenter[1] : -98.5795;
    const zoom = mapZoom || 4;
    
    const map = L.map(containerId).setView([centerLat, centerLon], zoom);
    
    // Use the color configuration
    const vfrColor = colorConfig.vfr;
    const mvfrColor = colorConfig.mvfr;
    const ifrColor = colorConfig.ifr;
    const lifrColor = colorConfig.lifr;
    const missingColor = colorConfig.missing;
    
    // Use a standard map style (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Store markers for easy access
    const airportMarkers = {};
    
    // Return the map and markers object
    return {
        map: map,
        markers: airportMarkers,
        
        // Function to get marker color based on flight category
        getMarkerColor: function(fltCat) {
            // Convert to uppercase for consistency
            const category = fltCat ? fltCat.toUpperCase() : 'MISSING';
            switch(category) {
                case 'VFR': return vfrColor;
                case 'MVFR': return mvfrColor;
                case 'IFR': return ifrColor;
                case 'LIFR': return lifrColor;
                case 'MISSING':
                default: return missingColor;
            }
        },
        
        // Function to create a colored marker
        createMarker: function(lat, lon, color, title) {
            // Create a circular marker with the flight category color
            return L.circleMarker([lat, lon], {
                radius: 10,
                fillColor: color,
                color: '#000',  // Black border for better visibility on light background
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8,
                title: title
            });
        },
        
        // Function to create popup content
        createPopupContent: function(code, data, color) {
            return `
                <div class="airport-popup">
                    <div class="airport-popup-header">
                        <h3 style="color: ${color};">${code}</h3>
                        <span style="margin-left: 8px;">${data.site || 'Unknown location'}</span>
                    </div>
                    <div class="airport-popup-content">
                        <div class="metar-label">Raw METAR:</div>
                        <div class="metar-text">${data.raw_observation || 'Not available'}</div>
                    </div>
                </div>
            `;
        },
        
        // Function to load airports from data
        loadAirports: function(weatherData) {
            // Clear existing markers
            Object.values(this.markers).forEach(marker => this.map.removeLayer(marker));
            this.markers = {};
            
            // Add markers for all airports
            for (const [code, data] of Object.entries(weatherData)) {
                if (data.latitude && data.longitude) {
                    // Get color based on flight category
                    const color = this.getMarkerColor(data.flt_cat);
                    
                    // Create colored marker
                    const marker = this.createMarker(
                        data.latitude,
                        data.longitude,
                        color,
                        `${code}: ${data.site || 'Unknown'}`
                    ).addTo(this.map);
                    
                    // Create popup with airport info
                    const popupContent = this.createPopupContent(code, data, color);
                    marker.bindPopup(popupContent);
                    
                    // Store marker for later reference
                    this.markers[code] = marker;
                }
            }
            
            return Object.keys(weatherData);
        },
        
        // Function to update map based on selected airports
        updateSelection: function(selectedAirports) {
            // Hide all markers first
            Object.values(this.markers).forEach(marker => this.map.removeLayer(marker));
            
            // Show only selected markers
            selectedAirports.forEach(code => {
                if (this.markers[code]) {
                    this.markers[code].addTo(this.map);
                }
            });
        },
        
        // Function to reset map to show all airports
        resetMap: function() {
            Object.values(this.markers).forEach(marker => this.map.removeLayer(marker));
            Object.values(this.markers).forEach(marker => marker.addTo(this.map));
        }
    };
} 