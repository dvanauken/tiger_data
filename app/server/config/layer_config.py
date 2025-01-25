from dataclasses import dataclass
from typing import Optional, List

@dataclass
class LayerConfig:
    name: str
    description: str
    enabled: bool = True
    layer_type: str = "SPATIAL"
    geometry_type: Optional[str] = None
    tolerance: Optional[float] = None
    skip_patterns: List[str] = None
    custom_processor: Optional[str] = None