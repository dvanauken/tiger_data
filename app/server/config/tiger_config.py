from typing import Dict, Optional
import os
import yaml
from .layer_config import LayerConfig
from .processing_config import ProcessingConfig
from .server_config import ServerConfig

class TigerConfig:
    def __init__(self, config_path: Optional[str] = None):
        self.processing = ProcessingConfig()
        self.servers = ServerConfig()
        self.layers: Dict[str, LayerConfig] = {}
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                if 'processing' in config:
                    for key, value in config['processing'].items():
                        if hasattr(self.processing, key):
                            setattr(self.processing, key, value)
                if 'servers' in config:
                    for key, value in config['servers'].items():
                        if hasattr(self.servers, key):
                            setattr(self.servers, key, value)
                if 'layers' in config:
                    for layer_name, layer_config in config['layers'].items():
                        self.layers[layer_name] = LayerConfig(name=layer_name, **layer_config)

    def is_layer_enabled(self, layer_name: str) -> bool:
        return layer_name in self.layers and self.layers[layer_name].enabled

    def get_layer_config(self, layer_name: str) -> Optional[LayerConfig]:
        return self.layers.get(layer_name)