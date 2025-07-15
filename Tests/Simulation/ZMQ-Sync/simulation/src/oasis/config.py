#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@file   config.py

Configuration for OASIS simulation using Apsim.
Kraww!!

@author     jLab
@author     HARE Lab

@date       14 May 2025
@version    1.0.3
"""
import copy
import csv
import geojson
import json
import math
import numpy as np
import os
import random
import rasterio
import re

from dataclasses import dataclass
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
from typing import Union
#from rasterio import Affine


# Module-level defs.

## Macros.

DEFAULT_CONFIGS = {
        "dim_x": 16,        # Number of nodes in one direction.
        "dim_y": 16,
        "dim_z": 1,         # Altitude.
        "layers": 10,       # Layers per node.
        "vwc_min": 0.1,   # Gallons?
        "vwc_max": 2.0,   # Gallons?
        "r": 0.5,         # Acres?
        "spacing": 1        # Acres?
        }

DEFAULT_DATA_DIR = "./data/"
DEFAULT_OUTPUT_DIR = "./out/"
DEFAULT_TOLERANCE = 0.0001      # Tolerance in coordinates for locations.
DEFAULT_LABEL = "simpleMean"

DEFAULT_MM_TO_LAYER = 200       # Encoding of depth until we can encode TIFF
                                # files with depth data in Apsim.

VERBOSE = False                 # Verbose-mode default to False.


## Dataclasses.

""" Datum

Storage for either sim or sensor datum.
"""
@dataclass
class Datum:
    timestamp:  datetime
    VWC:        float
    SC:         float = None
    ST:         float = None

""" Sensor

Sensor data from either a location in sim or a sensor.
"""
class Sensor(object):
    def __init__(
            self,
            coordinates: [float, float],    #   [lat, lon]
            data: list[Datum],
            depth: float,
            layer: int,
            name: str
            ):
        self.coordinates = coordinates
        self.data = data
        self.depth = depth
        self.layer = layer
        self.name = name

    """ get_vwc_max()

    @return Max VWC.
    """
    def get_vwc_max(self) -> float:
        return max([datum.VWC for datum in self.data])

## Helper functions.

""" _find(key, configs)

Recursively find the value of a specific key in a layered dictionary.

@param  key
@param  configs
"""
def _find(query: str, configs: dict) -> Union[str, None]:
    if query in configs.keys():
        return str(configs[query])
    # Recur deeper each dictionary until something is found.
    for key, val in configs.items():
        if isinstance(val, dict):
            found = _find(key, configs)
            if found is not None:
                return found
        # Check each child in array for query as well.
        if isinstance(val, list):
            for child in val:
                if isinstance(child, dict):
                    found = _find(query, child)
                    if found is not None:
                        return found
    # Return None if query not found.
    return None


""" Field

Class for holding each Field node info.
"""
class Field(object):
    def __init__(
            self,
            altitude: float = 0,
            coordinates: [float, float] = [0, 0],
            x: int = -1,
            y: int = -1,
            name: str = "",
            swc: [float] = []):
        self.altitude = altitude
        self.coordinates = coordinates
        self.x = x
        self.y = y
        self.name = name
        self.swc = swc 

    def __repr__(self):
        return str({
                "Altitude": str(self.altitude),
                "Latitude": str(self.coordinates[0]),
                "Longitude": str(self.coordinates[1]),
                "X": str(self.x),
                "Y": str(self.y),
                "Name": self.name,
                "SW": [str(layer_val) for layer_val in self.swc]
                })


""" Farm

