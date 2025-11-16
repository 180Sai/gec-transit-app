// ----- Search Elements -----
let startSearch, endSearch, startSuggestBox, endSuggestBox;

// ----- Initialize Search -----
function initSearch() {
    startSearch = document.getElementById('startSearch');
    endSearch = document.getElementById('endSearch');
    startSuggestBox = document.getElementById('startSuggestBox');
    endSuggestBox = document.getElementById('endSuggestBox');

    startSearch.addEventListener('input', () => handleSearchInput(startSearch, startSuggestBox, 'start'));
    endSearch.addEventListener('input', () => handleSearchInput(endSearch, endSuggestBox, 'end'));

    // Close suggestion boxes when clicking elsewhere
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.suggestions')) {
            startSuggestBox.style.display = 'none';
            endSuggestBox.style.display = 'none';
        }
    });
}

// ----- Search Handlers -----
function handleSearchInput(inputEl, suggestBox, type) {
    const query = inputEl.value.toLowerCase().trim();
    
    if (!query) {
        suggestBox.style.display = 'none';
        return;
    }
    
    const results = getStops().filter(stop => 
        stop.name.toLowerCase().includes(query)
    ).slice(0, 10);
    
    if (results.length === 0) {
        suggestBox.style.display = 'none';
        return;
    }
    
    displaySuggestions(results, suggestBox, type);
}

function displaySuggestions(results, suggestBox, type) {
    suggestBox.innerHTML = '';
    results.forEach(stop => {
        const div = document.createElement('div');
        div.className = 'suggest-item';
        div.textContent = stop.name;
        div.onclick = () => selectStop(stop, type);
        suggestBox.appendChild(div);
    });
    
    suggestBox.style.display = 'block';
}

function selectStop(stop, type) {
    if (type === 'start') {
        setSelectedStart(stop);
        startSearch.value = stop.name;
        startSuggestBox.style.display = 'none';
    } else {
        setSelectedEnd(stop);
        endSearch.value = stop.name;
        endSuggestBox.style.display = 'none';
    }
    
    clearMarkers();
    
    const marker = addMarker(
        parseFloat(stop.latitude), 
        parseFloat(stop.longitude), 
        `<strong>${stop.name}</strong><br>${type === 'start' ? 'Start' : 'End'} location`
    );
    
    if (getSelectedStart() && getSelectedEnd()) {
        fitBoundsToStops(getSelectedStart(), getSelectedEnd());
    } else {
        centerOnLocation(parseFloat(stop.latitude), parseFloat(stop.longitude));
    }
}