import json
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def generate_tile_boundaries():
    base_dir = Path("tiger_processed/ROADS")
    logging.info(f"Starting tile boundary generation from {base_dir}")

    # GeoJSON structure for features
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    file_count = 0
    error_count = 0

    for file in base_dir.glob("*.topojson"):
        try:
            logging.info(f"Processing {file.name}")
            with open(file, 'r') as f:
                data = json.load(f)
                bbox = data.get('bbox')  # [west, south, east, north]
                if bbox:
                    # Extract geohash code from filename
                    geohash = file.name.split('.')[-2]
                    logging.debug(f"Found geohash {geohash} with bounds {bbox}")

                    # Create polygon coordinates for the bounds
                    coordinates = [[
                        [bbox[0], bbox[1]],  # southwest
                        [bbox[0], bbox[3]],  # northwest
                        [bbox[2], bbox[3]],  # northeast
                        [bbox[2], bbox[1]],  # southeast
                        [bbox[0], bbox[1]]  # close the ring
                    ]]

                    # Create GeoJSON feature
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "code": geohash,
                            "center": [
                                (bbox[0] + bbox[2]) / 2,  # lon center for label
                                (bbox[1] + bbox[3]) / 2  # lat center for label
                            ]
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": coordinates
                        }
                    }

                    geojson["features"].append(feature)
                    file_count += 1
                else:
                    logging.warning(f"No bbox found in {file.name}")
                    error_count += 1
        except Exception as e:
            logging.error(f"Error processing {file.name}: {str(e)}")
            error_count += 1

    output_file = base_dir / "tile_boundaries.geojson"
    try:
        with open(output_file, 'w') as f:
            json.dump(geojson, f, indent=2)
        logging.info(f"Successfully created boundary file at {output_file}")
        logging.info(f"Processed {file_count} files with {error_count} errors")
        logging.info(f"Generated {len(geojson['features'])} features")
    except Exception as e:
        logging.error(f"Error writing output file: {str(e)}")


if __name__ == "__main__":
    logging.info("Starting boundary generation process")
    generate_tile_boundaries()
    logging.info("Process complete")