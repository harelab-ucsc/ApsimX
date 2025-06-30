"""
@file           MapGenerator.py

@author         jLab
@author         HARE Lab
@author         nubby   (jlee211@ucsc.edu)
@date           25 Jun 2025

@contributors   Raster processing code assisted by Perplexity.IO.
"""

import csv
from math import radians, sin, cos, sqrt, atan2
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt


_CSV_FILENAME = "FlagLocations.csv"
_GEOTIFF_FILENAME = "20250624_173200-UCSCFarm_HaybarnFields_GeoRef.tif"


"""distance_between_coordinates()
"""
def distance_between_coordinates(lat1, lon1, lat2, lon2):
    # Radius of the Earth in meters.
    R = 6371.0 * 1000

    # Convert latitude and longitude from degrees to radians.
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Differences.
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Haversine formula.
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Distance in meters.
    distance = R * c
    return distance

def _find_min_distance_between_coords(
        coords: list[tuple[float, float]]) -> float:
    min_distance = 10000000
    for coord1 in coords:
        for coord2 in coords:
            if coord1 != coord2:
                distance = distance_between_coordinates(coord1[0],coord1[1],coord2[0],coord2[1])
                if distance < min_distance:
                    min_distance = distance
    return min_distance

"""_get_csv_coords_by_label()
"""
def _get_csv_coords_by_label(csv_filepath: str, label: str) -> list[tuple]:
    coords = []
    with open(csv_filepath, mode="r") as cvp:
        csv_reader = csv.reader(cvp)
        for row in csv_reader:
            # Check each row for appropriate label.
            if (row[-1] == label):
                # Set coords as "[lat, lon]".
                coords.append([float(row[0]), float(row[1])])
    return coords

"""_get_latlon_by_label()

Read a clicker CSV file and return only latitude/longitude data based on label.

@param

@return
"""
def _get_latlon_by_label(label: str) -> list[tuple]:
    # This LUT converts a flag's color into its label from the clicker.
    flag_lut = {
            "blue": "label 3",
            "yellow": "label 4",
            "teros": "label 5",
            "atmos": "label 6"
            }
    flag = flag_lut[label]
    coords = _get_csv_coords_by_label(_CSV_FILENAME, flag)
    lat_coords = [coord[0] for coord in coords]
    lon_coords = [coord[1] for coord in coords]
    return [lat_coords, lon_coords]

"""MapGenerator

Add annotations to a .tif raster for beautiful, informative map generation.
"""
if __name__ == "__main__":
    # Open the GeoTIFF file.
    with rasterio.open(_GEOTIFF_FILENAME) as src:
        # Read the raster data.
        raster_data = src.read()

        # Create a figure and axis for plotting.
        fig, ax = plt.subplots()

        # Plot the raster data;
        # utilize the transform for proper georeferencing.
        show(raster_data, ax=ax, transform=src.transform)

        # Add markers at specific coordinates.
        # Remember to use the CRS of your raster data.
        lat_blue_coords, lon_blue_coords = _get_latlon_by_label("blue")
        lat_yellow_coords, lon_yellow_coords = _get_latlon_by_label("yellow")
        lat_teros_coords, lon_teros_coords = _get_latlon_by_label("teros")
        lat_atmos_coords, lon_atmos_coords = _get_latlon_by_label("atmos")

        # Get the min distance between Teros sensor locations.
        min_distance = _find_min_distance_between_coords(
                zip(lat_teros_coords,lon_teros_coords))
        print(min_distance)

        # 'bo' for blue, 'yo' for yellow, 'ro' for red circles.
        ax.plot(lon_blue_coords,
                lat_blue_coords,
                'bo',
                markersize=5,
                label="Blue flag")
        ax.plot(lon_yellow_coords,
                lat_yellow_coords,
                'yo',
                markersize=5,
                label="Yellow flag")
        ax.plot(lon_teros_coords,
                lat_teros_coords,
                'o',
                color="magenta",
                markersize=5,
                label="Teros logger")
        ax.plot(lon_atmos_coords,
                lat_atmos_coords,
                'ro',
                markersize=5,
                label="Atmos logger")

        # Add labels and title.
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title("(WGS 84) UCSC Farm Haybarn Field: Sensor Locations")

        # Show the plot.
        plt.legend()
        #plt.show()
        plt.savefig(f"UCSCFarmHaybarnField_SensorAndLoggerLocations_WGS84.png")

