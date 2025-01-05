import json
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def generate_spatial_index():
    base_dir = Path("tiger_processed/ROADS")
    index = {"files": []}

    logging.info(f"Starting index generation from {base_dir}")

    for file in base_dir.glob("*.topojson"):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                bbox = data.get('bbox')  # [west, south, east, north]
                if bbox:
                    index["files"].append({
                        "filename": file.name,
                        "bounds": {
                            "west": bbox[0],
                            "south": bbox[1],
                            "east": bbox[2],
                            "north": bbox[3]
                        }
                    })
                    logging.info(f"Processed {file.name}")
                else:
                    logging.warning(f"No bbox found in {file.name}")
        except Exception as e:
            logging.error(f"Error processing {file.name}: {str(e)}")

    index_file = base_dir / "spatial_index.json"
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2)

    logging.info(f"Index generated with {len(index['files'])} files")
    logging.info(f"Index saved to {index_file}")


if __name__ == "__main__":
    generate_spatial_index()