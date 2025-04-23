// Shared map functionality for both kiosk and settings pages

// Map initialization function
function initializeAirportMap(containerId, colorConfig, mapCenter, mapZoom) {
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
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8,
                title: title
            });
        },
        
        // Function to create popup content
        createPopupContent: function(code, data, color) {
            return `
                <div style="min-width: 200px;">
                    <h3 style="margin: 0 0 5px 0; color: ${color}; border-bottom: 1px solid #ccc; padding-bottom: 5px;">${code}</h3>
                    <div style="margin-bottom: 5px;">${data.site || 'Unknown location'}</div>
                    
                    <div style="display: flex; margin-bottom: 10px; align-items: center;">
                        <div style="font-weight: bold; margin-right: 8px;">Flight Category:</div>
                        <div style="color: ${color};">${data.flt_cat || 'Unknown'}</div>
                    </div>
                    
                    <div style="margin-top: 10px; border-top: 1px solid #ccc; padding-top: 8px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">Raw METAR:</div>
                        <div style="font-family: monospace; word-break: break-all; line-height: 1.4; background-color: #f8f8f8; padding: 8px; border-radius: 4px; border: 1px solid #eee;">${data.raw_observation || 'Not available'}</div>
                    </div>
                </div>
            `;
        },
        
        // Function to add a legend to the map
        addLegend: function() {
            const legend = L.control({position: 'bottomright'});
            
            legend.onAdd = (map) => {
                const div = L.DomUtil.create('div', 'map-legend');
                div.innerHTML = `
                    <div style="background: rgba(255, 255, 255, 0.8); padding: 5px; border-radius: 5px; color: #333;">
                        <div style="margin-bottom: 5px; font-weight: bold;">Flight Categories</div>
                        <div style="display: flex; flex-wrap: wrap;">
                            <span style="display: flex; align-items: center; margin-right: 5px;">
                                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: ${vfrColor}; margin-right: 5px;"></span>
                                VFR
                            </span>
                            <span style="display: flex; align-items: center; margin-right: 5px;">
                                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: ${mvfrColor}; margin-right: 5px;"></span>
                                MVFR
                            </span>
                            <span style="display: flex; align-items: center; margin-right: 5px;">
                                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: ${ifrColor}; margin-right: 5px;"></span>
                                IFR
                            </span>
                            <span style="display: flex; align-items: center; margin-right: 5px;">
                                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: ${lifrColor}; margin-right: 5px;"></span>
                                LIFR
                            </span>
                            <span style="display: flex; align-items: center;">
                                <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: ${missingColor}; margin-right: 5px;"></span>
                                Missing
                            </span>
                        </div>
                    </div>
                `;
                return div;
            };
            
            legend.addTo(map);
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
            
            // Add a legend to the map
            this.addLegend();
            
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