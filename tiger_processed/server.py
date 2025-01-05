from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import logging
import time
from typing import Dict
from shapely.geometry import box, shape
import asyncio
import aiofiles
from cachetools import TTLCache, LRUCache

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create rate limiter
REQUEST_LIMIT = 10  # requests per second
request_times = {}

# Create caches
CACHE_TTL = 300  # 5 minutes
tile_cache = TTLCache(maxsize=100, ttl=CACHE_TTL)
boundary_cache = LRUCache(maxsize=1)

# Semaphore for limiting concurrent file operations
file_semaphore = asyncio.Semaphore(4)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_methods=["*"],
    allow_headers=["*"]
)

# Configure static file directory
ROADS_DIR = Path("ROADS").absolute()


async def load_tile_boundaries():
    """Load and cache the tile boundaries"""
    if 'boundaries' in boundary_cache:
        return boundary_cache['boundaries']

    try:
        boundaries_file = ROADS_DIR / "tile_boundaries.geojson"
        async with aiofiles.open(boundaries_file, mode='r') as f:
            content = await f.read()
            geojson = json.loads(content)

        tile_index = {}
        for feature in geojson['features']:
            code = feature['properties'].get('code', 'unknown')
            geom = shape(feature['geometry'])
            tile_index[code] = geom

        boundary_cache['boundaries'] = tile_index
        return tile_index

    except Exception as e:
        logger.error(f"Error loading boundaries: {e}")
        raise


@app.post("/find_tiles")
async def find_tiles(bounds: Dict, request: Request):
    """Find tiles that intersect with given bounds"""
    try:
        # Check rate limit
        client_ip = request.client.host
        current_time = time.time()
        if client_ip in request_times:
            if current_time - request_times[client_ip] < 1 / REQUEST_LIMIT:
                raise HTTPException(status_code=429, detail="Too many requests")
        request_times[client_ip] = current_time

        # Generate cache key
        cache_key = f"{bounds['west']:.3f},{bounds['south']:.3f},{bounds['east']:.3f},{bounds['north']:.3f}"
        if cache_key in tile_cache:
            logger.debug(f"Cache hit for bounds: {cache_key}")
            return tile_cache[cache_key]

        logger.debug(f"Cache miss for bounds: {cache_key}")
        tile_index = await load_tile_boundaries()
        viewport = box(bounds['west'], bounds['south'], bounds['east'], bounds['north'])

        matching_tiles = []
        roads_dir = ROADS_DIR

        # Process tiles with concurrency control
        async with file_semaphore:
            for code, geometry in tile_index.items():
                if geometry.intersects(viewport):
                    pattern = f"tl_2023_*_roads.{code}.topojson"
                    matches = list(roads_dir.glob(pattern))
                    matching_tiles.extend(str(m.name) for m in matches)

        # Cache results
        tile_cache[cache_key] = matching_tiles
        logger.debug(f"Found {len(matching_tiles)} matching tiles")
        return matching_tiles

    except Exception as e:
        logger.error(f"Error in find_tiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tile_boundaries.geojson")
async def get_boundaries():
    """Serve the tile boundaries file"""
    try:
        file_path = ROADS_DIR / "tile_boundaries.geojson"
        async with file_semaphore, aiofiles.open(file_path, mode='r') as f:
            content = await f.read()
            return Response(
                content=content,
                media_type='application/json',
                headers={
                    'Cache-Control': f'public, max-age={CACHE_TTL}',
                    'Access-Control-Allow-Origin': '*'
                }
            )
    except Exception as e:
        logger.error(f"Error serving boundaries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/{filename:path}")
async def get_file(filename: str):
    """Serve static files with improved concurrency control"""
    try:
        async with file_semaphore:
            file_path = ROADS_DIR / filename
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")

            async with aiofiles.open(file_path, mode='rb') as f:
                content = await f.read()

            return Response(
                content=content,
                media_type='application/json',
                headers={
                    'Cache-Control': f'public, max-age={CACHE_TTL}',
                    'Access-Control-Allow-Origin': '*'
                }
            )
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files for direct access
app.mount("/", StaticFiles(directory=str(ROADS_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    print("\n=== Server Configuration ===")
    print(f"Serving files from: {ROADS_DIR}")
    uvicorn.run(app, host="127.0.0.1", port=8000, access_log=False)