import asyncio
import csv
import io
import json
import logging
import os
import shutil
import time
import zipfile
from datetime import datetime
from ftplib import FTP
from typing import Dict, Any, Optional

import aiohttp
import geopandas as gpd
import pygeohash as gh
import topojson

from app.server.config.tiger_config import TigerConfig
from app.server.config.layer_config import LayerConfig

class TigerProcessor:
    def __init__(self, config_path: Optional[str] = None):
        self.config = TigerConfig(config_path)
        self._setup_environment()
        self.processed_files = self._load_processed_files()
        self.connect_ftp()

    def _setup_environment(self):
        output_dir = self.config.processing.output_dir
        os.makedirs(output_dir, exist_ok=True)
        log_dir = os.path.join(output_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_dir, f'tiger_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.log_file = os.path.join(output_dir, "processed_files.csv")

    def _load_processed_files(self) -> set:
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['directory', 'filename', 'status', 'timestamp', 'protocol'])
            return set()

        try:
            with open(self.log_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)
                processed = set()
                for row in reader:
                    if len(row) >= 3 and row[2] == 'success':
                        processed.add((row[0], row[1]))
                return processed
        except Exception as e:
            logging.error(f"Error reading processed files log: {str(e)}")
            if os.path.exists(self.log_file):
                backup = f"{self.log_file}.bak.{int(time.time())}"
                os.rename(self.log_file, backup)
                logging.info(f"Backed up problematic log file to {backup}")

            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['directory', 'filename', 'status', 'timestamp', 'protocol'])
            return set()

    def _log_processed_file(self, directory: str, filename: str, status: str, protocol: str = 'FTP'):
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                directory, filename, status,
                time.strftime('%Y-%m-%d %H:%M:%S'), protocol
            ])
        logging.info(f"{directory}/{filename}: {status} via {protocol}")

    def connect_ftp(self):
        try:
            full_url = f"ftp://{self.config.servers.ftp_host}{self.config.servers.base_path}"
            print(f"\nFull FTP URL: {full_url}")
            print(f"Host: {self.config.servers.ftp_host}")
            print(f"Base path: {self.config.servers.base_path}")
            self.ftp = FTP(self.config.servers.ftp_host)
            print("Connected to FTP server")
            self.ftp.login()
            print("Logged in successfully")
            
            path_parts = self.config.servers.base_path.strip('/').split('/')
            current_path = ''
            for part in path_parts:
                next_path = f"{current_path}/{part}" if current_path else f"/{part}"
                print(f"\nTrying to access: {next_path}")
                if current_path:
                    print(f"\nCurrent directory ({current_path}) contents:")
                    try:
                        dir_files = self.ftp.nlst()
                        print("\n".join(sorted(dir_files)))
                    except Exception as e:
                        print(f"Error listing directory: {str(e)}")
                try:
                    self.ftp.cwd(next_path)
                    current_path = next_path
                except Exception as e:
                    print(f"Error accessing {next_path}: {str(e)}")
                    raise
        except Exception as e:
            logging.error(f"FTP connection error: {str(e)}")
            raise

    async def download_https(self, directory: str, filename: str) -> io.BytesIO:
        https_url = f"https://{self.config.servers.https_host}{self.config.servers.base_path}/{directory}/{filename}"
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

    async def _download_file(self, directory: str, filename: str, max_retries: int = 3) -> io.BytesIO:
        retries = 0
        while retries < max_retries:
            try:
                response = io.BytesIO()
                self.ftp.cwd(f'{self.config.servers.base_path}/{directory}')
                size = self.ftp.size(filename)
                size_mb = size / (1024 * 1024)
                print(f"\nDownloading {filename} (Total size: {size_mb:.1f}MB)")
                
                downloaded = 0
                last_time = time.time()
                last_size = 0

                def callback(data):
                    nonlocal downloaded, last_time, last_size
                    downloaded += len(data)
                    current_time = time.time()
                    if current_time - last_time > 1:
                        speed = (downloaded - last_size) / (current_time - last_time) / (1024 * 1024)
                        percent = (downloaded / size) * 100
                        downloaded_mb = downloaded / (1024 * 1024)
                        print(f"\rProgress: {percent:.1f}% ({downloaded_mb:.1f}MB of {size_mb:.1f}MB) [{speed:.1f}MB/s]", end="")
                        last_time = current_time
                        last_size = downloaded
                    response.write(data)

                self.ftp.retrbinary(f'RETR {filename}', callback)
                print()
                response.seek(0)
                return response
            except Exception as e:
                retries += 1
                if retries == max_retries:
                    print(f"\nFTP download failed, trying HTTPS...")
                    try:
                        return await self.download_https(directory, filename)
                    except Exception as https_e:
                        raise Exception(
                            f"Both FTP and HTTPS downloads failed: FTP error: {str(e)}, HTTPS error: {str(https_e)}")
                else:
                    wait_time = 2 ** retries
                    print(f"\nDownload attempt {retries} failed, waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

    async def process_layer(self, directory: str, filename: str) -> Dict[str, Any]:
        if not self.config.is_layer_enabled(directory):
            print(f"Layer {directory} is disabled, skipping {filename}")
            return {
                'success': True,
                'file': filename,
                'status': 'skipped_disabled',
                'message': f"Layer {directory} is disabled"
            }

        if (directory, filename) in self.processed_files:
            print(f"Already processed {filename}, skipping")
            return {'success': True, 'file': filename, 'status': 'skipped'}

        try:
            layer_config = self.config.get_layer_config(directory)
            if not layer_config:
                return {
                    'success': False,
                    'file': filename,
                    'error': f"No configuration found for layer {directory}"
                }

            if layer_config.layer_type == "RELATIONSHIP":
                return {
                    'success': True,
                    'file': filename,
                    'status': 'skipped_relationship'
                }

            output_path = await self._process_spatial_file(layer_config, directory, filename)
            self._log_processed_file(directory, filename, 'success')
            self.processed_files.add((directory, filename))

            return {
                'success': True,
                'file': filename,
                'path': output_path,
                'layer_type': layer_config.layer_type
            }

        except Exception as e:
            error_msg = f"Error processing {filename}: {str(e)}"
            logging.error(error_msg)
            self._log_processed_file(directory, filename, f'error: {str(e)}')
            return {'success': False, 'file': filename, 'error': str(e)}

    async def _process_spatial_file(self, layer_config: LayerConfig, directory: str, filename: str) -> str:
        dir_path = os.path.join(self.config.processing.output_dir, directory)
        os.makedirs(dir_path, exist_ok=True)
        temp_dir = os.path.join(dir_path, "temp_shp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            print(f"\nProcessing {filename}:")
            response = await self._download_file(directory, filename)
            print("Extracting shapefile...")
            with zipfile.ZipFile(response) as zip_ref:
                zip_ref.extractall(temp_dir)

            base_name = filename.replace('.zip', '')
            shp_file = os.path.join(temp_dir, f"{base_name}.shp")
            
            print("Reading shapefile...")
            gdf = gpd.read_file(shp_file)
            print(f"Loaded {len(gdf):,} features")
            
            bounds = gdf.total_bounds
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
            geohash = gh.encode(center_lat, center_lon, precision=5)
            
            tolerance = layer_config.tolerance or self.config.processing.base_tolerance
            print(f"Processing geometry...")
            gdf['geometry'] = gdf['geometry'].simplify(
                tolerance=tolerance,
                preserve_topology=True
            )
            
            print("Converting to TopoJSON...")
            topo = topojson.Topology(gdf, prequantize=False)
            output_filename = f"{base_name}.{geohash}.topojson"
            output_path = os.path.join(dir_path, output_filename)
            
            print(f"Saving {output_filename}")
            with open(output_path, 'w') as f:
                json.dump(topo.to_dict(), f)
            
            print(f"Completed {filename}")
            return output_path
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    async def process_all(self):
        try:
            print("\nScanning available layers...")
            directories = [d for d in self.ftp.nlst() if '.' not in d]
            enabled_dirs = [d for d in directories if self.config.is_layer_enabled(d)]
            print(f"\nFound {len(enabled_dirs)} enabled layers to process")

            for layer_idx, dir in enumerate(enabled_dirs, 1):
                print(f"\nLayer {layer_idx} of {len(enabled_dirs)}: {dir}")
                self.ftp.cwd(f'{self.config.servers.base_path}/{dir}')
                files = [f for f in self.ftp.nlst() if f.endswith('.zip')]
                print(f"Found {len(files)} files to process in {dir}")
                
                for file_idx, file in enumerate(files, 1):
                    print(f"\nFile {file_idx} of {len(files)}")
                    await self.process_layer(dir, file)
                print(f"\nCompleted layer: {dir}")
            
            print("\nAll layers processed successfully!")
        except Exception as e:
            print(f"\nError during processing: {str(e)}")
            raise
        finally:
            self.close()

    def close(self):
        try:
            self.ftp.quit()
        except:
            pass

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'tiger_config.yaml') 
    processor = TigerProcessor(config_path)
    asyncio.run(processor.process_all())