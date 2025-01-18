import streamlit as st
import json
import folium
from streamlit_folium import folium_static
import topojson as tp
import geopandas as gpd
from shapely.geometry import shape
import os
from pathlib import Path


def load_topojson(file_path):
    """Load and convert TopoJSON to GeoJSON for visualization"""
    with open(file_path, 'r') as f:
        topojson_data = json.load(f)

    # Get the first geometry collection from the TopoJSON
    geometry_key = list(topojson_data['objects'].keys())[0]
    geojson = tp.feature(topojson_data, geometry_key)
    return geojson


def main():
    st.title("TopoJSON Viewer")

    # File selection
    file_path = st.file_uploader("Choose a TopoJSON file", type=['topojson'])

    if file_path is not None:
        try:
            # Load and convert the data
            geojson = load_topojson(file_path)

            # Create map centered on the data
            # Initialize with a default view of the US
            m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

            # Add the GeoJSON layer
            folium.GeoJson(
                geojson,
                style_function=lambda x: {
                    'fillColor': '#ffff00',
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.5
                }
            ).add_to(m)

            # Fit map bounds to the data
            gdf = gpd.GeoDataFrame.from_features(geojson['features'])
            bounds = gdf.total_bounds
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

            # Display the map
            folium_static(m)

            # Display some basic information about the file
            st.subheader("File Information")
            st.write(f"Number of features: {len(geojson['features'])}")

            # Display the raw JSON if requested
            if st.checkbox("Show raw JSON"):
                st.json(geojson)

        except Exception as e:
            st.error(f"Error loading file: {str(e)}")


if __name__ == "__main__":
    main()