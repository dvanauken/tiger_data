import geopandas as gpd
import topojson
import os
import json
from abc import ABC, abstractmethod
from typing import Any, Dict
from tiger_types import TigerGeometryType


class BaseProcessor(ABC):
    def __init__(self, tolerance: float = 0.001):
        self.tolerance = tolerance

    @abstractmethod
    def process(self, shp_file: str) -> Dict[str, Any]:
        """Process a shapefile and return topojson data"""
        pass

    def _simplify_geometry(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Common geometry simplification logic"""
        gdf['geometry'] = gdf['geometry'].simplify(
            tolerance=self.tolerance,
            preserve_topology=True
        )
        return gdf


class PolygonProcessor(BaseProcessor):
    def process(self, shp_file: str) -> Dict[str, Any]:
        gdf = gpd.read_file(shp_file)
        gdf = self._simplify_geometry(gdf)

        # Special handling for polygon features
        gdf = gdf.explode(index_parts=True)
        gdf = gdf.reset_index(drop=True)

        topo = topojson.Topology(gdf, prequantize=False)
        return topo.to_dict()


class PolylineProcessor(BaseProcessor):
    def process(self, shp_file: str) -> Dict[str, Any]:
        gdf = gpd.read_file(shp_file)
        gdf = self._simplify_geometry(gdf)

        # Special handling for line features
        # Ensure proper line directionality and connectivity
        topo = topojson.Topology(gdf, prequantize=False)
        return topo.to_dict()


class PointProcessor(BaseProcessor):
    def process(self, shp_file: str) -> Dict[str, Any]:
        gdf = gpd.read_file(shp_file)
        # Points don't need simplification

        topo = topojson.Topology(gdf, prequantize=False)
        return topo.to_dict()


class RelationshipProcessor(BaseProcessor):
    def process(self, dbf_file: str) -> Dict[str, Any]:
        # Handle relationship files (DBF only)
        # This might be implemented later when we handle relationship files
        raise NotImplementedError("Relationship file processing not yet implemented")


def get_processor(geometry_type: TigerGeometryType, tolerance: float = 0.001) -> BaseProcessor:
    """Factory function to get the appropriate processor"""
    processors = {
        TigerGeometryType.POLYGON: PolygonProcessor(tolerance),
        TigerGeometryType.POLYLINE: PolylineProcessor(tolerance),
        TigerGeometryType.POINT: PointProcessor(tolerance)
    }

    processor = processors.get(geometry_type)
    if not processor:
        raise ValueError(f"No processor available for geometry type: {geometry_type}")

    return processor