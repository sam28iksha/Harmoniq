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

    // Stored Procedure elements
    const callProcBtn = document.getElementById('callProcBtn');
    const procGenreSelect = document.getElementById('procGenreSelect');
    const procResult = document.getElementById('procResult');
    const transferBtn = document.getElementById('transferBtn');
    const transferResult = document.getElementById('transferResult');

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

    // Stored Procedure: get_bands_by_genre
    callProcBtn.addEventListener('click', async () => {
        const genre = procGenreSelect.value;
        try {
            const response = await fetch(`${API_BASE}/procedures/bands_by_genre/${genre}`);
            const data = await response.json();
            if (data.length === 0) {
                procResult.innerHTML = '<em>No bands found for this genre.</em>';
            } else {
                procResult.innerHTML = data.map(b =>
                    `<div class="proc-item">🎸 <b>${b.band_name}</b> (${b.band_genre}) — ${b.album_count} album(s)</div>`
                ).join('');
            }
        } catch (error) {
            procResult.innerHTML = `<em style="color:red;">Error: ${error.message}</em>`;
        }
    });

    // Stored Procedure: transfer_albums
    transferBtn.addEventListener('click', async () => {
        const fromId = document.getElementById('fromBandId').value;
        const toId = document.getElementById('toBandId').value;
        if (!fromId || !toId) {
            transferResult.innerHTML = '<em style="color:red;">Please enter both band IDs.</em>';
            return;
        }
        try {
            const response = await fetch(`${API_BASE}/procedures/transfer_albums?from_band_id=${fromId}&to_band_id=${toId}`, {
                method: 'POST'
            });
            const data = await response.json();
            if (response.ok) {
                transferResult.innerHTML = `<div class="proc-item">✅ Transferred <b>${data.transferred_count}</b> album(s) from <b>${data.from_band}</b> → <b>${data.to_band}</b></div>`;
                fetchBands(); // Refresh
            } else {
                transferResult.innerHTML = `<em style="color:red;">${data.detail}</em>`;
            }
        } catch (error) {
            transferResult.innerHTML = `<em style="color:red;">Error: ${error.message}</em>`;
        }
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

            let albumsText = '';
            if (!isView && band.albums && band.albums.length > 0) {
                const albumNames = band.albums.map(a => a.title).join(', ');
                albumsText = `<p class="albums-info">Albums: ${band.albums.length} — ${albumNames}</p>`;
            } else if (!isView) {
                albumsText = `<p class="albums-info">Albums: 0</p>`;
            }

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
                    ${!isView ? `<p class="band-id-info">ID: ${band.id}</p>` : ''}
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

            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">No logs available. Try adding or deleting a band!</td></tr>';
            } else {
                logs.forEach(log => {
                    const tr = document.createElement('tr');
                    const actionClass = log.action === 'DELETE' ? 'action-delete' : 'action-insert';
                    tr.innerHTML = `
                        <td>${log.id}</td>
                        <td>${log.band_name}</td>
                        <td><span class="${actionClass}">${log.action}</span></td>
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