Class for holding details about the simulation together.
"""
class Farm(object):
    def __init__(
            self,
            path_apsimx: str = "",
            path_dir_geojson: str = "",
            ):
        self.altitude = None 
        self.latitude = None 
        self.longitude = None 
        self.ll15 = None
        self.dul = None
        self.sat = None
        self.fields = [] 
        self.sensors = []

        # Field configs.
        self.field_radius = 0.0001  # The radius in GPS coordinates of a Field.
        self.fields_margin = 6      # Number of Fields bordering the Farm on
                                    # each side.

        self.path_apsimx = path_apsimx
        self.path_dir_geojson = path_dir_geojson
        # Import configs from .apsimx file if provided.
        self._import_apsimx()
        self.load_sensor_dir()

    def __repr__(self):
         return "\r\n".join([
             "FARM:",
             f"\tAltitude: {self.altitude}",
             f"\tLatitude: {self.latitude}",
             f"\tLongitude: {self.longitude}",
             f"\tLL15: {str(self.ll15)}",
             f"\tDUL: {str(self.dul)}",
             f"\tSAT: {str(self.sat)}"
             ])

    """ _import_apsimx()

    Load configs from provided .apsimx file.
    """
    def _import_apsimx(self):
        try:
            with open(self.path_apsimx, 'r') as apxp:
                configs = json.load(apxp)
                self.altitude = _find("Altitude", configs)
                self.latitude = _find("Latitude", configs)
                self.longitude = _find("Longitude", configs)
                self.ll15 = _find("LL15", configs)
                self.dul = _find("DUL", configs)
                self.sat = _find("SAT", configs)
                self.boundary = {
                    "N": float(self.latitude),
                    "S": float(self.latitude),
                    "E": float(self.longitude),
                    "W": float(self.longitude)
                }
                print(f"SUCCESS: Loaded configs from {self.path_apsimx}!")

        except FileNotFoundError:
            print(f"ERROR: {self.apsimx_path} does not exist!")
        except json.JSONDecodeError:
            print(f"ERROR: {self.apsimx_path} not properly formatted!")

    """ _ingest_sensor_data_single_dict(data_json) -> Sensor, crs

    @param  data_json   (dict)      Data from a sensor saved as a dict.
    @return             (Sensor)    Translated data.
    @return crs         (str)       Coordinate reference system used (if any).
    """
    def _ingest_sensor_data_single_dict(self, data_json: dict) -> Sensor:
        # The below table translates each layer simulated to a range of soil
        # depths by layer index.
        depth_lut = {
            "0": [0.0,0.199],
            "1": [0.2,0.399],
            "2": [0.4,0.599],
            "3": [0.6,0.799],
            "4": [0.8,0.999],
            "5": [1.0,0.1199],
            "6": [1.2,0.1399],
            "7": [1.4,0.1599],
            "8": [1.6,0.1799],
            "9": [1.8,0.1999]
        }
        data = []
        name = data_json["name"]
        # Assume coordinates and depth do not change before the file entry.
        # NOTE: For some reason, coordinates are output as ["lon", "lat"] here.
        coordinates = [
                data_json["features"][-1]["geometry"]["coordinates"][1],
                data_json["features"][-1]["geometry"]["coordinates"][0]
                ]

        crs = None  # TODO(nubby)
        depth = data_json["features"][-1]["properties"]["depth"]
        layer = -1  # Index of layer based on sensor depth.
        for index, depth_range in depth_lut.items():
            if (depth >= depth_range[0] and depth <= depth_range[1]):
                layer = int(index)
                break
        [data.append(Datum(
                timestamp=datetime.strptime(
                    entry["properties"]["ts"],
                    "%Y-%m-%d %H:%M:%S"
                ),
                SC=entry["properties"]["SC"],
                ST=entry["properties"]["ST"],
                VWC=entry["properties"]["WC"]
        )) for entry in data_json["features"]]
        return Sensor(
            coordinates=coordinates,
            data=data,
            depth=depth,
            layer=layer,
            name=name
        ), crs

    """ _update_boundary(coordinates)

    Expand the border of the Farm in the direction of the new set of
    coordinates.

    @param  coordinates ([float, float])  Latitude, longitude.
    """
    def _update_boundary(self, coordinates: [float, float]):
        if coordinates[0] < self.boundary["S"]:
            self.boundary["S"] = coordinates[0]
        if coordinates[0] > self.boundary["N"]:
            self.boundary["N"] = coordinates[0]
        if coordinates[1] < self.boundary["W"]:
            self.boundary["W"] = coordinates[1]
        if coordinates[1] > self.boundary["E"]:
            self.boundary["E"] = coordinates[1]
        print(str(self.boundary), str(coordinates))

    """ check_in_farm(coordinates) -> bool
    Are the coordinates within the Farm boundaries?

    @param  coordinates [float, float]  Latitude, longitude.
    """
    def check_in_farm(self, coordinates: [float, float]):
        if ((coordinates[0] >= self.boundary["S"]) and
            (coordinates[0] <= self.boundary["N"]) and
            (coordinates[1] >= self.boundary["W"]) and
            (coordinates[1] <= self.boundary["E"])):
            return True
        return False
        
    """ add_sensor(sensor)
    Add sensor to Farm and adjust boundaries if needed.

    @param  sensor  (Sensor)
    @param  verbose (bool)      Verbose mode?

    @todo   Convert sensor depth into sim depth.
    @todo   Extract initial sensor values.
    @todo   Generate a "sim farm" rectangle of sufficient size to cover sensors.
    @todo   Set the lowest layers of SWC to DUL/SAT, highest to LL15.
    @todo   Predict SWC for intermediary fields.
    @todo   Predict SWC for boundary fields.
    @todo   Allow for integration with simulation as it runs.
    @todo   Export initial configs as .json.
    @todo   Reintegrate with CLI.
    """
    # TODO
    def add_sensor(self, sensor: Sensor, verbose: bool = False):
        self.sensors.append(sensor)
        if (not self.check_in_farm(sensor.coordinates)):
            self._update_boundary(sensor.coordinates)
        print("うまい") if verbose else print("DONE.")

    """ load_sensor_file(data_path)

    Load data from a sensor data file.

    @param  data_path   Path to GEOJSON-formatted sensor data.
    """
    def load_sensor_file(self, data_path: str, verbose: bool = False):
        if data_path.split(".")[-1] != "geojson":
            print(f"ERROR: {data_path} not a supported format!")
            return

        print(f"Ingesting sensor data from {data_path}...")
        with open(data_path, "r+") as gjp:
            raw_data = geojson.load(gjp)
            sensor, crs = self._ingest_sensor_data_single_dict(raw_data)
            print(str(sensor.get_vwc_max()))
            self.add_sensor(sensor, verbose)

    """ load_sensor_dir(dir_path, verbose)
    """
    def load_sensor_dir(self, dir_path: str = "", verbose: bool = False):
        if dir_path:
            self.path_dir_geojson = dir_path
        else:
            print("No path given.")
        data_files = os.listdir(path=self.path_dir_geojson)
        # Look for valid .geojson files in a directory.
        if any("geojson" in file for file in data_files):
            sensor_data_paths = [
                os.path.join(
                    self.path_dir_geojson,
                    file
                ) for file in data_files if "geojson" in file]
            # Try to load sensor data.
            [self.load_sensor_file(
                file_path) for file_path in sensor_data_paths]

    
    """ _get_field_indices(coordinates)

    Return the indices of a given set of GPS coordinates.

    @param  coordinates Lat, lon. 
    @return Indices in the self.fields matrix.
    """
    def _get_field_indices(self, coordinates: [float, float]) -> [int, int]:
        if not self.check_in_farm(coordinates):
            print("ERROR: Coordinates not located in Farm!")
            return [-1, -1]

        # Calculate the offsets from boundaries.
        offset_north = coordinates[0] - self.boundary["S"]
        offset_east = coordinates[1] - self.boundary["W"]
        
        # Find the boundaries of the Fields in which the coordinates are
        # located.
        row = math.floor(offset_north / (2 * self.radius))
        col = math.floor(offset_east / (2 * self.radius))

        return [row, col]

    """ _initialize_fields()

    Create an empty matrix of Fields that span the entire Farm.
    """
    def _initialize_fields(self):
        field_index = 0
        for i in range(self.length):
            row = []
            for j in range(self.width):
                # Place each Field at the center of their coordinates.
                coordinates = [self.boundary["N"] - (
                    i * 2 * self.radius - self.radius),
                               self.boundary["W"] + (
                    j * 2 * self.radius + self.radius)]
                """
                row.append(Field(
                    coordinates=coordinates,
                    x=j,
                    y=i,
                    altitude=self.altitude,
                    name=f"Field{field_index}",
                    swc=self.sat))  # Initialize Fields with saturated water
                                    # content.
                """
                row.append(Field(
                    coordinates=coordinates,
                    x=j,
                    y=i,
                    altitude=self.altitude,
                    name=f"Field{field_index}",
                    swc=self.dul))  # Initialize Fields with saturated water
                                    # content.
                field_index += 1
            self.fields.append(row)
    

    """ _infer_field_swc()
    
    Infer SWC for each Field based on initial sensor readings.
    """
    def _infer_field_swc(self):
        for sensor in self.sensors:
            # Get the location of a given sensor.
            [x, y] = self._get_field_indices(sensor.coordinates)
            # Find the initial SWC at that location.
            # TODO: Make all SWC/VWC/SW conventions align.
            swc = [sensor.data[0].VWC for _ in range(len(self.dul))]

    """ build()

    Generate an array of Fields.

    @param  margin  The number of Fields to add in each direction around sensor
                    locations.
    @param  radius  Length/Width of each Field node.

    @todo   density The min number of Fields to create for a given Farm
                    geometry.
    @todo   Move to using rasters.
    """
    def build(
            self,
            margin: int = 6,
            radius: float = 0.0001):
        if radius:
            self.radius = radius
        if margin:
            self.margin = margin

        # 1. Redefine Farm boundaries with margin.
        self._update_boundary([
            self.boundary["S"] - self.radius * self.margin,
            self.boundary["W"] - self.radius * self.margin])
        self._update_boundary([
            self.boundary["N"] + self.radius * self.margin,
            self.boundary["E"] + self.radius * self.margin])
        ## Find the dimensions of the grid.
        self.length = math.ceil(
                (self.boundary["N"] - self.boundary["S"]) / (2 * self.radius))
        self.width = math.ceil(
                (self.boundary["E"] - self.boundary["W"]) / (2 * self.radius))

        # 2. Initialize Farm SWC.
        ## Initialize Field matrix.
        self._initialize_fields()
        ## Map sensor initial data to appropriate Fields.
        ## Infer SWC for Fields without sensors.
        self._infer_field_swc()

    """ export_field_configs(path_output)

    @param  path_output
    """
    def export_field_configs(self, path_output: str, verbose: bool = False):
        farm_dict = []
        for row in self.fields:
            for field in row:
                farm_dict.append({
                    "Altitude": str(field.altitude),
                    "Latitude": str(field.coordinates[0]),
                    "Longitude": str(field.coordinates[1]),
                    "X": str(field.x),
                    "Y": str(field.y),
                    "Radius": str(self.radius),
                    "Name": field.name,
                    "SW": field.swc
                    })
        print("Milling grist...") if verbose else print(
                f"Generating configs at {path_output}...")
        with open(path_output, "w") as po:
            json.dump(farm_dict, po, indent=4)
        print(f"Grist millt upon {path_output}.") if verbose else print("DONE.")

    """ export_apsimx(path_output)

    @param  path_output
    """
    def export_apsimx(self, path_output: str, verbose: bool = False):
        pass

""" generate_json_configs(farm_dict, path_output)

