(function () {
    const state = {
        layers: [],
        svg: null,
        projection: null,
        path: null,
        zoom: null
    };

    function initMap() {
        console.log('Initializing map...');
        const width = window.innerWidth;
        const height = window.innerHeight;

        state.svg = d3.select('#map')
            .attr('width', width)
            .attr('height', height);

        state.projection = d3.geoAlbersUsa()
            .fitSize([width, height], { type: "Sphere" });

        state.path = d3.geoPath().projection(state.projection);

        state.zoom = d3.zoom()
            .scaleExtent([1, 8])
            .on('zoom', zoomed);

        state.svg.call(state.zoom);

        state.svg.append('g')
            .attr('class', 'zoom-group');

        console.log('Map initialized');
    }

    function zoomed(event) {
        state.svg.select('.zoom-group')
            .attr('transform', event.transform);
    }

    function handleDrop(event) {
        console.log('File drop detected', event);
        console.log('DataTransfer items:', event.dataTransfer.items);
        console.log('DataTransfer files:', event.dataTransfer.files);

        event.preventDefault();
        event.stopPropagation();

        document.getElementById('drop-overlay').classList.add('hidden');

        // Try both items and files APIs
        let files = [];
        if (event.dataTransfer.items) {
            console.log('Using items API');
            files = Array.from(event.dataTransfer.items)
                .filter(item => {
                    console.log('Item:', item, 'Kind:', item.kind, 'Type:', item.type);
                    return item.kind === 'file';
                })
                .map(item => {
                    const file = item.getAsFile();
                    console.log('Converted to file:', file);
                    return file;
                });
        } else {
            console.log('Using files API');
            files = Array.from(event.dataTransfer.files);
        }

        console.log('Processed files:', files);

        const topojsonFiles = files.filter(file => {
            console.log('Checking file:', file.name, file.type);
            return file.name.toLowerCase().endsWith('.topojson');
        });

        console.log('Filtered TopoJSON files:', topojsonFiles);
        topojsonFiles.forEach(loadTopoJSON);
    }

    async function loadTopoJSON(file) {
        console.log(`Loading file: ${file.name}`);
        const reader = new FileReader();
        const progressBar = document.getElementById('progress-bar');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        progressBar.classList.remove('hidden');

        try {
            const text = await new Promise((resolve, reject) => {
                reader.onload = e => resolve(e.target.result);
                reader.onerror = e => reject(e);
                reader.readAsText(file);
            });

            console.log('File read complete, parsing JSON...');
            const topology = JSON.parse(text);

            console.log('Topology loaded:', topology);

            const layerType = file.name.split('_').pop().split('.')[0].toUpperCase();
            console.log(`Layer type detected: ${layerType}`);

            progressBar.classList.add('hidden');
            addLayer(topology, file.name, layerType);
            fitToData();
        } catch (error) {
            console.error('Error loading TopoJSON:', error);
            progressBar.classList.add('hidden');
        }
    }

    function addLayer(topology, filename, layerType) {
        console.log(`Adding layer: ${filename} (${layerType})`);
        const geometries = [];

        for (let key in topology.objects) {
            console.log(`Processing topology object: ${key}`);
            const geojson = topojson.feature(topology, topology.objects[key]);
            geometries.push(geojson);
        }

        const layer = {
            id: Date.now(),
            name: filename,
            type: layerType,
            data: geometries
        };

        state.layers.push(layer);
        console.log(`Layer added, now rendering...`);
        renderLayer(layer);
        updateLayersList();
    }

    function renderLayer(layer) {
        console.log(`Rendering layer: ${layer.name}`);
        const layerGroup = state.svg.select('.zoom-group')
            .append('g')
            .attr('class', `layer-${layer.id}`);

        layer.data.forEach((geojson, idx) => {
            console.log(`Rendering geometry set ${idx + 1}/${layer.data.length}`);
            layerGroup.selectAll('path')
                .data(geojson.features)
                .enter()
                .append('path')
                .attr('d', state.path)
                .attr('class', () => layer.type);
        });
        console.log('Layer render complete');
    }

    function removeLayer(layerId) {
        console.log(`Removing layer: ${layerId}`);
        state.svg.select(`.layer-${layerId}`).remove();
        state.layers = state.layers.filter(layer => layer.id !== layerId);
        updateLayersList();
        fitToData();
    }

    function updateLayersList() {
        console.log('Updating layers list');
        const list = document.getElementById('layers-list');
        list.innerHTML = '';

        state.layers.forEach(layer => {
            const li = document.createElement('li');
            li.className = 'layer-item';
            li.innerHTML = `
              <span>${layer.name} (${layer.type})</span>
              <button class="delete-layer" data-id="${layer.id}">Delete</button>
          `;
            list.appendChild(li);
        });
    }

    function fitToData() {
        if (state.layers.length === 0) return;

        console.log('Fitting view to data extents');
        const features = state.layers.flatMap(layer =>
            layer.data.flatMap(geojson => geojson.features)
        );

        const bounds = d3.geoBounds({
            type: 'FeatureCollection',
            features: features.filter(f => f && f.geometry && !isNaN(f.geometry.coordinates[0]))
        });
        console.log('Raw bounds:', bounds);

        if (!bounds || bounds.some(coord => coord.some(isNaN))) {
            console.error('Invalid bounds detected, using default USA bounds');
            state.projection.fitSize([window.innerWidth, window.innerHeight], {
                type: "Feature",
                geometry: {
                    type: "Point",
                    coordinates: [-98.5795, 39.8283]
                }
            });
        } else {
            const [[x0, y0], [x1, y1]] = bounds;
            const width = window.innerWidth;
            const height = window.innerHeight;
            const padding = Math.min(width, height) * 0.1;

            try {
                state.projection.fitExtent(
                    [[padding, padding], [width - padding, height - padding]],
                    {
                        type: 'Feature',
                        geometry: {
                            type: 'MultiPoint',
                            coordinates: [[x0, y0], [x1, y1]]
                        }
                    }
                );
            } catch (e) {
                console.error('Error fitting projection:', e);
            }
        }

        state.svg.selectAll('path')
            .attr('d', state.path);

        console.log('View updated');
    }
    
    function initEventListeners() {
        console.log('Initializing event listeners');
        const mapContainer = document.getElementById('map-container');
        const dropOverlay = document.getElementById('drop-overlay');

        // Prevent default drag behavior on the entire document
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);

        document.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);

        // Map container specific handlers
        mapContainer.addEventListener('dragenter', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Drag enter detected');
            dropOverlay.classList.remove('hidden');
        }, false);

        mapContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Drag over detected');
            dropOverlay.classList.remove('hidden');
        }, false);

        dropOverlay.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Drag leave detected');
            dropOverlay.classList.add('hidden');
        }, false);

        dropOverlay.addEventListener('drop', handleDrop, false);
        mapContainer.addEventListener('drop', handleDrop, false);

        document.getElementById('layers-list').addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-layer')) {
                removeLayer(parseInt(e.target.dataset.id));
            }
        });

        window.addEventListener('resize', () => {
            console.log('Window resize detected');
            state.svg
                .attr('width', window.innerWidth)
                .attr('height', window.innerHeight);
            fitToData();
        });

        console.log('Event listeners initialized');
    }

    function init() {
        console.log('Initializing application');
        initMap();
        initEventListeners();
        console.log('Application ready');
    }

    init();
})();