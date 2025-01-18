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
    #ROADS = ("ROADS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #PRIMARYROADS = ("PRIMARYROADS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #PRISECROADS = ("PRISECROADS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #RAILS = ("RAILS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)

    # Boundary Features (Polyline)
    #AIANNH = ("AIANNH", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    #AITSN = ("AITSN", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    # COUNTY = ("COUNTY", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    # STATE = ("STATE", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    # ... (add other boundary features)


    # AIANNH = ("AIANNH", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)  # American Indian/Alaska Native/Native Hawaiian Areas
    # AITS = ("AITS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)      # American Indian Tribal Subdivisions
    # ANRC = ("ANRC", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)      # Alaska Native Regional Corporations
    # BG = ("BG", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)          # Block Groups
    # CBSA = ("CBSA", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)      # Core Based Statistical Areas
    # CD = ("CD", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)          # Congressional Districts
    # CNECTA = ("CNECTA", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)  # Combined New England City and Town Areas
    # CONCITY = ("CONCITY", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)# Consolidated Cities
    # COUNTY = ("COUNTY", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)  # Counties
    # COUSUB = ("COUSUB", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)  # County Subdivisions
    # CSA = ("CSA", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)        # Combined Statistical Areas
    # ELSD = ("ELSD", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)      # Elementary School Districts
    # METDIV = ("METDIV", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)  # Metropolitan Divisions
    # MIL = ("MIL", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)        # Military Installations
    # NECTA = ("NECTA", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)    # New England City and Town Areas
    # NECTADIV = ("NECTADIV", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)  # New England City and Town Area Divisions
    # PLACE = ("PLACE", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)    # Census Places
    # PUMA = ("PUMA", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)      # Public Use Microdata Areas
    # SCSD = ("SCSD", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)      # Secondary School Districts
    # SLDL = ("SLDL", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)      # State Legislative Districts - Lower Chamber
    # SLDU = ("SLDU", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)      # State Legislative Districts - Upper Chamber
    # STATE = ("STATE", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)     # States and Equivalent Areas
    # SUBMCD = ("SUBMCD", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)  # Sub-Minor Civil Divisions
    # TABBLOCK = ("TABBLOCK", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE) # Census Blocks
    # TBG = ("TBG", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)        # Tribal Block Groups
    # TRACT = ("TRACT", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)    # Census Tracts
    # TTRACT = ("TTRACT", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)  # Tribal Census Tracts
    # UAC = ("UAC", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)        # Urban Areas
    # UNSD = ("UNSD", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)      # Unified School Districts
    # VTD = ("VTD", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)        # Voting Districts

    PRIMARYROADS = ("PRIMARYROADS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)
    PRISECROADS = ("PRISECROADS", TigerLayerType.SPATIAL, TigerGeometryType.POLYLINE)        # Voting Districts




    # # Polygon Features
    # AREALM = ("AREALM", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)
    # AREAWATER = ("AREAWATER", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)
    # COASTLINE = ("COASTLINE", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)




    #AIANNH = ("AIANNH", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)    # American Indian/Alaska Native/Native Hawaiian Areas
    #ANRC = ("ANRC", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)        # Alaska Native Regional Corporations
    #AREALM = ("AREALM", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)    # Area Landmarks
    #AREAWATER = ("AREAWATER", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)  # Area Hydrography
    #BG = ("BG", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)            # Block Groups
    #CBSA = ("CBSA", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)        # Core Based Statistical Areas
    #CD = ("CD", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)            # Congressional Districts
    #CNECTA = ("CNECTA", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)    # Combined New England City and Town Areas
    #COASTLINE = ("COASTLINE", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)  # Coastline
    #CONCITY = ("CONCITY", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)  # Consolidated Cities
    #COUNTY = ("COUNTY", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)    # Counties
    #COUSUB = ("COUSUB", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)    # County Subdivisions
    #CSA = ("CSA", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)          # Combined Statistical Areas
    #ELSD = ("ELSD", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)        # Elementary School Districts
    #METDIV = ("METDIV", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)    # Metropolitan Divisions
    #MIL = ("MIL", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)          # Military Installations
    #NECTA = ("NECTA", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)      # New England City and Town Areas
    #NECTADIV = ("NECTADIV", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)    # New England City and Town Area Divisions
    #PLACE = ("PLACE", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)      # Census Places
    #PUMA = ("PUMA", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)        # Public Use Microdata Areas
    #RESERVATION = ("RESERVATION", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)  # Federal American Indian Reservations
    #SCSD = ("SCSD", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)        # Secondary School Districts
    #SLDL = ("SLDL", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)        # State Legislative Districts - Lower Chamber
    #SLDU = ("SLDU", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)        # State Legislative Districts - Upper Chamber
    #STATE = ("STATE", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)       # States and Equivalent Areas
    #SUBBARRIO = ("SUBBARRIO", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)  # Sub-Barrios (Puerto Rico)
    #SUBMCD = ("SUBMCD", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)    # Sub-Minor Civil Divisions
    #TABBLOCK = ("TABBLOCK", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)  # Census Blocks
    #TRACT = ("TRACT", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)      # Census Tracts
    #TTRACT = ("TTRACT", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)    # Tribal Census Tracts
    UAC = ("UAC", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)          # Urban Areas
    UNSD = ("UNSD", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)        # Unified School Districts
    VTD = ("VTD", TigerLayerType.SPATIAL, TigerGeometryType.POLYGON)          # Voting Districts


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