Write the details of a flight plan to a JSON file.

@param  farm_dict       A list of configurations that define characteristics of
                            each generated Field.
@param  path_output     Path to output JSON file.
"""
def generate_json_configs(
        farm_dict: list[dict],
        path_output: str,
        verbose: bool = False):
    print("Milling grist...") if verbose else print(
            f"Generating configs at {path_output}...")
    with open(path_output, "w") as po:
        json.dump(farm_dict, po, indent=4)
    print(f"Grist millt upon {path_output}.") if verbose else print("DONE.")


# Deprecate the below?
""" generate_data(configs, mode)

Grist for The Mill.
Generate a set of configurations for each Field node.

@param  configs     Base configurations for entire simulation.
@param  mode        Mapping of initial VWC for each node:
                        "n" = "naive"
                        "a" = "average"
                        "l" = "minimum"
                        "u" = "maximum"
@return Configurations for each Field node.
"""
def generate_data(
        configs: dict,
        mode: str = "a") -> list[dict]:
    data = []
    field_config = {
            "Name": "",
            "Radius": "",
            "SW": "",
            "X": "",
            "Y": "",
            "Altitude": ""
            }

    index = 0
    for i in range(0, configs.dim_x):
        for j in range(0, configs.dim_y):
            for k in range(0, configs.dim_z):
                fresh_field_config = copy.deepcopy(field_config)
                fresh_field_config["Name"] = f"Field{index}"
                fresh_field_config["Radius"] = str(configs.r)
                if mode == "a":
                    fresh_field_config["SW"] = str(0.160657)    # Avg init VWC.

                elif mode == "l":
                    fresh_field_config["SW"] = str(configs.vwc_min)
                elif mode == "u":
                    fresh_field_config["SW"] = str(configs.vwc_max)
                else:
                    fresh_field_config["SW"] = str(
                            random.uniform(configs.vwc_min, configs.vwc_max)
                            )
                fresh_field_config["X"] = str(configs.spacing * i)
                fresh_field_config["Y"] = str(configs.spacing * j)
                fresh_field_config["Altitude"] = str(configs.spacing * k)
                data.append(fresh_field_config)
                index += 1
    return data







"""_ingest_sensor_data_geojson(data_paths, IRLFarm, verbose=False) -> data

