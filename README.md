# TIGER/Line Roads Data Downloader

A Python utility for downloading U.S. Census TIGER/Line road shapefiles.

## Overview

This tool downloads road shapefiles from the U.S. Census Bureau's TIGER/Line database. It handles concurrent downloads with retry capabilities and provides detailed logging of the download process.

## Features

- Downloads road shapefiles for all U.S. states and territories
- Concurrent downloading with configurable number of workers
- Automatic retries with exponential backoff
- Detailed logging
- Memory-efficient streaming downloads
- Handles both state and county FIPS codes

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd tiger-data
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```python
from TigerDownloader import TigerDownloader

# Create downloader instance
downloader = TigerDownloader(
    year=2023,              # Year of TIGER/Line data
    max_workers=4,          # Number of concurrent downloads
    retry_count=3,          # Number of retry attempts
    timeout=30              # Download timeout in seconds
)

# Start downloading
downloader.download_roads("./tiger_roads_2023")
```

### Configuration Options

- `year`: The year of TIGER/Line data to download (default: 2023)
- `max_workers`: Number of concurrent downloads (default: 4)
- `retry_count`: Number of retry attempts for failed downloads (default: 3)
- `timeout`: Download timeout in seconds (default: 30)
- `chunk_size`: Size of download chunks in bytes (default: 8192)

## File Structure

Downloaded files follow the naming convention:
```
tl_YYYY_XXXXX_roads.zip
```
Where:
- `YYYY`: Year (e.g., 2023)
- `XXXXX`: FIPS code (state and county)

## Data Volume

- Approximately 3,233 individual files
- File sizes range from ~12KB to ~23MB
- Total download size: ~4.8GB

## Requirements

- Python 3.6+
- requests library

## Error Handling

The downloader includes:
- Automatic retries with exponential backoff
- Detailed error logging
- Preservation of successful downloads even if some fail
- Configurable timeout and retry settings

## Notes

- Ensure sufficient disk space (~5GB recommended)
- Download speed will depend on your internet connection and chosen number of workers
- Consider bandwidth limitations when configuring concurrent downloads

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Your chosen license]

# TIGER/Line Data Types

## Relationship Tables (Non-Spatial)
Tables containing attributes but no geometry. These link to spatial features via IDs.
- ADDR - Address Range Relations
- ADDRFEAT - Address Feature Relations  
- ADDRFN - Address Feature Names
- FACES - Census Block Face Relations
- FACESAH - Area Landmark Block Face Relations
- FACESAL - Area Landmark Face Relations
- FACESMIL - Military Block Face Relations
- FEATNAMES - Geographic Feature Names
- TBG - TIGER/Line Block Group Relations

## Point Features (Shapefiles)
Features represented as single coordinate points.
- POINTLM - Point Landmarks

## Polyline Features (Shapefiles)
Features represented as connected line segments.
- EDGES - Base Network Edges
- LINEARWATER - Rivers and Streams
- PRIMARYROADS - Major Roads
- PRISECROADS - Primary and Secondary Roads
- RAILS - Railroads 
- ROADS - All Roads
- AIANNH - American Indian/Alaska Native/Native Hawaiian Areas
- AITSN - American Indian Tribal Subdivision
- ANRC - Alaska Native Regional Corporation
- BG - Block Groups
- CBSA - Core Based Statistical Areas
- CD - Congressional Districts
- CONCITY - Consolidated Cities
- COUNTY - Counties
- COUSUB - County Subdivisions
- CSA - Combined Statistical Areas
- ELSD - School Districts (Elementary)
- ESTATE - Estates (Virgin Islands)
- INTERNATIONALBOUNDARY - US International Borders
- METDIV - Metropolitan Divisions
- MIL - Military Installations
- PLACE - Places (Cities, Towns, etc.)
- PUMA - Public Use Microdata Areas
- SCSD - School Districts (Secondary)
- SDADM - School Districts (Unified)
- SLDL - State Legislative Districts - Lower
- SLDU - State Legislative Districts - Upper
- STATE - States and Equivalents
- SUBBARRIO - Sub-barrios (Puerto Rico)
- TABBLOCK20 - Census Blocks (2020)
- TRACT - Census Tracts
- TTRACT - Tribal Census Tracts
- UAC - Urban Areas
- UNSD - School Districts (Unified)
- ZCTA520 - ZIP Code Tabulation Areas

## Polygon Features (Shapefiles)
Features represented as closed shapes with area.
- AREALM - Area Landmarks
- AREAWATER - Water Bodies
- COASTLINE - Coastline


To serve local files, you'll need a simple web server. You could use Python's built-in server:
cd D:\code\python\tiger-data
python -m http.server 8000
