"""Test file for raster.py"""

import unittest
from oasis.raster import Rasterize
import numpy as np


class TestRasterApsim(unittest.TestCase):

    def setUp(self):
        """Set up test data

        Test data representing 365 days of 10x10 grid with 8 soil layers.
        Values at each timesteps are set to their index.
        """
        self.test_data = np.ones((365, 10, 10, 8), dtype=np.float32)
        for i in range(self.test_data.shape[0]):
            self.test_data[i] *= i

    def test_init_defaults(self):
        """Test the init method"""
        raster = Rasterize(self.test_data)
        self.assertIsNone(raster.xlim)
        self.assertIsNone(raster.ylim)
        self.assertIsNone(raster.transform)
        self.assertEqual(raster.epsg, 4326)

    def test_init_params(self):
        """Test the init method"""
        raster = Rasterize(
            self.test_data,
            xlim=(-75.5838, -75.5833),
            ylim=(37.7427, 37.7448),
            epsg=26944,
        )
        self.assertEqual(raster.xlim, (-75.5838, -75.5833))
        self.assertEqual(raster.ylim, (37.7427, 37.7448))
        self.assertIsNotNone(raster.transform)
        self.assertEqual(raster.epsg, 26944)

    def test_crs(self):
        """Test the crs method"""
        raster = Rasterize(self.test_data)
        crs = raster.crs(26944)
        self.assertEqual(raster.epsg, 26944)
        self.assertEqual(crs.to_epsg(), 26944)

    def test_save(self):
        """Test the save method"""
        raster = Rasterize(
            self.test_data,
            xlim=(-75.5838, -75.5833),
            ylim=(37.7427, 37.7448),
        )
        raster.save(".", "test_")
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
