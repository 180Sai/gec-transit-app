// ----- Configuration -----
const API_BASE = 'http://localhost:8000/api/v1'; // Django backend URL

// ----- Global Variables -----
let stops = [];
let selectedStart = null;
let selectedEnd = null;

// ----- Initialize Application -----
async function initApp() {
    await initMap();
    await fetchStops();
    initSearch();
    initRouteHandlers();
    console.log('App initialized successfully');
}

// ----- Data Management -----
async function fetchStops() {
    try {
        const response = await fetch(`${API_BASE}/stops/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        stops = await response.json();
        console.log('Loaded stops from backend:', stops.length);
    } catch (error) {
        console.error('Failed to fetch stops:', error);
        showStatus('error', 'Failed to load stop data from backend.');
        
        // Fallback to mock data if backend is unavailable
        stops = [
            { id: 1, name: 'University Centre', latitude: 43.5326, longitude: -80.2264 },
            { id: 2, name: 'Gordon at Edinburgh', latitude: 43.5189, longitude: -80.2401 },
            { id: 3, name: 'Stone Road Mall', latitude: 43.5253, longitude: -80.2507 },
            { id: 4, name: 'Guelph Central Station', latitude: 43.5432, longitude: -80.2489 },
            { id: 5, name: 'Imperial at Silvercreek', latitude: 43.5512, longitude: -80.2734 }
        ];
        console.log('Using fallback mock stops data');
    }
}

function getStops() {
    return stops;
}

function setSelectedStart(stop) {
    selectedStart = stop;
    document.getElementById('selectedStart').textContent = `Selected: ${stop.name}`;
    updateRouteResultsMessage();
}

function setSelectedEnd(stop) {
    selectedEnd = stop;
    document.getElementById('selectedEnd').textContent = `Selected: ${stop.name}`;
    updateRouteResultsMessage();
}

function getSelectedStart() {
    return selectedStart;
}

function getSelectedEnd() {
    return selectedEnd;
}

// ----- UI Helpers -----
function updateRouteResultsMessage() {
    const routeResults = document.getElementById('routeResults');
    
    if (!selectedStart || !selectedEnd) {
        if (selectedStart) {
            routeResults.innerHTML = '<div class="status info">Start location selected. Now choose a destination.</div>';
        } else if (selectedEnd) {
            routeResults.innerHTML = '<div class="status info">Destination selected. Now choose a start location.</div>';
        } else {
            routeResults.innerHTML = '<div class="status info">Enter start and destination to find routes</div>';
        }
    } else {
        routeResults.innerHTML = '<div class="status info">Ready to find routes! Click "Find Routes" button.</div>';
    }
}

function showStatus(type, message) {
    const routeResults = document.getElementById('routeResults');
    routeResults.innerHTML = `<div class="status ${type}">${message}</div>`;
}

function showLoading(message = 'Loading...') {
    const routeResults = document.getElementById('routeResults');
    routeResults.innerHTML = `<div class="status loading">${message}</div>`;
}

// ----- Event Handlers -----
function initRouteHandlers() {
    document.getElementById('findRoutes').addEventListener('click', findRoutes);
}

// Start the application
initApp();