@param  data_paths  (list[str]) 
@param  IRLFarm     (Farm)
@param  verbose     (bool)      Verbose mode?
"""
def _ingest_sensor_data_geojson(
        data_paths: list[str],
        IRLFarm: Farm,
        verbose: bool = False
    ):
    for file in data_paths:
        print(f"Ingesting sensor data from {file}...")
        with open(file, "r+") as fp:
            raw_data = geojson.load(fp)
            sensor, crs = _ingest_sensor_data_single_dict(raw_data)
            IRLFarm.add_sensor(sensor, verbose)
    return crs

"""_ingest_sensor_data_csv(data_path) -> data
"""
def _ingest_sensor_data_csv(data_path: str, IRLFarm: Farm):
    # Set the path to farm sensor data.
    farm_data_path = None
    for file in data_files:
        if "csv" in file:
            farm_data_path = file
            break
    assert farm_data_path   # Raise assertion error if farm data not found.

    # Extract information about each sensor used through the main farm CSV file.
    csv_lines = []
    with open(farm_data_path, "r+") as fdp:
        reader = csv.reader(fdp)
        for row in reader:
            csv_lines += row

    return None

"""_get_sensor_data( data_path, data_files, verbose=False) -> crs 

@return crs (str)   Coordinate reference system used.
"""
def _get_sensor_data(
        data_path: str,
        data_files: list[str],
        IRLFarm: Farm,
        verbose: bool = False
    ) -> str:
    # Read .geojson-formatted sensor data if pre-processed, otherwise read
    # .csv-formatted sensor data.
    if any("geojson" in file for file in data_files):
        sensor_data_paths = [
            os.path.join(
                data_path,
                file
            ) for file in data_files if "geojson" in file
        ]
        crs = _ingest_sensor_data_geojson(sensor_data_paths, IRLFarm, verbose)
    elif any("csv" in file for file in data_files):
        sensor_data_path = [os.path.join(
            data_path,
            file
        ) for file in data_files if "csv" in file][0]
        crs = _ingest_sensor_data_csv(sensor_data_path, IRLFarm)
    else:
        raise IOError

    return crs

"""_ingest_sim_data_single_dict(data_tiff, IRLSensor) -> Sensor

