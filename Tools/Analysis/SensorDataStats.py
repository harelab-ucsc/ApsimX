#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SensorDataStats.py

Ingest data from one or more sensor data files, then display stats.

@description
Point this script at either a single file or a directory containing sensor data
to ingest.

Supported sensor file formats:
    * CSV 

@author     jLab
@author     HARE Lab

@date       27 Jun 2025
@version    0.0.9

@todo       Add .geojson sensor data file support.
"""

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

## Objects.
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

#

## Helpers.

"""read_teros_data_csv(base_path)

"""
def read_teros_data_csv(base_path: str) -> list[Sensor]:
    return []


"""generate_statistics(sensors)

"""
def generate_statistics(list[Sensor]):
    pass

if __name__ == "__main__":
    base_path_teros = "./SensorData/"
    teros_data = read_teros_data_csv(base_path_teros)
    generate_statistics(teros_data)
