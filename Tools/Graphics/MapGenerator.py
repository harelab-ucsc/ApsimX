"""
@file           MapGenerator.py

@author         jLab
@author         HARE Lab
@author         nubby   (jlee211@ucsc.edu)

@version        1.0.1
@date           1 Jul 2025

@contributors   Raster processing code assisted by Perplexity.IO.
"""

import csv
import json
from math import radians, sin, cos, sqrt, atan2
import numpy as np
import utm
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt


_CSV_FILENAME = "UCSCFarm-HaybarnField-20241014_20250130/FlagLocations.csv"
_GEOTIFF_FILENAME = "UCSCFarm-HaybarnField-20241014_20250130/20250701_151600-UCSCFarm_HaybarnFields_GeoRef.tif"

# UTM maxima; minima are 0.
_UTM_NORTH_MAX  = 100000000 
_UTM_EAST_MAX   = 100000000

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

"""_get_coords_by_label()

Read a clicker CSV file and return only latitude/longitude data based on label.

@param

@return
    * use_utm == True: [easting, northing, zone_number, zone_letter]
        + easting: (float) m
        + northing: (float) m
        + zone_number: (int)
        + zone_letter: (str)
    * use_utm == False: [lat_coords, lon_coords]
"""
def _get_coords_by_label(label: str, use_utm: bool = True) -> list[tuple]:
    # This LUT converts a flag's color into its label from the clicker.
    flag_lut = {
            "blue": "label 3",
            "yellow": "label 4",
            "teros": "label 5",
            "atmos": "label 6",
            "boundary": "label 7",
            "gcp": "label 8"
            }
    flag = flag_lut[label]
    coords = _get_csv_coords_by_label(_CSV_FILENAME, flag)
    lat_coords = [coord[0] for coord in coords]
    lon_coords = [coord[1] for coord in coords]
    if use_utm:
        return [utm.from_latlon(
            lat_coord, lon_coord
            ) for lat_coord, lon_coord in zip(lat_coords, lon_coords)]
    return zip(lat_coords, lon_coords)

"""_generate_point_from_poi(poi_coord)

Convert UTM coordinates into a GeoJSON point format.

@param
@return
"""
def _generate_point_from_poi(poi_coord: tuple, label: int) -> dict:
    return {
            "type": "Feature",
            "id": label,
            "properties": {},
            "geometry": {
                "type": "Point",
                "coordinates": [poi_coord[0], poi_coord[1]]
                }
            }

"""_generate_line_from_pois(poi_coord1, poi_coord2)

Convert UTM coordinates into a GeoJSON line format.

@param
@param
@param
@return
"""
def _generate_line_from_pois(
        poi_coord1: tuple,
        poi_coord2: tuple, 
        label: int) -> dict:
    return {
            "type": "Feature",
            "id": label,
            "properties": {},
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    poi_coord1,
                    poi_coord2
                    ]
                }
            }

"""_generate_points_from_pois(gcp_coords, resolution)

Bound the polygon defined by GCP coordinates within a rectangle and return
GeoJSON-formatted dictionaries that form a "brownie pan" grid.

@param  gcp_coords  [easting, northing, zone_number, zone_letter]
@param  resolution  In meters; defines the length of one side of square nodes.
@return List of GeoJSON-formatted dictionaries defining the grid.
"""
def _generate_points_from_pois(poi_coords: list[tuple]) -> dict:
    label = 0
    features = []
    for coord in poi_coords:
        features.append(_generate_point_from_poi(coord, label))
        label += 1
    return {
            "type": "FeatureCollection",
            "features": features
            }

