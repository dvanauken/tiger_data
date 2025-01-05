from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import logging
from typing import Dict
from shapely.geometry import box, shape

logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more info
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Cache for tile boundaries
tile_index = None


def load_tile_boundaries():
    """Load and cache the tile boundaries"""
    global tile_index
    if tile_index is None:
        try:
            with open("ROADS/tile_boundaries.geojson") as f:
                geojson = json.load(f)
                # Debug output
                logger.debug(f"GeoJSON features: {len(geojson['features'])}")
                logger.debug(f"First feature properties: {geojson['features'][0]['properties']}")

                tile_index = {}
                for feature in geojson['features']:
                    code = feature['properties'].get('code', 'unknown')
                    geom = shape(feature['geometry'])
                    tile_index[code] = geom
                    logger.debug(f"Loaded tile {code}: bounds = {geom.bounds}")

                logger.info(f"Successfully loaded {len(tile_index)} tiles")
        except Exception as e:
            logger.error(f"Error loading boundaries: {e}")
            raise


@app.post("/find_tiles")
async def find_tiles(bounds: Dict):
    """Find tiles that intersect with the given bounds"""
    try:
        # Load boundaries if not loaded
        if tile_index is None:
            load_tile_boundaries()

        # Create viewport box
        viewport = box(
            bounds['west'],
            bounds['south'],
            bounds['east'],
            bounds['north']
        )

        logger.info(f"Searching viewport: {viewport.bounds}")

        # Find intersecting tiles
        matching_tiles = []
        intersecting_count = 0
        missing_count = 0

        for code, geometry in tile_index.items():
            if geometry.intersects(viewport):
                intersecting_count += 1
                filename = f"tl_2023_01001_roads.{code}.topojson"
                file_path = Path("ROADS") / filename

                if file_path.exists():
                    matching_tiles.append(filename)
                else:
                    missing_count += 1
                    # Log every 100th missing file to avoid spam
                    if missing_count % 100 == 0:
                        logger.warning(f"Missing files count: {missing_count}")
                        logger.warning(f"Sample missing file: {file_path.absolute()}")

        logger.info(f"Summary: Found {len(matching_tiles)} files out of {intersecting_count} intersecting tiles")
        if len(matching_tiles) > 0:
            logger.info(f"Sample found file: {matching_tiles[0]}")
        if missing_count > 0:
            logger.warning(f"Total missing files: {missing_count}")

        return matching_tiles

    except Exception as e:
        logger.error(f"Error in find_tiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files
app.mount("/", StaticFiles(directory="ROADS", html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    print("\n=== Server Configuration ===")
    print(f"Directory: {Path('ROADS').absolute()}")

    # Preload and verify tile index
    load_tile_boundaries()

    uvicorn.run(app, host="127.0.0.1", port=8000)