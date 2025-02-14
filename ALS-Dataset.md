# Airborne-Lidar-Scanning dataset

The ALS dataset is freely available dataset, served by the austrian Federal Office for Metrology and Surveying.

The digital terrain elevation model (DTM) describes the earth's surface (natural ground, without vegetation) in the form of sets of points arranged in a regular grid and georeferenced in terms of position and height.
The high-resolution ALS-DGM data was captured using airborne laser scanning technologies and is a cooperative product of the Austrian federal and state government geodata providers.

## Precision
The data is structured into 50km x 50km tiles.
An overview of the Tiled map can be downloaded [here](https://www.bev.gv.at/dam/jcr:2c9aefcf-8662-4fb0-bd8a-6b29c637117b/ALS_Kacheluebersicht.pdf).
The heights are captured in 1x1m areas and are precise to +- 0.5m.

## Measurement Types
The dataset consists of 2 types of measurements:
1. Digital Terrain Model (not including Buildings)
2. Digital Surface Model (including Buildings)

## File format
All the tiles are in GeoTiF Format, thus are in principle compatible with the original implementation of open-elevation.
The ALS dataset uses the EPSG:3035 projection, while open-elevation requires the input data to be in EPSG:4326 (WGS84).
Therefore, the downloaded data has to be reprojected into EPSG:4326 using this gdal command:

    gdalwarp -s_srs EPSG:3035 -t_srs EPSG:4326 -r near -of GTiff <input_file> <output_file>

## Download
The dataset can be downloaded manually [here](https://www.bev.gv.at/Services/Produkte.html).
The process of downloading and reprojecting the dataset can be automated using the "download_and_transform_ALS.sh" script.
Currently, the usage of this script is only tested directly on Linux, it should also work within a docker container to use on Windows.
When downloading the full dataset, about 550GB Storage is needed.