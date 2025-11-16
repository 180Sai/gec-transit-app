// ----- Route Planning -----
async function findRoutes() {
    const start = getSelectedStart();
    const end = getSelectedEnd();
    
    if (!start || !end) {
        showStatus('error', 'Please select both start and destination locations.');
        return;
    }
    
    if (start.id === end.id) {
        showStatus('error', 'Start and destination cannot be the same location.');
        return;
    }
    
    const findBtn = document.getElementById('findRoutes');
    findBtn.disabled = true;
    findBtn.textContent = 'Finding Routes...';
    
    showLoading('Finding the best routes for you...');
    
    try {
        const routes = await fetchRoutesFromBackend(start, end);
        displayRouteResults(routes);
        drawRoutesOnMap(routes);
    } catch (error) {
        console.error('Error finding routes:', error);
        showStatus('error', 'Failed to find routes. Please try again.');
    } finally {
        findBtn.disabled = false;
        findBtn.textContent = 'Find Routes';
    }
}

async function fetchRoutesFromBackend(start, end) {
    // Use your Django backend API
    const params = new URLSearchParams({
        from_lat: start.latitude,
        from_lon: start.longitude,
        to_lat: end.latitude,
        to_lon: end.longitude
    });
    
    const response = await fetch(`${API_BASE}/plan/?${params}`);
    
    if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Transform backend response to match frontend format
    return transformBackendResponse(data);
}

function transformBackendResponse(backendData) {
    // Transform the Django backend response to match our frontend format
    // This will depend on your actual ItinerarySerializer output
    
    if (!backendData || !Array.isArray(backendData)) {
        return [];
    }
    
    return backendData.map((itinerary, index) => {
        // Extract basic route information
        // You'll need to adjust this based on your actual serializer output
        const duration = itinerary.total_duration || 30;
        const cost = itinerary.total_cost || 3.50;
        const transfers = itinerary.transfer_count || 0;
        
        // Create a simple path for demonstration
        // In production, you'd use actual shape data from the backend
        const start = getSelectedStart();
        const end = getSelectedEnd();
        const path = [
            [parseFloat(start.latitude), parseFloat(start.longitude)],
            [43.5330, -80.2270],
            [43.5345, -80.2285],
            [43.5360, -80.2300],
            [parseFloat(end.latitude), parseFloat(end.longitude)]
        ];
        
        // Create steps based on itinerary segments
        const steps = createStepsFromItinerary(itinerary);
        
        return {
            id: `route_${index + 1}`,
            duration: duration,
            cost: cost,
            transfers: transfers,
            ecoScore: 75 + Math.floor(Math.random() * 20), // Mock eco score
            features: ['electric_bus'], // Mock features
            steps: steps,
            path: path
        };
    });
}

function createStepsFromItinerary(itinerary) {
    // Create step-by-step instructions from itinerary data
    // This is a simplified version - adjust based on your actual data structure
    
    const steps = [];
    
    // Add walking step to first stop
    steps.push({
        type: 'walk',
        duration: 5,
        description: 'Walk to nearest bus stop'
    });
    
    // Add bus segments (mock for now)
    steps.push({
        type: 'bus',
        duration: 15,
        description: 'Take bus to transfer point'
    });
    
    // Add transfer if needed
    if (itinerary.transfer_count > 0) {
        steps.push({
            type: 'walk',
            duration: 3,
            description: 'Transfer to connecting bus'
        });
        
        steps.push({
            type: 'bus',
            duration: 10,
            description: 'Take bus to destination'
        });
    }
    
    // Add final walking step
    steps.push({
        type: 'walk',
        duration: 2,
        description: 'Walk to final destination'
    });
    
    return steps;
}

function displayRouteResults(routes) {
    const container = document.getElementById('routeResults');
    
    if (routes.length === 0) {
        container.innerHTML = '<div class="status info">No routes found matching your criteria.</div>';
        return;
    }
    
    container.innerHTML = '';
    
    routes.forEach((route, index) => {
        const div = document.createElement('div');
        div.className = 'list-item route-option';
        
        const stepsHtml = route.steps.map(step => {
            const iconClass = step.type === 'walk' ? 'walk' : 
                             step.type === 'bus' ? 'bus' : 
                             step.type === 'on_demand' ? 'eco' : 'bus';
            const iconText = step.type === 'walk' ? 'W' : 
                            step.type === 'bus' ? 'B' : 
                            step.type === 'on_demand' ? 'O' : 'B';
            
            return `
                <div class="route-step">
                    <div class="step-icon ${iconClass}">${iconText}</div>
                    <span>${step.description} (${step.duration} min)</span>
                </div>
            `;
        }).join('');
        
        const featuresHtml = route.features.map(feature => {
            const featureName = feature === 'electric_bus' ? 'Electric' :
                               feature === 'ride_sharing' ? 'Ride Share' :
                               feature === 'on_demand' ? 'On Demand' : feature;
            return `<span style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-size:10px; margin-right:4px;">${featureName}</span>`;
        }).join('');
        
        div.innerHTML = `
            <div class="route-header">
                <div class="route-title">Option ${index + 1}</div>
                <div class="route-duration">${route.duration} min</div>
            </div>
            <div class="route-details">
                <div>Cost: $${route.cost.toFixed(2)}</div>
                <div>Transfers: ${route.transfers}</div>
            </div>
            <div class="route-details">
                <div>Eco Score: ${route.ecoScore}/100</div>
                <div>${featuresHtml}</div>
            </div>
            <div class="route-steps">
                ${stepsHtml}
            </div>
        `;
        
        div.onclick = () => {
            document.querySelectorAll('.route-option').forEach(item => {
                item.style.background = '#fff';
            });
            div.style.background = '#f0f5ff';
            highlightRoute(route, index);
        };
        
        container.appendChild(div);
    });
}