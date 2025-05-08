#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@file   config.py

Configuration for OASIS simulation using Apsim.
Kraww!!

@author     jLab
@author     HARE Lab

@date       7 Apr 2025
@version    1.0.1
"""
import copy
import csv
import json
import os
import random

from dataclasses import dataclass


""" generate_farm_configs(input, output, verbose)

"""
def generate_farm_configs(
        path_input: str,
        path_output: str,
        verbose: bool = False
        ):
    # Create path if doesn't already exist.
    dir_path = os.path.dirname(path_output)
    if dir_path and not os.path.exists(path_output):
        os.makedirs(os.path.dirname(path_output), exist_ok=True)

    # Number of fields in each dimension of spacetime.
    # TODO(nubby): Reformat to map initial sensor data to this.
    @dataclass
    class OasisConfigs:
        dim_x: int = 16         # Number of nodes in one direction.
        dim_y: int = 16
        dim_z: int = 1          # Altitude.
        layers: int = 10        # Layers per node.
        vwc_min: float = 0.1    # Gallons?
        vwc_max: float = 2.0    # Gallons?
        r: float = 0.5          # Acres?
        spacing: int = 1        # Acres?

    # Generate a matrix of Field node configurations based on input data.
    configs = OasisConfigs()
    farm_dict = generate_data(configs, mode="a")

    # Write Farm configs to an output file.
    # TODO(nubby): Deprecate CSV.
    output_type = path_output.split(".")[-1]
    if output_type == "csv":
        generate_csv_configs(farm_dict, path_output, verbose)
    elif output_type == "json":
        generate_json_configs(farm_dict, path_output, verbose)

""" generate_json_configs(farm_dict, path_output)

Write the details of a flight plan to a JSON file.

@param  farm_dict       A list of configurations that define characteristics of
                            each generated Field.
@param  path_output     Path to output JSON file.
"""
def generate_json_configs(
        farm_dict: list[dict],
        path_output: str,
        verbose: bool = False
        ):
    print("Milling grist...") if verbose else print("Generating configs...")
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
        verbose: bool = False
        ):
    print("Milling grist...") if verbose else print("Generating configs...")
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
        mode: str = "a"
        ) -> list[dict]:
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

if __name__ == "__main__":
    pass