@param  coordinates
@param  data_rio   ()          Raster data from a GeoTIFF file..
@param  depth
@param  name

@return             (Sensor)    Translated data.
"""
def _ingest_sim_data_single_sensor(
        coordinates: tuple[float],
        data_rio: any, # TODO(nubby)
        depth: float,
        name: str,
        start_ts: datetime
        ) -> Sensor:
    data = []
    ts = start_ts
    td_24hrs = timedelta(days=1)
    for index in data_rio.indexes:
        try:
            band = data_rio.read(index)
            # TODO: Is this the proper way to index?
            data.append(Datum(
                timestamp=ts,
                VWC=band[coordinates[0]-1, coordinates[1]-1]
            ))
        except IndexError:
            # Some raster frames are deficient, but not a problem so long as
            # we keep track of time.
            print(
                    "Height: "+str(data_rio.height),
                    "Width: "+str(data_rio.width),
                    "COORDS: "+str(coordinates)," failed")
        finally:
            # Always advance a day, even when a sample is missing.
            ts = ts + td_24hrs
    if len(data) == 0:
        print(f"FAILED: Sim {name}.")

    return Sensor(
        coordinates=coordinates,
        data=data,
        depth=depth,
        name=name
    )

"""_ingest_sim_data_tiff(data_paths, sensors, SimFarm, crs)
"""
def _ingest_sim_data_tiff(
        data_paths: list[str],
        sensors: list[Sensor],
        SimFarm: Farm,
        crs: dict = None
    ):
    regex = re.compile(r".*([0-9]).*")
    depth_lut = {
        "0": [0.0,0.199],
        "1": [0.2,0.399],
        "2": [0.4,0.599],
        "3": [0.6,0.799],
        "4": [0.8,0.999],
        "5": [1.0,0.1199],
        "6": [1.2,0.1399],
        "7": [1.4,0.1599],
        "8": [1.6,0.1799],
        "9": [1.8,0.1999]
    }
    for sensor in sensors:
        for file in data_paths:
            try:
                check = regex.match(file)
                depth_code = check.group(1)
                depth_range = depth_lut[depth_code]
            except AttributeError:
                # Skip files with name formatting issues.
                continue
            if (
                sensor.depth >= depth_range[0] and
                sensor.depth <= depth_range[1]
            ):
                print(f"Ingesting sim data from {file}...")
                dataset = rasterio.open(file)
                # TODO(nubby): Translate to uniform coordinates.
                """
                # NOTE: Look at rio.Env() and dst_transform
                x_delta = 
                transform = Affine(
                    1.0, 0.0, x_delta / width,  # x transform.
                    0.0, 1.0, y_delta / height  # y transform.
                )
                translator = dataset.transform.AffineTransformer(transform)j
                print(dataset.bounds, sensor.coordinates)
                """
                x, y = dataset.index(
                    sensor.coordinates[0],
                    sensor.coordinates[1]
                )
                SimFarm.add_sensor(_ingest_sim_data_single_sensor(
                    coordinates=[x, y],
                    data_rio=dataset,
                    depth=sensor.depth,
                    name=sensor.name,
                    start_ts=sensor.data[0].timestamp
                ))
                dataset.close()




"""_ingest_sim_data_npy(data_path) -> data
"""
def _ingest_sim_data_npy(data_path: str, crs: dict = None):
    # TODO(nubby)
    return None

"""_get_sim_data(data_path, data_files, SimFarm, crs=None, verbose=False)
Digest real sensor coordinates to generate simulated sensors.

