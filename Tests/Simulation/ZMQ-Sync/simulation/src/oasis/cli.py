#!/usr/bin/env python

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import os

from .apsim import ApsimController
from .simulation import Simulation
from .plots import plot_vwc_layer, plot_vwc_field_grid
from .config import generate_csv_from_grist, generate_data
from .met import MetGenerator


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

    # Plot simulation.
    # TODO(nubby): Integrate irrigation with colors.
    # plot_oasis(apsim)
    plot_vwc_layer(ts_arr, vwc_arr)
    plot_vwc_field_grid(ts_arr, vwc_arr)


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


def generate_met(args):
    """Generate met data

    See argparser set_defaults() (https://docs.python.org/3/library/argparse.html#sub-commands)
    """

    # parse json
    config_path = args.config
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    start = datetime.fromisoformat(config["start_date"])
    end = datetime.fromisoformat(config["end_date"])

    met_generator = MetGenerator(start, end, "constant", config["lat"], config["lon"])

    # save file
    met_path = args.path
    met_generator.save(met_path)


def entry():
    """Entry point for oasis"""

    # cli interface
    parser = argparse.ArgumentParser(description="OASIS Apsim Python client")

    subparsers = parser.add_subparsers(help="Subcommand", required=True)

    client_parser = subparsers.add_parser("client", help="Runs oasis client")
    client_parser.add_argument(
        "--addr", type=str, default="0.0.0.0", help="Server address"
    )
    client_parser.add_argument(
        "--port", type=int, default=27746, help="Server port number"
    )
    client_parser.add_argument("config", type=str, help="Configuration CSV")
    client_parser.set_defaults(func=client)

    config_parser = subparsers.add_parser("config", help="Generates field config csv")
    config_parser.add_argument("path", type=str, help="Path to save csv")
    config_parser.set_defaults(func=kraww)

    met_parser = subparsers.add_parser("met", help="Generate met data")
    met_parser.add_argument("config", type=str, help="Path to config json")
    met_parser.add_argument("path", type=str, help="Path to save met data")
    met_parser.set_defaults(func=generate_met)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    entry()
