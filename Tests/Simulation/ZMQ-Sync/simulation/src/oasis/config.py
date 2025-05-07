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
import os
import random

from dataclasses import dataclass


""" generate_csv_fields(input, output, verbose)
"""
def generate_csv_fields(
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
        vwc_min: float = 0.1    # Gallons?
        vwc_max: float = 2.0    # Gallons?
        r: float = 0.5          # Acres?
        spacing: int = 1        # Acres?

    configs = OasisConfigs()
    grist = generate_data(configs, mode="a")
    generate_csv_from_grist(grist, path_output)

""" generate_csv_from_grist(grist, fpath)

Write the details of a flight plan to a CSV file.

@param  grist   A list of configurations that define characteristics of each
                generated Field.
@param  fpath   Path to output CSV file.
"""
def generate_csv_from_grist(
        grist: list[dict],
        fpath: str,
        verbose: bool = False
        ):
    print("Milling grist...") if verbose else print("Generating configs...")
    with open(fpath, "w", newline="") as csvp:
        writer = csv.DictWriter(csvp, fieldnames=grist[0].keys())
        writer.writeheader()
        [writer.writerow(datum) for datum in grist]
    print(f"Grist millt upon {fpath}.") if verbose else print("DONE.")


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
        mode: str = "n"
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
                    fresh_field_config["SW"] = str(
                            (configs.vwc_max - configs.vwc_min) / 2
                            )
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

if __name__ == "__main__":
    pass
