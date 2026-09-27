from unittest import TestCase

from complexity.misc import ModulationComplexityScore
from tests.helpers import make_aperture


def stepped_aperture():
    # three leaf pairs, each 50 mm wide, shifted 10 mm per pair
    return make_aperture([0.0, 10.0, 20.0], [50.0, 60.0, 70.0], [10.0] * 3)


class TestModulationComplexityScore(TestCase):
    def test_CalculatePerAperture(self):
        apertures = [stepped_aperture(), stepped_aperture()]
        values = ModulationComplexityScore().CalculatePerAperture(apertures)
        # aav_norm = |50 - 0| + |70 - 10| = 50 + 50 = 100
        # per aperture: LSV = 4/9 (see LeafSequenceVariability), AAV = 150 / 100 = 1.5
        self.assertEqual(len(values), 2)
        for value in values:
            self.assertAlmostEqual(value, 4.0 / 9.0 * 1.5)

    def test_CalculatePerAperture_single_aperture(self):
        values = ModulationComplexityScore().CalculatePerAperture(
            [stepped_aperture()]
        )
        # aav_norm = 50; AAV = 150 / 50 = 3
        self.assertAlmostEqual(values[0], 4.0 / 9.0 * 3.0)
