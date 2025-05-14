#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@file   config.py

Configuration for OASIS simulation using Apsim.
Kraww!!

@author     jLab
@author     HARE Lab

@date       12 Apr 2025
@version    1.0.2
"""
import copy
import csv
import json
import os
import random

from dataclasses import dataclass
from typing import Union

#from simulation import FieldNode


# Module-level defs.
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

""" Farm

Class for holding details about the simulation together.
"""
class Farm(object):
    def __init__(self, apsimx_path: str = ""):
        self.altitude = None 
        self.latitude = None 
        self.longitude = None 
        self.ll15 = None
        self.dul = None
        self.sat = None
        self.fields = [] 

        self.apsimx_path = apsimx_path
        # Import configs from .apsimx file if provided.
        self._import_conifgs()

    def __repr__(self):
         return "\r\n".join([
             "FARM:",
             f"\tAltitude: {self.altitude}",
             f"\tLatitude: {self.latitude}",
             f"\tLongitude: {self.longitude}",
             f"\tLL15: {str(self.ll15)}",
             f"\tDUL: {str(self.dul)}",
             f"\tSAT: {str(self.sat)}",
             ])

       

    def _import_conifgs(self):
        try:
            with open(self.apsimx_path, 'r') as apxp:
                configs = json.load(apxp)
                self.altitude = _find("Altitude", configs)
                self.latitude = _find("Latitude", configs)
                self.longitude = _find("Longitude", configs)
                self.ll15 = _find("LL15", configs)
                self.dul = _find("DUL", configs)
                self.sat = _find("SAT", configs)
                print(f"SUCCESS: Loaded configs from {self.apsimx_path}!")

        except FileNotFoundError:
            print(f"ERROR: {self.apsimx_path} does not exist!")
        except json.JSONDecodeError:
            print(f"ERROR: {self.apsimx_path} not properly formatted!")


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
                    """
                    fresh_field_config["SW"] = str(
                            (configs.vwc_max - configs.vwc_min) / 2
                            )
                    """
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
        print(str(data))
    return data

""" _sensor_data_to_initial_configs(path_input)

Extract [sparse] initial conditions from sensor data.
"""
def _sensor_data_to_initial_configs(path_input: str) -> list[dict]:
    initial_conditions = {}

""" generate_farm_configs(input, output, verbose)

"""
def generate_farm_configs(
        path_input: str,
        path_output: str,
        verbose: bool = False
        ):
    # Generate initial conditions from sensor data if available;
    # else programmatically generate them from a guess.
    configs = _sensor_data_to_initial_configs(
            path_input=path_input) if path_input else DEFAULT_CONFIGS

    # Create path if doesn't already exist.
    dir_path = os.path.dirname(path_output)
    if dir_path and not os.path.exists(path_output):
        os.makedirs(os.path.dirname(path_output), exist_ok=True)

    # Generate a matrix of Field node configurations based on input data.
    farm_dict = generate_data(configs, mode="a")

    # Write Farm configs to an output file.
    # TODO(nubby): Deprecate CSV.
    output_type = path_output.split(".")[-1]
    if output_type == "csv":
        generate_csv_configs(farm_dict, path_output, verbose)
    elif output_type == "json":
        generate_json_configs(farm_dict, path_output, verbose)


if __name__ == "__main__":
    apsimx_path = "/Users/nubby/Documents/Research/OASIS/sim/Tests/Simulation/ZMQ-Sync/MetompkinFarm/MetompkinFarm.apsimx"
    farm = Farm(apsimx_path=apsimx_path)
    print(farm)
