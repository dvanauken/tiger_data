from ftplib import FTP, error_perm
import geopandas as gpd
import topojson
import os
import json
import zipfile
import io
import shutil
from tqdm import tqdm
import asyncio
import time
import random
from functools import wraps
import csv
import logging
from datetime import datetime
import aiohttp
from typing import Dict, Any, Optional
import pygeohash as gh

from tiger_types import TigerLayer, TigerLayerType, TigerGeometryType
from processors import get_processor

class TigerProcessor:
    def __init__(self, tolerance: float = 0.001):
        self.ftp_host = 'ftp2.census.gov'
        self.https_host = 'www2.census.gov'
        self.base_path = '/geo/tiger/TIGER2023'
        self.output_dir = "./tiger_processed"
        self.tolerance = tolerance

        # Setup logging and directories
        self._setup_environment()
        self.processed_files = self._load_processed_files()
        self.connect_ftp()

    def _setup_environment(self):
        """Setup logging and directory structure"""
        os.makedirs(self.output_dir, exist_ok=True)

        log_dir = os.path.join(self.output_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            filename=os.path.join(log_dir, f'tiger_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.log_file = os.path.join(self.output_dir, "processed_files.csv")

    def _load_processed_files(self) -> set:
        """Load record of processed files"""
        if not os.path.exists(self.log_file):
            # Create new file with headers
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['directory', 'filename', 'status', 'timestamp', 'protocol'])
            return set()

        try:
            with open(self.log_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header row
                processed = set()
                for row in reader:
                    if len(row) >= 3 and row[2] == 'success':  # Check row has enough columns
                        processed.add((row[0], row[1]))
                return processed
        except Exception as e:
            logging.error(f"Error reading processed files log: {str(e)}")
            # If there's any error reading the file, backup the old one and start fresh
            if os.path.exists(self.log_file):
                backup = f"{self.log_file}.bak.{int(time.time())}"
                os.rename(self.log_file, backup)
                logging.info(f"Backed up problematic log file to {backup}")

            # Create new file
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['directory', 'filename', 'status', 'timestamp', 'protocol'])
            return set()

    def _log_processed_file(self, directory: str, filename: str, status: str, protocol: str = 'FTP'):
        """Log file processing status"""
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                directory,
                filename,
                status,
                time.strftime('%Y-%m-%d %H:%M:%S'),
                protocol
            ])
        logging.info(f"{directory}/{filename}: {status} via {protocol}")

    def connect_ftp(self):
        """Establish FTP connection"""
        try:
            self.ftp = FTP(self.ftp_host)
            self.ftp.login()
            self.ftp.cwd(self.base_path)
        except Exception as e:
            logging.error(f"FTP connection error: {str(e)}")
            raise

    async def download_https(self, directory: str, filename: str) -> io.BytesIO:
        """Download file via HTTPS"""
        https_url = f"https://{self.https_host}{self.base_path}/{directory}/{filename}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(https_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        return io.BytesIO(content)
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            logging.warning(f"HTTPS download failed for {filename}: {str(e)}")
            raise

    async def process_layer(self, directory: str, filename: str) -> Dict[str, Any]:
        """Process a single TIGER/Line layer file"""
        if (directory, filename) in self.processed_files:
            logging.info(f"Skipping already processed: {filename}")
            return {'success': True, 'file': filename, 'status': 'skipped'}

        try:
            # Identify layer type
            layer = TigerLayer.from_directory_name(directory)

            # Skip relationship files for now
            if layer.layer_type == TigerLayerType.RELATIONSHIP:
                return {
                    'success': True,
                    'file': filename,
                    'status': 'skipped_relationship'
                }

            # Process spatial files
            output_path = await self._process_spatial_file(layer, directory, filename)

            self._log_processed_file(directory, filename, 'success')
            self.processed_files.add((directory, filename))

            return {
                'success': True,
                'file': filename,
                'path': output_path,
                'layer_type': layer.name
            }

        except Exception as e:
            error_msg = f"Error processing {filename}: {str(e)}"
            logging.error(error_msg)
            self._log_processed_file(directory, filename, f'error: {str(e)}')
            return {'success': False, 'file': filename, 'error': str(e)}

    async def _process_spatial_file(self, layer: TigerLayer, directory: str, filename: str) -> str:
        """Process a spatial data file"""
        dir_path = os.path.join(self.output_dir, directory)
        os.makedirs(dir_path, exist_ok=True)
        temp_dir = os.path.join(dir_path, "temp_shp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Download and extract
            response = await self._download_file(directory, filename)
            with zipfile.ZipFile(response) as zip_ref:
                zip_ref.extractall(temp_dir)

            # Process based on geometry type
            processor = get_processor(layer.geometry_type, self.tolerance)
            base_name = filename.replace('.zip', '')
            shp_file = os.path.join(temp_dir, f"{base_name}.shp")

            # Read file and get bounds before processing
            gdf = gpd.read_file(shp_file)
            bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]

            # Calculate geohash for center point of bounds
            center_lat = (bounds[1] + bounds[3]) / 2  # avg of min/max lat
            center_lon = (bounds[0] + bounds[2]) / 2  # avg of min/max lon
            geohash = gh.encode(center_lat, center_lon, precision=5)  # 5 char precision

            # Process geometry
            gdf['geometry'] = gdf['geometry'].simplify(
                tolerance=self.tolerance,
                preserve_topology=True
            )
            topo = topojson.Topology(gdf, prequantize=False)

            # Save with geohash in filename
            output_filename = f"{base_name}.{geohash}.topojson"
            output_path = os.path.join(dir_path, output_filename)

            with open(output_path, 'w') as f:
                json.dump(topo.to_dict(), f)

            return output_path

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


    # async def _process_spatial_file(self, layer: TigerLayer, directory: str, filename: str) -> str:
    #     """Process a spatial data file"""
    #     dir_path = os.path.join(self.output_dir, directory)
    #     os.makedirs(dir_path, exist_ok=True)
    #     temp_dir = os.path.join(dir_path, "temp_shp")
    #     os.makedirs(temp_dir, exist_ok=True)
    #
    #     try:
    #         # Download and extract
    #         response = await self._download_file(directory, filename)
    #
    #         with zipfile.ZipFile(response) as zip_ref:
    #             zip_ref.extractall(temp_dir)
    #
    #         # Process based on geometry type
    #         processor = get_processor(layer.geometry_type, self.tolerance)
    #         base_name = filename.replace('.zip', '')
    #         shp_file = os.path.join(temp_dir, f"{base_name}.shp")
    #
    #         topo_data = processor.process(shp_file)
    #
    #         # Save output
    #         output_filename = f"{base_name}.{str(self.tolerance).replace('.', '')}.topojson"
    #         output_path = os.path.join(dir_path, output_filename)
    #
    #         with open(output_path, 'w') as f:
    #             json.dump(topo_data, f)
    #
    #         return output_path
    #
    #     finally:
    #         if os.path.exists(temp_dir):
    #             shutil.rmtree(temp_dir)

    async def _download_file(self, directory: str, filename: str) -> io.BytesIO:
        """Download file with FTP/HTTPS fallback"""
        try:
            # Try FTP first
            response = io.BytesIO()
            self.ftp.cwd(f'{self.base_path}/{directory}')
            self.ftp.retrbinary(f'RETR {filename}', response.write)
            response.seek(0)
            return response
        except Exception as e:
            # Fallback to HTTPS
            logging.warning(f"FTP download failed, trying HTTPS: {str(e)}")
            return await self.download_https(directory, filename)

    def close(self):
        """Clean up resources"""
        self.ftp.quit()

