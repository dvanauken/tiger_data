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
from dataclasses import dataclass
import yaml

from tiger_types import TigerLayer, TigerLayerType, TigerGeometryType
from processors import get_processor
from typing import Dict, Any, Optional, List  # Add List to the imports



@dataclass
class ProcessingConfig:
    """Global processing configuration"""
    base_tolerance: float = 0.005
    output_dir: str = "./tiger_processed"
    parallel_downloads: int = 4
    max_retries: int = 3
    timeout: int = 300


@dataclass
class ServerConfig:
    """Server configuration"""
    ftp_host: str = 'ftp2.census.gov'
    https_host: str = 'www2.census.gov'
    base_path: str = '/geo/tiger/TIGER2023'


@dataclass
class LayerConfig:
    """Configuration for a single TIGER layer"""
    name: str
    description: str
    enabled: bool = True
    layer_type: str = "SPATIAL"
    geometry_type: Optional[str] = None
    tolerance: Optional[float] = None
    skip_patterns: List[str] = None
    custom_processor: Optional[str] = None


class TigerConfig:
    """Main configuration manager"""

    def __init__(self, config_path: Optional[str] = None):
        self.processing = ProcessingConfig()
        self.servers = ServerConfig()
        self.layers: Dict[str, LayerConfig] = {}

        # Load built-in defaults
        self._load_defaults()

        # Override with custom config if provided
        if config_path and os.path.exists(config_path):
            self._load_custom_config(config_path)

    def _load_defaults(self):
        """Load default layer configurations"""
        # Common spatial layers that most users want
        default_layers = {
            "STATE": LayerConfig(
                name="STATE",
                description="States and Equivalent Areas",
                geometry_type="POLYGON",
                tolerance=0.003
            ),
            "COUNTY": LayerConfig(
                name="COUNTY",
                description="Counties and Equivalent Areas",
                geometry_type="POLYGON",
                tolerance=0.003
            )
        }
        self.layers.update(default_layers)

    def _load_custom_config(self, path: str):
        """Load custom configuration from YAML file"""
        with open(path, 'r') as f:
            config = yaml.safe_load(f)

        # Update processing config
        if 'processing' in config:
            for key, value in config['processing'].items():
                if hasattr(self.processing, key):
                    setattr(self.processing, key, value)

        # Update server config
        if 'servers' in config:
            for key, value in config['servers'].items():
                if hasattr(self.servers, key):
                    setattr(self.servers, key, value)

        # Update layer configs
        if 'layers' in config:
            for layer_name, layer_config in config['layers'].items():
                if 'enabled' not in layer_config:
                    layer_config['enabled'] = True
                self.layers[layer_name] = LayerConfig(
                    name=layer_name,
                    **layer_config
                )

    def is_layer_enabled(self, layer_name: str) -> bool:
        """Check if a layer is enabled"""
        return layer_name in self.layers and self.layers[layer_name].enabled

    def get_layer_config(self, layer_name: str) -> Optional[LayerConfig]:
        """Get configuration for a specific layer"""
        return self.layers.get(layer_name)


