import os
import json
import logging
from pathlib import Path


def generate_manifest():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Define paths
    base_dir = Path("tiger_processed/ROADS")
    manifest_file = base_dir / "manifest.json"

    try:
        # Ensure directory exists
        if not base_dir.exists():
            logger.error(f"Directory not found: {base_dir}")
            return

        # Scan for topojson files
        files = []
        for file in base_dir.glob("*.topojson"):
            files.append(file.name)

        logger.info(f"Found {len(files)} topojson files")

        # Write manifest
        with open(manifest_file, 'w') as f:
            json.dump(files, f, indent=2)

        logger.info(f"Manifest written to {manifest_file}")

    except Exception as e:
        logger.error(f"Error generating manifest: {e}")


if __name__ == "__main__":
    generate_manifest()