@param  data_path   (str)
@param  data_files  (list[str])
@param  sensors     (list[Sensor])
@param  SimFarm     (Farm)
@param  crs         (dict)                  [optional] Use native crs if none
                                            given.
@param  verbose     (bool)                  Verbose mode?
"""
def _get_sim_data(
        data_path: str,
        data_files: list[str],
        sensors: list[Sensor],
        SimFarm: Farm,
        crs: dict = None,
        save: bool = True,
        verbose: bool = False
    ) -> list[Sensor]:
    # Read .tiff-formatted sim data if pre-processed, otherwise read .npy data.
    if any("tiff" in file for file in data_files):
        sim_data_paths = [
            os.path.join(
                data_path,
                file
            ) for file in data_files if "tiff" in file
        ]
        _ingest_sim_data_tiff(
            data_paths=sim_data_paths,
            sensors=sensors,
            SimFarm=SimFarm,
            crs=crs
        )
    elif any("npy" in file for file in data_files):
        sim_data_path = [os.path.join(
            data_path,
            file
        ) for file in data_files if "npy" in file][0]
        _ingest_sim_data_npy(sim_data_path, crs)
    else:
        raise IOError

"""_get_avg_sensor(sensor) -> Sensor
Average all data throughout a day.

@param  sensor  (Sensor)
@param
@return         (Sensor)    Sensor with daily-averaged data.
"""
def _get_avg_sensor(sensor: Sensor, hours: float = 24) -> Sensor:
    t_delta = hours * 60 * 60   # Seconds between averaged data.
    data_avg = []
    # Initialize the timestamp for comparison.
    start_ts = int(sensor.data[0].timestamp.timestamp())
    ts = start_ts
    # Setup a running averager dummy.
    datum_running = Datum(timestamp=sensor.data[0].timestamp, VWC=0)
    data_count = 1
    for datum in sensor.data:
        # When the timestamp has advanced a day, average all values and save.
        if (ts - start_ts >= t_delta):
            start_ts = ts
            datum_running.VWC /= data_count
            data_avg.append(copy.deepcopy(datum_running))
            datum_running = Datum(
                timestamp=datetime.fromtimestamp(ts),
                VWC=datum.VWC
            )
            data_count = 1
        else:
            datum_running.VWC += datum.VWC
            data_count += 1
        ts = int(datum.timestamp.timestamp())
    # Capture the last datum.
    datum_running.VWC /= data_count
    data_avg.append(copy.deepcopy(datum_running))
    datum_running = Datum(
        timestamp=datetime.fromtimestamp(ts),
        VWC=datum.VWC
    )
    return Sensor(
        coordinates=sensor.coordinates,
        data=data_avg,
        depth=sensor.depth,
        name=sensor.name
    )












# Function defs.
""" generate_json_configs(farm_dict, path_output)

