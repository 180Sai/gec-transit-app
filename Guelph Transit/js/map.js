// ----- Map Variables -----
let map;
let markers = [];
let routeLayers = [];

// ----- Initialize Map -----
function initMap() {
    return new Promise((resolve) => {
        map = L.map('map').setView([43.5448, -80.2482], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);
        resolve();
    });
}

// ----- Marker Management -----
function addMarker(lat, lon, popupContent) {
    const marker = L.marker([lat, lon])
        .addTo(map)
        .bindPopup(popupContent);
    
    markers.push(marker);
    return marker;
}

function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

function clearRoutes() {
    routeLayers.forEach(layer => map.removeLayer(layer));
    routeLayers = [];
}

// ----- Route Drawing -----
function drawRoutesOnMap(routes) {
    clearRoutes();
    
    const colors = ['#2563eb', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444'];
    
    routes.forEach((route, index) => {
        if (route.path && route.path.length > 1) {
            const polyline = L.polyline(route.path, {
                color: colors[index % colors.length],
                weight: 6,
                opacity: 0.7
            }).addTo(map);
            
            routeLayers.push(polyline);
        }
    });
    
    // Fit map to show all routes
    if (routeLayers.length > 0) {
        const group = new L.featureGroup(routeLayers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
    
    // Add markers for start and end
    const start = getSelectedStart();
    const end = getSelectedEnd();
    
    if (start) {
        addMarker(parseFloat(start.latitude), parseFloat(start.longitude), `<strong>Start:</strong> ${start.name}`).openPopup();
    }
    
    if (end) {
        addMarker(parseFloat(end.latitude), parseFloat(end.longitude), `<strong>Destination:</strong> ${end.name}`);
    }
}

function highlightRoute(route, index) {
    clearRoutes();
    
    if (route.path && route.path.length > 1) {
        const colors = ['#2563eb', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444'];
        const polyline = L.polyline(route.path, {
            color: colors[index % colors.length],
            weight: 8,
            opacity: 0.9
        }).addTo(map);
        
        routeLayers.push(polyline);
    }
    
    const start = getSelectedStart();
    const end = getSelectedEnd();
    
    if (start) {
        addMarker(parseFloat(start.latitude), parseFloat(start.longitude), `<strong>Start:</strong> ${start.name}`).openPopup();
    }
    
    if (end) {
        addMarker(parseFloat(end.latitude), parseFloat(end.longitude), `<strong>Destination:</strong> ${end.name}`);
    }
}

function centerOnLocation(lat, lon, zoom = 15) {
    map.setView([lat, lon], zoom);
}

function fitBoundsToStops(start, end) {
    const group = new L.featureGroup([
        L.marker([parseFloat(start.latitude), parseFloat(start.longitude)]),
        L.marker([parseFloat(end.latitude), parseFloat(end.longitude)])
    ]);
    map.fitBounds(group.getBounds().pad(0.1));
}