#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@file   config.py

Configuration for OASIS simulation using Apsim.
Kraww!!

@author jLab

@date   7 Apr 2025
"""

import copy
import csv
import random


def generate_csv_from_grist(grist: list[dict], fpath: str):
    """Write the details of a flight plan to a CSV file."""
    print("Milling grist...")
    with open(fpath, "w", newline="") as csvp:
        writer = csv.DictWriter(csvp, fieldnames=grist[0].keys())
        writer.writeheader()
        [writer.writerow(datum) for datum in grist]
    print(f"Grist millt upon {fpath}.")


def generate_data(
        configs: dict,
        mode: str = "n"
        ) -> list[dict]:
    """generate_data(configs, mode)
    Grist for The Mill.
    Generate a set of configurations for each Field node.

    @param  configs     (dict)          Base configurations for entire
                                        simulation.
    @param  mode        (str)           Mapping of initial VWC for each node:
                                            "n" = "naive"
                                            "a" = "average"
                                            "l" = "minimum"
                                            "u" = "maximum"
    @return sim_setup   (list[dict])    Configurations for each Field node.
    """
    data = []
    field_config = {
            "Name": "",
            "Radius": "",
            "SW": "",
            "X": "",
            "Y": "",
            "Z": ""
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
                fresh_field_config["Z"] = str(configs.spacing * k)
                data.append(fresh_field_config)
                index += 1
    return data