Write the details of a flight plan to a JSON file.

@param  farm_dict       A list of configurations that define characteristics of
                            each generated Field.
@param  path_output     Path to output JSON file.
"""
def generate_json_configs(
        farm_dict: list[dict],
        path_output: str,
        verbose: bool = False):
    print("Milling grist...") if verbose else print(
            f"Generating configs at {path_output}...")
    with open(path_output, "w") as po:
        json.dump(farm_dict, po, indent=4)
    print(f"Grist millt upon {path_output}.") if verbose else print("DONE.")

""" generate_csv_configs(farm_dict, fpath)

Write the details of a flight plan to a CSV file.

@param  farm_dict       A list of configurations that define characteristics of
                            each generated Field.
@param  path_output     Path to output CSV file.
"""
def generate_csv_configs(
        farm_dict: list[dict],
        path_output: str,
        verbose: bool = False):
    print("Milling grist...") if verbose else print(
            f"Generating configs at {path_output}...")
    with open(path_output, "w", newline="") as csvp:
        writer = csv.DictWriter(csvp, fieldnames=farm_dict[0].keys())
        writer.writeheader()
        [writer.writerow(datum) for datum in farm_dict]
    print(f"Grist millt upon {path_output}.") if verbose else print("DONE.")


""" _sensor_data_to_initial_configs(path_input)

Extract [sparse] initial conditions from sensor data.
"""
def _sensor_data_to_initial_configs(path_input: str) -> list[dict]:
    initial_conditions = {}

""" generate_farm_configs(input, output, verbose)

"""
def generate_farm_configs(
        path_apsimx: str,
        path_dir_geojson: str,
        path_output: str,
        verbose: bool = False
        ):
    farm = Farm(path_apsimx=path_apsimx, path_dir_geojson=path_dir_geojson)
    farm.build()
    farm.export_field_configs(path_output) 


if __name__ == "__main__":
    path_apsimx = "/Users/nubby/Documents/Research/OASIS/sim/Tests/Simulation/ZMQ-Sync/MetompkinFarm/MetompkinFarm.apsimx"
    path_dir_geojson = "/Users/nubby/Documents/Research/OASIS/sim/Tools/PostProcessing/data/"
    output_path ="out.json"
    farm = Farm(path_apsimx=path_apsimx, path_dir_geojson=geojson_path)
    farm.build()
    farm.export_field_configs(output_path) 
