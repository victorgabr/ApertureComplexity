from unittest import TestCase

import numpy as np

from complexity.misc import LeafSequenceVariability
from tests.helpers import make_aperture, uniform_aperture


def stepped_aperture():
    # three leaf pairs, each 50 mm wide, shifted 10 mm per pair
    return make_aperture([0.0, 10.0, 20.0], [50.0, 60.0, 70.0], [10.0] * 3)


class TestLeafSequenceVariability(TestCase):
    def test_Calculate(self):
        # McNiven et al. 2010: per bank, (range + total variation) / (N * range)
        # for a monotonic 10 mm shift per pair: range = 20, TV = 20, N = 3,
        # so each factor is (20 + 20) / (3 * 20) = 2/3 and LSV = 4/9
        # total field size = 150 mm; AAV = 150 / 150 = 1
        value = LeafSequenceVariability().Calculate(stepped_aperture(), 150.0)
        self.assertAlmostEqual(value, 4.0 / 9.0)

    def test_Calculate_uniform_aperture_is_degenerate(self):
        # a perfectly uniform aperture has pos_max = (100, 0) on the right
        # axis, so the second LSV factor divides by zero
        aperture = uniform_aperture(10, 10.0, 0.0, 100.0)
        with np.errstate(invalid="ignore"):
            value = LeafSequenceVariability().Calculate(aperture, 1000.0)
        self.assertTrue(np.isnan(value))
