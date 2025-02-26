#!/usr/bin/env python

import argparse
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import json
import os

from .apsim import ApsimController
from .simulation import Simulation
from .plots import plot_vwc_layer, plot_vwc_field_grid, plot_heatmap
from .config import generate_csv_from_grist, generate_data
from .raster import Rasterize
from .metompkin import MetompkinConverter


def client(args):
    """Starts oasis client

    See argparser set_defaults() (https://docs.python.org/3/library/argparse.html#sub-commands)
    """

    # initialize connection
    apsim = ApsimController(args.config, addr=args.addr, port=args.port)

    sim = Simulation(apsim, args.config)

    sim.add_action(datetime(2023, 1, 1), "irrigate", [1, 1, 0, 10000])

    # add any commands here
    ts_arr, vwc_arr = sim.run()
    if args.output:
        np.save(args.output, vwc_arr)

    # Plot simulation.
    # TODO(nubby): Integrate irrigation with colors.
    # plot_oasis(apsim)
    #if not args.quiet:
    #    plot_vwc_layer(ts_arr, vwc_arr)
    #    plot_vwc_field_grid(ts_arr, vwc_arr)
    
    # nubby's code 
    #plot_vwc_layer(ts_arr, vwc_arr)
    #plot_vwc_field_grid(ts_arr, vwc_arr)
    plot_heatmap(args.anim, ts_arr, vwc_arr)


def kraww(args):
    """Procedurally generate a CSV file of APSIM Field configs.

    See argparser set_defaults() (https://docs.python.org/3/library/argparse.html#sub-commands)
    """

    # create path if doesn't already exist
    dir_path = os.path.dirname(args.path)
    if dir_path and not os.path.exists(args.path):
        os.makedirs(os.path.dirname(args.path), exist_ok=True)

    # Number of fields in each dimension of spacetime.
    @dataclass
    class GristConfigs:
        dim_x: int = 4
        dim_y: int = 4
        dim_z: int = 1

    configs = GristConfigs()
    grist = generate_data(configs)
    generate_csv_from_grist(grist, args.path)

def raster(args):
    """Generate tiff files vwc numpy array

    See argparser set_defaults() (https://docs.python.org/3/library/argparse.html#sub-commands)
    """

    raster_arry = np.load(args.input)
    raster = Rasterize(
        raster_arry,
        xlim=(-75.5838, -75.5833),
        ylim=(37.7427, 37.7448),
        epsg=4326,
    )

    raster.save(args.output, "")

def metompkin(args):
    """Create a geojson files for Metompkin farm dataset
    
    See argparser set_defaults() (https://docs.python.org/3/library/argparse.html#sub-commands)
    """

    converter = MetompkinConverter()
    converter.convert(args.path, args.json)

def entry():
    """Entry point for oasis"""

    # cli interface
    parser = argparse.ArgumentParser(description="OASIS Apsim Python client")

    subparsers = parser.add_subparsers(help="Subcommand", required=True)

    client_parser = subparsers.add_parser("client", help="Runs oasis client")
    client_parser.add_argument("--interactive", action="store_true",
                               help="Plot vwc arrays")
    client_parser.add_argument("--output", type=str, help="Output directory for numpy array")
    client_parser.add_argument(
        "--addr", type=str, default="0.0.0.0", help="Server address (default: 0.0.0.0"
    )
    client_parser.add_argument(
        "--port", type=int, default=27746, help="Server port number (default: 27746)"
    )
    client_parser.add_argument("config", type=str, help="Configuration CSV")
    client_parser.add_argument("anim", type=str, help="Path to save heatmap animation")
    client_parser.set_defaults(func=client)

    config_parser = subparsers.add_parser("config", help="Generates field config csv")
    config_parser.add_argument("path", type=str, help="Path to save csv")
    config_parser.set_defaults(func=kraww)
    
    metompkin_parser = subparsers.add_parser("metompkin", help="Convert metompkin dataset")
    metompkin_parser.add_argument("path", type=str, help="Path to metopkin data")
    metompkin_parser.add_argument("json", type=str, help="Suffix of geojson files")
    metompkin_parser.set_defaults(func=metompkin)

    raster_parser = subparsers.add_parser("raster", help="Generates tiff files")
    raster_parser.add_argument("input", type=str, help="Input numpy file")
    raster_parser.add_argument("output", type=str, help="Output directory for tiff files")
    raster_parser.set_defaults(func=raster)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    entry()