class TigerProcessor:
    def __init__(self, config_path: Optional[str] = None):
        # Load configuration
        self.config = TigerConfig(config_path)

        # Setup environment based on config
        self._setup_environment()
        self.processed_files = self._load_processed_files()
        self.connect_ftp()

    def _setup_environment(self):
        """Setup logging and directory structure"""
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
        """Load record of processed files"""
        if not os.path.exists(self.log_file):
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
            self.ftp = FTP(self.config.servers.ftp_host)
            self.ftp.login()
            self.ftp.cwd(self.config.servers.base_path)
        except Exception as e:
            logging.error(f"FTP connection error: {str(e)}")
            raise

    async def download_https(self, directory: str, filename: str) -> io.BytesIO:
        """Download file via HTTPS"""
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

    async def process_layer(self, directory: str, filename: str) -> Dict[str, Any]:
        """Process a single TIGER/Line layer file"""
        # Check if layer is enabled in config
        if not self.config.is_layer_enabled(directory):
            return {
                'success': True,
                'file': filename,
                'status': 'skipped_disabled',
                'message': f"Layer {directory} is disabled in configuration"
            }

        if (directory, filename) in self.processed_files:
            logging.info(f"Skipping already processed: {filename}")
            return {'success': True, 'file': filename, 'status': 'skipped'}

        try:
            # Get layer configuration
            layer_config = self.config.get_layer_config(directory)
            if not layer_config:
                return {
                    'success': False,
                    'file': filename,
                    'error': f"No configuration found for layer {directory}"
                }

            # Skip relationship files
            if layer_config.layer_type == "RELATIONSHIP":
                return {
                    'success': True,
                    'file': filename,
                    'status': 'skipped_relationship'
                }

            # Process spatial file
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
        """Process a spatial data file"""
        dir_path = os.path.join(self.config.processing.output_dir, directory)
        os.makedirs(dir_path, exist_ok=True)
        temp_dir = os.path.join(dir_path, "temp_shp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Download and extract
            response = await self._download_file(directory, filename)
            with zipfile.ZipFile(response) as zip_ref:
                zip_ref.extractall(temp_dir)

            # Use layer-specific tolerance if set, otherwise use base tolerance
            tolerance = layer_config.tolerance or self.config.processing.base_tolerance

            # Process file
            base_name = filename.replace('.zip', '')
            shp_file = os.path.join(temp_dir, f"{base_name}.shp")

            # Read file and get bounds before processing
            gdf = gpd.read_file(shp_file)
            bounds = gdf.total_bounds

            # Calculate geohash for center point
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
            geohash = gh.encode(center_lat, center_lon, precision=5)

            # Process geometry
            gdf['geometry'] = gdf['geometry'].simplify(
                tolerance=tolerance,
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
    async def _download_file(self, directory: str, filename: str, max_retries: int = 3) -> io.BytesIO:
        """Download file with FTP/HTTPS fallback and retries"""
        retries = 0
        while retries < max_retries:
            try:
                # Try FTP first
                response = io.BytesIO()
                self.ftp.cwd(f'{self.config.servers.base_path}/{directory}')
                self.ftp.retrbinary(f'RETR {filename}', response.write)
                response.seek(0)
                return response
            except Exception as e:
                retries += 1
                if retries == max_retries:
                    logging.warning(f"FTP download failed after {max_retries} attempts, trying HTTPS")
                    try:
                        return await self.download_https(directory, filename)
                    except Exception as https_e:
                        raise Exception(
                            f"Both FTP and HTTPS downloads failed: FTP error: {str(e)}, HTTPS error: {str(https_e)}")
                else:
                    wait_time = 2 ** retries  # Exponential backoff
                    logging.warning(f"Download attempt {retries} failed, waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

    def _validate_config(self, config: dict) -> None:
        """Validate the loaded YAML configuration"""
        required_sections = ['processing', 'servers', 'layers']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section '{section}' in configuration")

        # Validate processing section
        if not isinstance(config['processing'].get('base_tolerance', 0.005), (int, float)):
            raise ValueError("base_tolerance must be a number")

        # Validate layers
        for layer_name, layer_config in config.get('layers', {}).items():
            if not isinstance(layer_config, dict):
                raise ValueError(f"Layer {layer_name} configuration must be a dictionary")
            if 'description' not in layer_config:
                raise ValueError(f"Layer {layer_name} is missing required field 'description'")

    def close(self):
        """Clean up resources"""
        try:
            self.ftp.quit()
        except:
            pass


async def main():
    processor = TigerProcessor('tiger_config.yaml')  # Use config file

    try:
        processor.ftp.cwd(processor.config.servers.base_path)
        directories = [d for d in processor.ftp.nlst() if '.' not in d]

        # Process each layer with progress bar
        for dir in tqdm(directories, desc="Processing layers", unit="layer"):
            # Skip if layer is not enabled
            if not processor.config.is_layer_enabled(dir):
                continue

            processor.ftp.cwd(f'{processor.config.servers.base_path}/{dir}')
            files = [f for f in processor.ftp.nlst() if f.endswith('.zip')]

            # Process files with nested progress bar
            for file in tqdm(files, desc=f"Processing {dir}", leave=False):
                result = await processor.process_layer(dir, file)
                if result['success']:
                    if result.get('status') == 'skipped_disabled':
                        print(f"⏭ Skipped {file} (disabled)")
                    elif result.get('status') == 'skipped':
                        print(f"⏭ Skipped {file} (already processed)")
                    elif result.get('status') == 'skipped_relationship':
                        print(f"📋 {file} (relationship file)")
                    else:
                        print(f"✓ {file}")
                else:
                    print(f"✗ Error processing {file}: {result.get('error', 'Unknown error')}")

    except Exception as e:
        logging.error(f"Processing error: {str(e)}")
        raise
    finally:
        processor.close()


if __name__ == "__main__":
    asyncio.run(main())