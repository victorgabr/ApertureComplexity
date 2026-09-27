from unittest import TestCase

import numpy as np

from complexity.PyApertureMetric import PyAperture, PyLeafPair
from tests.helpers import OPEN_JAW


def make_pyaperture(lefts, rights, widths, gantry_angle=0.0):
    positions = np.array([list(lefts), list(rights)], dtype=float)
    return PyAperture(
        positions, np.array(widths, dtype=float), list(OPEN_JAW), gantry_angle
    )


class TestPyAperture(TestCase):
    def test_CreateLeafPairs(self):
        aperture = make_pyaperture([0.0, 0.0], [50.0, 50.0], [10.0, 10.0])
        self.assertEqual(len(aperture.LeafPairs), 2)
        for leaf_pair in aperture.LeafPairs:
            self.assertIsInstance(leaf_pair, PyLeafPair)

    def test_LeafPairArea(self):
        aperture = make_pyaperture([0.0, 0.0, 0.0], [50.0, 50.0, 50.0], [10.0] * 3)
        self.assertEqual(aperture.LeafPairArea, [500.0, 500.0, 500.0])

    def test_GantryAngle(self):
        aperture = make_pyaperture([0.0], [50.0], [10.0], gantry_angle=90.0)
        self.assertAlmostEqual(aperture.GantryAngle, 90.0)
        aperture.GantryAngle = 45.0
        self.assertAlmostEqual(aperture.GantryAngle, 45.0)
