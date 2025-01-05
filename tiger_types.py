from enum import Enum

class TigerLayerType(Enum):
    SPATIAL = "SPATIAL"
    RELATIONSHIP = "RELATIONSHIP"

class TigerGeometryType(Enum):
    POINT = "POINT"
    POLYLINE = "POLYLINE"
    POLYGON = "POLYGON"

class TigerLayer(Enum):
    ## Relationship Tables
    #ADDR = ("ADDR", TigerLayerType.RELATIONSHIP, None)
    #ADDRFEAT = ("ADDRFEAT", TigerLayerType.RELATIONSHIP, None)
    #ADDRFN = ("ADDRFN", TigerLayerType.RELATIONSHIP, None)
    #FACES = ("FACES", TigerLayerType.RELATIONSHIP, None)
    #FACESAH = ("FACESAH", TigerLayerType.RELATIONSHIP, None)
    #FACESAL = ("FACESAL", TigerLayerType.RELATIONSHIP, None)
    #FACESMIL = ("FACESMIL", TigerLayerType.RELATIONSHIP, None)
    #FEATNAMES = ("FEATNAMES", TigerLayerType.RELATIONSHIP, None)
    #TBG = ("TBG", TigerLayerType.RELATIONSHIP, None)

    ## Point Features
    #POINTLM = ("POINTLM", TigerLayerType.SPATIAL, TigerGeometryType.POINT)

    ## Polyline Features
    #EDGES = ("EDGES", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #LINEARWATER = ("LINEARWATER", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    ROADS = ("ROADS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #PRIMARYROADS = ("PRIMARYROADS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #PRISECROADS = ("PRISECROADS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #RAILS = ("RAILS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)

    ## Boundary Features (Polyline)
    #AIANNH = ("AIANNH", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #AITSN = ("AITSN", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #COUNTY = ("COUNTY", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #STATE = ("STATE", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    ## ... (add other boundary features)

    ## Polygon Features
    #AREALM = ("AREALM", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)
    #AREAWATER = ("AREAWATER", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)
    #COASTLINE = ("COASTLINE", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)

    def __init__(self, dirname, layer_type, geometry_type):
        self.dirname = dirname  # Changed from name to dirname
        self.layer_type = layer_type
        self.geometry_type = geometry_type

    @classmethod
    def from_directory_name(cls, dirname: str):
        try:
            return cls[dirname.upper()]
        except KeyError:
            raise ValueError(f"Unknown TIGER/Line layer type: {dirname}")