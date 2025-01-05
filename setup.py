from setuptools import setup, find_packages

setup(
    name='TigerGeoprocessing',
    version='0.1.0',
    description='Geospatial processing for TIGER/Line data',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
        'tqdm>=4.65.0',
        'geopandas~=1.0.1',
        'topojson~=1.9',
        'aiohttp>=3.8.1',
        'fastapi>=0.68.0',
        'uvicorn>=0.15.0',
        'pygeohash>=1.2.0',
        'shapely>=1.8.0'
    ],
    python_requires='>=3.7',
)
