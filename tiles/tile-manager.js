const TileManager = (function() {
    // Private variables
    let visibleTiles = new Set();
    let loadedTiles = new Map();
    let g = null;
    let path = null;
    let projection = null;
    
    // Constants
    const ZOOM_THRESHOLD = 10;
    const SERVER_URL = "http://127.0.0.1:8000";
    const MAX_CONCURRENT_OPERATIONS = 4;
    
    async function initialize() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        projection = d3.geoMercator()
            .scale(width / 2 / Math.PI)
            .translate([width / 2, height / 2]);

        path = d3.geoPath().projection(projection);
        
        const svg = d3.select('#map')
            .append('svg')
            .attr('width', width)
            .attr('height', height);
            
        g = svg.append('g');
        
        const zoom = d3.zoom()
            .scaleExtent([1, 2048])
            .on('zoom', handleZoom);
            
        svg.call(zoom);
        
        // Load world map first
        try {
            const world = await d3.json("land-110m.json");
            g.append("path")
                .datum(topojson.feature(world, world.objects.land))
                .attr("class", "background")
                .attr("d", path);
        } catch (error) {
            console.error("Error loading world map:", error);
        }
        
        // Then initialize boundaries
        await loadBoundaries();
        
        // Initialize view
        updateTiles(d3.zoomIdentity);
    }
    
    async function loadBoundaries() {
        try {
            console.log("Loading boundaries...");
            const result = await fetch(`${SERVER_URL}/tile_boundaries.geojson`);
            if (!result.ok) throw new Error(`HTTP error! status: ${result.status}`);
            
            const boundaries = await result.json();
            console.log("Boundaries loaded:", boundaries.features.length, "features");
            
            // Add boundary paths
            g.selectAll("path.tile-boundary")
                .data(boundaries.features)
                .enter()
                .append("path")
                .attr("class", "tile-boundary")
                .attr("d", path)
                .attr("vector-effect", "non-scaling-stroke")
                .attr("fill", "none")
                .attr("stroke", "#666")
                .attr("stroke-width", "0.5px");

            // Add labels
            g.selectAll("text.tile-label")
                .data(boundaries.features)
                .enter()
                .append("text")
                .attr("class", "tile-label")
                .attr("text-anchor", "middle")
                .attr("alignment-baseline", "middle")
                .attr("vector-effect", "non-scaling-size")
                .attr("font-size", "0.25px")
                .attr("fill", "#666")
                .text(d => d.properties.code)
                .attr("transform", d => {
                    const centroid = path.centroid(d);
                    return `translate(${centroid[0]},${centroid[1]})`;
                });
                
            console.log("Boundaries rendered");
        } catch (error) {
            console.error("Error loading boundaries:", error);
        }
    }
    
    function handleZoom(event) {
        if (!g) return;
        
        g.attr('transform', event.transform);
        const bounds = calculateBounds(event.transform);
        const zoom = Math.log2(event.transform.k);
        console.log('Current zoom level:', zoom);
        
        if (zoom >= ZOOM_THRESHOLD) {
            updateTiles(bounds, zoom);
        }
    }
    
    function calculateBounds(transform) {
        if (!projection) return null;

        const width = window.innerWidth;
        const height = window.innerHeight;

        const topLeft = [0, 0];
        const bottomRight = [width, height];

        const invertedTopLeft = transform.invert(topLeft);
        const invertedBottomRight = transform.invert(bottomRight);

        const geoTopLeft = projection.invert(invertedTopLeft);
        const geoBottomRight = projection.invert(invertedBottomRight);

        return {
            west: geoTopLeft[0],
            east: geoBottomRight[0],
            north: geoTopLeft[1],
            south: geoBottomRight[1]
        };
    }
    
    const debouncedUpdateTiles = debounce(async function(bounds, zoom) {
        if (zoom < ZOOM_THRESHOLD) return;
        
        try {
            const result = await fetch(`${SERVER_URL}/find_tiles`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bounds)
            });
            
            if (!result.ok) throw new Error(`HTTP error! status: ${result.status}`);
            
            const filenames = await result.json();
            console.log(`Found ${filenames.length} tiles to load`);
            
            const newVisibleTiles = new Set(filenames);
            
            // Remove tiles that are no longer visible
            const tilesToRemove = new Array();
            loadedTiles.forEach((_, filename) => {
                if (!newVisibleTiles.has(filename)) {
                    tilesToRemove.push(filename);
                }
            });
            
            tilesToRemove.forEach(filename => {
                loadedTiles.delete(filename);
                const safeClassName = sanitizeFilename(filename);
                d3.selectAll(`.roads-${safeClassName}`).remove();
                console.log(`Removed tile: ${filename}`);
            });
            
            // Load new tiles with concurrency control
            const tilesToLoad = filenames.filter(f => !loadedTiles.has(f));
            await loadTilesWithConcurrency(tilesToLoad, MAX_CONCURRENT_OPERATIONS);
            
            visibleTiles = newVisibleTiles;
            
        } catch (error) {
            console.error("Error updating tiles:", error);
        }
    }, 300);
    
    function updateTiles(bounds, zoom) {
        if (!bounds) return;
        debouncedUpdateTiles(bounds, zoom);
    }
    
    async function loadTilesWithConcurrency(tiles, concurrency) {
        const queue = [...tiles];
        const inProgress = new Set();
        
        while (queue.length > 0 || inProgress.size > 0) {
            while (inProgress.size < concurrency && queue.length > 0) {
                const filename = queue.shift();
                inProgress.add(filename);
                
                loadTile(filename).finally(() => {
                    inProgress.delete(filename);
                });
            }
            
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }
    
    async function loadTile(filename) {
        try {
            console.log(`Loading tile: ${filename}`);
            const result = await fetch(`${SERVER_URL}/${filename}`);
            if (!result.ok) throw new Error(`HTTP error! status: ${result.status}`);
            
            const data = await result.json();
            if (!loadedTiles.has(filename)) {
                renderTile(data, filename);
                loadedTiles.set(filename, true);
                console.log(`Rendered tile: ${filename}`);
            }
        } catch (error) {
            console.error(`Error loading tile ${filename}:`, error);
        }
    }
    
    function sanitizeFilename(filename) {
        // Replace dots and other invalid characters with underscores
        return filename.replace(/[^a-zA-Z0-9-]/g, '_');
    }

    function renderTile(data, filename) {
        if (!g || !path) return;
        
        const features = data.type === 'Topology' 
            ? topojson.feature(data, data.objects.data).features 
            : [data];
            
        const safeClassName = sanitizeFilename(filename);
        g.selectAll(`.roads-${safeClassName}`)
            .data(features)
            .enter()
            .append('path')
            .attr('class', `roads roads-${safeClassName}`)
            .attr('d', path);
    }
    
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    function cleanup() {
        if (g) {
            g.selectAll('*').remove();
            g = null;
        }
        visibleTiles = new Set();
        loadedTiles = new Map();
    }
    
    // Public API
    return {
        initialize,
        cleanup
    };
})();

// Add window load event listener
window.addEventListener('load', function() {
    // Initialize the tile manager
    TileManager.initialize().catch(error => {
        console.error("Failed to initialize TileManager:", error);
    });
});

// Add cleanup on window unload
window.addEventListener('unload', function() {
    TileManager.cleanup();
});