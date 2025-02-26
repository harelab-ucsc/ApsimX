"""
Module for rasterizing dataa from simulation and vector sensor data

"""

import os
import numpy as np
from numpy.typing import NDArray
import rasterio
from rasterio.control import GroundControlPoint
from rasterio.transform import Affine
from rasterio.crs import CRS


class Rasterize:
    def __init__(
        self,
        data: NDArray,
        xlim: tuple | None = None,
        ylim: tuple | None = None,
        epsg: int = 4326,
    ):
        """Default constructor

        Args:
            data (dict): Dictionary containing the data to be rasterized
            xlim (tuple): List containing the x-axis limits
            ylim (tuple): List containing the y-axis limits
            epsg (int): EPSG code for the coordinate reference system
        """

        # store data
        self.data = data
        self.shape = data.shape

        # create meshgrid if limits are provided
        if (xlim is not None) and (ylim is not None):
            self.meshify(xlim, ylim)
        else:
            self.xlim = None
            self.ylim = None
            self.transform = None

        # set coordinate reference system
        self.crs(epsg)

    def meshify(self, xlim: tuple, ylim: tuple):
        """Creates a meshgrid from limits of the data

        The transform is calculated from the limits and size of data.

        """

        self.xlim = xlim
        self.ylim = ylim

        # create meshgrid of gps points
        x = np.linspace(xlim[0], xlim[1], self.shape[1])
        y = np.linspace(ylim[0], ylim[1], self.shape[2])
        X, Y = np.meshgrid(x, y)

        # Create affine translation
        res = (x[-1] - x[0]) / x.shape[0]
        self.transform = Affine.translation(
            x[0] - res / 2, y[0] - res / 2
        ) * Affine.scale(res, res)

    def crs(self, epsg):
        """Set the coordinate reference system

        Args:
            epsg (int): EPSG code

        Returns:
            Coordinate reference system object
        """

        self.epsg = epsg
        self._crs = CRS.from_epsg(epsg)
        return self._crs

    def save(self, path: str, prefix: str = ""):
        """Save data to raster files

        Overwrites the files if it already exists.

        Args:
            path (str): Path to directory
            prefix (str): Prefix for the file name
        """

        # checks for empty data
        if self.crs is None:
            raise ValueError("CRS not defined")

        if self.transform is None:
            raise ValueError("Transform not defined")

        # save each layer
        for layer in range(self.shape[3]):
            full_path = os.path.join(path, f"{prefix}{layer}.tiff")
            self.save_layer(full_path, layer)

    def save_layer(self, path: str, layer: int):
        """Save a single layer to raster file

        Overwrites the files if it already exists.

        Args:
            path (str): Path to directory
            layer (int): Layer number
        """

        # Open rasterio file
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=self.shape[1],
            width=self.shape[2],
            count=self.shape[0],
            dtype=self.data.dtype,
            crs=self._crs,
            transform=self.transform,
        ) as dst:
            # loop over data for given layer
            for idx, d in enumerate(self.data[:, :, :, layer]):
                # write each timestep to geotiff data
                dst.write(d, idx + 1)


if __name__ == "__main__":
    x = np.linspace(-75.5838, -75.5833, 240)
    y = np.linspace(37.7427, 37.7448, 180)
    X, Y = np.meshgrid(x, y)

    # Test Affine transform
    res = (x[-1] - x[0]) / x.shape[0]
    transform = Affine.translation(x[0] - res / 2, y[0] - res / 2) * Affine.scale(
        res, res
    )
    print(transform)

    # coordinate reference system (WGS84)
    crs = CRS.from_epsg(4326)

    layers = range(1, 365)

    with rasterio.open(
        "raster_test.tiff",
        "w",
        driver="GTiff",
        height=X.shape[0],
        width=X.shape[1],
        count=len(layers),
        dtype=rasterio.int16,
        crs=crs,
        transform=transform,
    ) as dst:
        for layer in layers:
            Z = np.ones_like(X) * layer
            dst.write(Z, layer)
