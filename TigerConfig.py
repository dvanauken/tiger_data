from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import yaml
import os
from enum import Enum


class LayerType(Enum):
    SPATIAL = "SPATIAL"
    RELATIONSHIP = "RELATIONSHIP"


class GeometryType(Enum):
    POINT = "POINT"
    POLYLINE = "POLYLINE"
    POLYGON = "POLYGON"


@dataclass
class LayerConfig:
    """Configuration for a single TIGER layer"""
    name: str
    enabled: bool = True
    layer_type: LayerType = LayerType.SPATIAL
    geometry_type: Optional[GeometryType] = None
    tolerance: Optional[float] = None  # Override default tolerance
    skip_patterns: List[str] = None  # Skip files matching these patterns
    custom_processor: Optional[str] = None  # Custom processor class name


@dataclass
class ProcessingConfig:
    """Global processing configuration"""
    base_tolerance: float = 0.005
    output_dir: str = "./tiger_processed"
    ftp_host: str = 'ftp2.census.gov'
    https_host: str = 'www2.census.gov'
    base_path: str = '/geo/tiger/TIGER2023'
    max_retries: int = 3
    timeout: int = 300
    parallel_downloads: int = 4


class TigerConfig:
    """Main configuration manager"""

    def __init__(self, config_path: Optional[str] = None):
        self.processing = ProcessingConfig()
        self.layers: Dict[str, LayerConfig] = {}

        # Load built-in defaults
        self._load_defaults()

        # Override with custom config if provided
        if config_path and os.path.exists(config_path):
            self._load_custom_config(config_path)

    def _load_defaults(self):
        """Load default layer configurations"""
        # Common spatial layers most users want
        default_layers = {
            "STATE": LayerConfig("STATE", geometry_type=GeometryType.POLYGON),
            "COUNTY": LayerConfig("COUNTY", geometry_type=GeometryType.POLYGON),
            "TRACT": LayerConfig("TRACT", geometry_type=GeometryType.POLYGON),
            "PLACE": LayerConfig("PLACE", geometry_type=GeometryType.POLYGON),
            # Add other common defaults...
        }

        # Relationship tables disabled by default
        relationship_layers = {
            "ADDR": LayerConfig("ADDR", enabled=False, layer_type=LayerType.RELATIONSHIP),
            "ADDRFEAT": LayerConfig("ADDRFEAT", enabled=False, layer_type=LayerType.RELATIONSHIP),
            # Add other relationship layers...
        }

        self.layers.update(default_layers)
        self.layers.update(relationship_layers)

    def _load_custom_config(self, path: str):
        """Load custom configuration from YAML file"""
        with open(path, 'r') as f:
            config = yaml.safe_load(f)

        # Update processing config
        if 'processing' in config:
            for key, value in config['processing'].items():
                if hasattr(self.processing, key):
                    setattr(self.processing, key, value)

        # Update layer configs
        if 'layers' in config:
            for layer_name, layer_config in config['layers'].items():
                if layer_name in self.layers:
                    # Update existing layer config
                    for key, value in layer_config.items():
                        if hasattr(self.layers[layer_name], key):
                            setattr(self.layers[layer_name], key, value)
                else:
                    # Add new layer config
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

    def enable_layer(self, layer_name: str):
        """Enable a specific layer"""
        if layer_name in self.layers:
            self.layers[layer_name].enabled = True

    def disable_layer(self, layer_name: str):
        """Disable a specific layer"""
        if layer_name in self.layers:
            self.layers[layer_name].enabled = False