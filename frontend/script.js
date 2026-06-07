document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const bandsGrid = document.getElementById('bandsGrid');
    const totalBandsCount = document.getElementById('totalBandsCount');
    const searchInput = document.getElementById('searchInput');
    
    // Modals
    const bandModal = document.getElementById('bandModal');
    const logsModal = document.getElementById('logsModal');
    
    // Buttons
    const addBandBtn = document.getElementById('addBandBtn');
    const viewLogsBtn = document.getElementById('viewLogsBtn');
    const rockViewBtn = document.getElementById('rockViewBtn');
    const metalViewBtn = document.getElementById('metalViewBtn');
    const allViewBtn = document.getElementById('allViewBtn');
    
    const closeModalBtns = document.querySelectorAll('.close-modal, .close-logs-modal');
    
    // Forms
    const bandForm = document.getElementById('bandForm');
    const albumSection = document.getElementById('albumSection');
    const addAlbumFieldBtn = document.getElementById('addAlbumFieldBtn');
    const albumsList = document.getElementById('albumsList');

    const API_BASE = '';

    // Initialize View
    fetchBands();

    // Event Listeners
    addBandBtn.addEventListener('click', () => openModal('add'));
    viewLogsBtn.addEventListener('click', openLogsModal);
    searchInput.addEventListener('input', (e) => fetchBands(e.target.value));
    
    rockViewBtn.addEventListener('click', () => fetchView('rock'));
    metalViewBtn.addEventListener('click', () => fetchView('metal'));
    allViewBtn.addEventListener('click', () => {
        searchInput.value = '';
        fetchBands();
    });

    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            bandModal.style.display = 'none';
            logsModal.style.display = 'none';
        });
    });

    bandForm.addEventListener('submit', handleBandSubmit);

    addAlbumFieldBtn.addEventListener('click', () => {
        const div = document.createElement('div');
        div.className = 'album-entry p-2 border-bottom';
        div.innerHTML = `
            <input type="text" placeholder="Album Title" class="album-title">
            <input type="date" class="album-date">
        `;
        albumsList.appendChild(div);
    });

    // Core Functions
    async function fetchBands(query = '') {
        const url = query ? `${API_BASE}/bands?q=${encodeURIComponent(query)}` : `${API_BASE}/bands`;
        try {
            const response = await fetch(url);
            const data = await response.json();
            renderBands(data);
        } catch (error) {
            console.error("Error fetching bands:", error);
        }
    }

    async function fetchView(genre) {
        try {
            const response = await fetch(`${API_BASE}/views/${genre}_bands`);
            const data = await response.json();
            renderBands(data, true);
        } catch (error) {
            console.error("Error fetching view:", error);
        }
    }

    function renderBands(bands, isView = false) {
        bandsGrid.innerHTML = '';
        totalBandsCount.textContent = bands.length;

        if (bands.length === 0) {
            bandsGrid.innerHTML = '<p>No bands found. Add some!</p>';
            return;
        }

        let counter = 1;
        bands.forEach(band => {
            const genreLower = (band.genre || '').toLowerCase();
            let themeClass = 'theme-rock';
            if (genreLower === 'electronic') themeClass = 'theme-electronic';
            if (genreLower === 'metal') themeClass = 'theme-metal';
            if (genreLower === 'hip-hop') themeClass = 'theme-hip-hop';

            const albumsText = isView ? '' : `<p class="albums-info">Albums: ${band.albums ? band.albums.length : 0}</p>`;
            
            // Format number as 01, 02
            const numLabel = counter.toString().padStart(2, '0');

            const card = document.createElement('div');
            card.className = `card ${themeClass}`;
            card.innerHTML = `
                <div class="card-badge">
                    <span>${numLabel}</span>
                </div>
                <div class="card-content">
                    <h3 class="card-title">${band.name}</h3>
                    <p class="card-desc">Genre: ${band.genre}</p>
                    ${albumsText}
                </div>
                <div class="card-actions">
                    <button class="action-btn edit-btn" onclick="editBand(${band.id}, '${band.name.replace(/'/g, "\\'")}', '${band.genre}')">✏</button>
                    <button class="action-btn delete-btn" onclick="deleteBand(${band.id})">🗑</button>
                </div>
            `;
            bandsGrid.appendChild(card);
            counter++;
        });
    }

    function openModal(mode, id = null, name = '', genre = 'Rock') {
        const title = document.getElementById('modalTitle');
        const bandIdField = document.getElementById('bandId');
        const bandNameField = document.getElementById('bandName');
        const bandGenreField = document.getElementById('bandGenre');

        bandIdField.value = id || '';
        bandNameField.value = name;
        bandGenreField.value = genre;

        if (mode === 'add') {
            title.textContent = 'Add New Band';
            albumSection.style.display = 'block'; // Show album section
        } else {
            title.textContent = 'Edit Band';
            albumSection.style.display = 'none'; // Hide album section on edit
        }

        bandModal.style.display = 'flex';
    }

    // Expose edit and delete to local scope as they are called in HTML string
    window.editBand = (id, name, genre) => {
        openModal('edit', id, name, genre);
    };

    window.deleteBand = async (id) => {
        if (!confirm('Are you sure you want to delete this band?')) return;
        try {
            await fetch(`${API_BASE}/bands/${id}`, { method: 'DELETE' });
            fetchBands(); // Refresh
        } catch (error) {
            console.error("Error deleting band", error);
        }
    };

    async function handleBandSubmit(e) {
        e.preventDefault();
        
        const id = document.getElementById('bandId').value;
        const name = document.getElementById('bandName').value;
        const genre = document.getElementById('bandGenre').value;
        
        if (id) {
            // Update
            try {
                await fetch(`${API_BASE}/bands/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, genre })
                });
                bandModal.style.display = 'none';
                fetchBands();
            } catch (error) {
                console.error("Error updating", error);
            }
        } else {
            // Create
            const albumInputs = document.querySelectorAll('.album-entry');
            const albums = [];
            albumInputs.forEach(entry => {
                const title = entry.querySelector('.album-title').value;
                const release_date = entry.querySelector('.album-date').value;
                if (title && release_date) {
                    albums.push({ title, release_date });
                }
            });

            const bandData = { name, genre, albums: albums.length > 0 ? albums : undefined };

            try {
                await fetch(`${API_BASE}/bands`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bandData)
                });
                bandModal.style.display = 'none';
                bandForm.reset();
                fetchBands();
            } catch (error) {
                console.error("Error creating", error);
            }
        }
    }

    async function openLogsModal() {
        try {
            const response = await fetch(`${API_BASE}/logs`);
            const logs = await response.json();
            const tbody = document.getElementById('logsTableBody');
            tbody.innerHTML = '';
            
            if(logs.length === 0){
                tbody.innerHTML = '<tr><td colspan="3">No logs available. Try deleting a band!</td></tr>';
            } else {
                logs.forEach(log => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${log.id}</td>
                        <td>${log.band_name}</td>
                        <td>${new Date(log.timestamp).toLocaleString()}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
            logsModal.style.display = 'flex';
        } catch (error) {
            console.error("Error fetching logs", error);
        }
    }
});