"""
async def main():
    processor = TigerProcessor(tolerance=0.001)

    try:
        # List all directories
        processor.ftp.cwd(processor.base_path)
        directories = [d for d in processor.ftp.nlst() if '.' not in d]

        # First show directory counts
        for dir in directories:
            processor.ftp.cwd(f'{processor.base_path}/{dir}')
            files = [f for f in processor.ftp.nlst() if f.endswith('.zip')]
            print(f"Directory: {dir}({len(files)})")

        # Process first 3 files from each directory
        for dir in directories:
            processor.ftp.cwd(f'{processor.base_path}/{dir}')
            files = [f for f in processor.ftp.nlst() if f.endswith('.zip')]

            print(f"\nProcessing first 3 files from {dir}:")
            for file in files[:3]:
                result = await processor.process_layer(dir, file)

                if result['success']:
                    if result.get('status') == 'skipped':
                        print(f"⏭ Skipped {file} (already processed)")
                    elif result.get('status') == 'skipped_relationship':
                        print(f"📋 Skipped {file} (relationship file)")
                    else:
                        print(f"✓ Processed {file}")
                        print(f"✓ Saved to {result['path']}")
                else:
                    print(f"✗ Error processing {file}")
                    print(f"✗ Error: {result['error']}")

    finally:
        processor.close()
        """


async def main():
    processor = TigerProcessor(tolerance=0.001)

    try:
        processor.ftp.cwd(processor.base_path)
        directories = [d for d in processor.ftp.nlst() if '.' not in d]

        # Process each layer with tqdm progress bar
        for dir in tqdm(directories, desc="Processing layers", unit="layer"):
            processor.ftp.cwd(f'{processor.base_path}/{dir}')
            files = [f for f in processor.ftp.nlst() if f.endswith('.zip')]

            #for file in files[:3]:
            for file in files:
                result = await processor.process_layer(dir, file)
                if result['success']:
                    if result.get('status') == 'skipped':
                        print(f"⏭ Skipped {file}")
                    elif result.get('status') == 'skipped_relationship':
                        print(f"📋 {file} (relationship file)")
                    else:
                        print(f"✓ {file}")
                else:
                    print(f"✗ Error: {file}")

    finally:
        processor.close()


if __name__ == "__main__":
    asyncio.run(main())