"""_generate_grid_from_boundary(boundary_coords, resolution)

Bound the polygon defined by boundary coordinates within a rectangle and return
GeoJSON-formatted dictionaries that form a "brownie pan" grid.

@param  boundary_coords     [easting, northing, zone_number, zone_letter]
@param  resolution          In meters; defines the length of one side of square
                            nodes.
@return List of GeoJSON-formatted dictionaries defining the grid.
"""
def _generate_grid_from_boundary(
        boundary_coords: list[tuple],
        resolution: float) -> list[dict]:
    # Assume we are in Zone 10N for now.
    # TODO: Make zone-agnostic.
    bound_ne = [0, 0, 10, "N"]
    bound_sw = [_UTM_EAST_MAX, _UTM_NORTH_MAX, 10, "N"]

    # Define a bounding rectangle with two points.
    # NOTE: The enclosing grid will extend beyond the boundaries on the
    #       N and E edges.
    for coord in boundary_coords:
        if coord[0] > bound_ne[0]:
            bound_ne[0] = coord[0] + resolution
        if coord[1] > bound_ne[1]:
            bound_ne[1] = coord[1] + resolution
        if coord[0] < bound_sw[0]:
            bound_sw[0] = coord[0]
        if coord[1] < bound_sw[1]:
            bound_sw[1] = coord[1]

    # Build a grid enclosing the borders.
    x = np.arange(bound_sw[0], bound_ne[0], resolution)
    y = np.arange(bound_sw[1], bound_ne[1], resolution)

    # Create lines spanning the grid (to minimize lines used).
    grid = []
    label = 0
    for x_i in x:
        grid.append(_generate_line_from_pois(
            [x_i, bound_sw[1]], [x_i, bound_ne[1]], label))
        label += 1
    for y_i in y:
        grid.append(_generate_line_from_pois(
            [bound_sw[0], y_i], [bound_ne[0], y_i], label))
        label += 1
    # Format as a collection.
    grid_out = {
            "type": "FeatureCollection",
            "features": grid
            }
    return grid_out

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
        blue_coords = _get_coords_by_label("blue")
        geojson_blue_pois = _generate_points_from_pois(blue_coords)
        with open("blue.geojson", "w") as gfp:
            json.dump(geojson_blue_pois, gfp)

        yellow_coords = _get_coords_by_label("yellow")
        geojson_yellow_pois = _generate_points_from_pois(yellow_coords)
        with open("yellow.geojson", "w") as gfp:
            json.dump(geojson_yellow_pois, gfp)

        teros_coords = _get_coords_by_label("teros")
        geojson_teros_pois = _generate_points_from_pois(teros_coords)
        with open("teros.geojson", "w") as gfp:
            json.dump(geojson_teros_pois, gfp)

        atmos_coords = _get_coords_by_label("atmos")
        geojson_atmos_pois = _generate_points_from_pois(atmos_coords)
        with open("atmos.geojson", "w") as gfp:
            json.dump(geojson_atmos_pois, gfp)
        
        gcp_coords = _get_coords_by_label("gcp")
        print(str(gcp_coords))

        boundary_coords = _get_coords_by_label("boundary")
        geojson_gridlines = _generate_grid_from_boundary(boundary_coords, 0.5)
        with open("grid.geojson", "w") as gfp:
            json.dump(geojson_gridlines, gfp)

        """
        e_blue_coords,
        n_blue_coords,
        zone_blue_num,
        zone_blue_let = _get_coords_by_label("blue")
        e_yellow_coords,
        n_yellow_coords,
        zone_yellow_num,
        zone_yellow_let = _get_coords_by_label("yellow")
        e_teros_coords,
        n_teros_coords,
        zone_teros_num,
        zone_teros_let = _get_coords_by_label("teros")
        e_atmos_coords,
        n_atmos_coords,
        zone_num,
        zone_let = _get_coords_by_label("atmos")
        """
        """
        lat_blue_coords, lon_blue_coords = _get_coords_by_label("blue")
        lat_yellow_coords, lon_yellow_coords = _get_coords_by_label("yellow")
        lat_teros_coords, lon_teros_coords = _get_coords_by_label("teros")
        lat_atmos_coords, lon_atmos_coords = _get_coords_by_label("atmos")

        # Get the min distance between Teros sensor locations.
        min_distance = _find_min_distance_between_coords(
                zip(lat_teros_coords,lon_teros_coords))
        print(min_distance)

        # 'bo', 'yo', 'ro' for blue, yellow, and red circles, resp.
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
        plt.show()
        #plt.savefig(f"UCSCFarmHaybarnField_SensorAndLoggerLocations_WGS84.png")
        """

