from unittest import TestCase

import numpy as np

from complexity.PyApertureMetric import (
    PyAperturesFromBeamCreator,
    PyMetersetsFromMetersetWeightsCreator,
)
from complexity.misc import ModulationIndexTotal
from tests.helpers import make_beam

# static beam: 3 control points, the MLC and the gantry do not move
OPENINGS = [(0.0, 100.0)] * 10
BEAM = make_beam([0.0, 50.0, 100.0], [OPENINGS, OPENINGS, OPENINGS])
APERTURES = PyAperturesFromBeamCreator().Create(BEAM)
CUMULATIVE_MU = PyMetersetsFromMetersetWeightsCreator().GetCumulativeMetersets(BEAM)


def make_instance():
    return ModulationIndexTotal(APERTURES, CUMULATIVE_MU)


class TestModulationIndexTotal(TestCase):
    def test_get_mu_data(self):
        # bypass __init__: get_mu_data does not use other instance state
        mi = ModulationIndexTotal.__new__(ModulationIndexTotal)
        data = mi.get_mu_data(np.array([0.0, 10.0, 20.0]))
        self.assertEqual(list(data.columns), ["MU", "delta_mu", "time"])
        self.assertEqual(len(data), 3)
        # 10 MU above the 4.238 MU threshold: time = 10 / 10 = 1.0 s
        self.assertAlmostEqual(data["time"][1], 1.0)
        self.assertAlmostEqual(data["time"][2], 1.0)

    def test_calculate_time(self):
        # below the threshold: the fixed 0.4238 s sampling interval
        self.assertAlmostEqual(
            ModulationIndexTotal.calculate_time(2.0), 2.0341 / 4.8
        )
        # above the threshold: 10 MU/s dose rate
        self.assertAlmostEqual(ModulationIndexTotal.calculate_time(10.0), 1.0)

    def test_delta_gantry(self):
        self.assertEqual(ModulationIndexTotal.delta_gantry((0, 90)), 90)
        self.assertEqual(ModulationIndexTotal.delta_gantry((0, 270)), 90)
        self.assertEqual(ModulationIndexTotal.delta_gantry((350, 10)), 20)
        self.assertEqual(ModulationIndexTotal.delta_gantry((90, 90)), 0)

    def test_rolling_apply(self):
        result = ModulationIndexTotal.rolling_apply(
            sum, np.array([1, 2, 3, 4]), w=2
        )
        self.assertTrue(np.isnan(result[0]))
        np.testing.assert_array_equal(result[1:], [3, 5, 7])

    def test_get_positions(self):
        mi = make_instance()
        positions = mi.get_positions(APERTURES)
        # 3 control points x 20 leaf positions
        self.assertEqual(positions.shape, (3, 20))

    def test_calc_mi_speed(self):
        mi = make_instance()
        value = mi.calc_mi_speed(mi.mlc_speed, mi.mlc_speed_std.values)
        # a static beam moves no leaves
        self.assertAlmostEqual(value, 0.0)

    def test_calc_mi_acceleration(self):
        mi = make_instance()
        alpha = 1.0 / mi.cumulative_mu["time"].mean()
        value = mi.calc_mi_acceleration(
            mi.mlc_speed,
            mi.mlc_speed_std.values,
            mi.mlc_acceleration,
            mi.mlc_acceleration_std.values,
            alpha=alpha,
        )
        self.assertAlmostEqual(value, 0.0)

    def test_calc_mi_total(self):
        mi = make_instance()
        alpha = 1.0 / mi.cumulative_mu["time"].mean()
        value = mi.calc_mi_total(
            mi.mlc_speed,
            mi.mlc_speed_std.values,
            mi.mlc_acceleration,
            mi.mlc_acceleration_std.values,
            alpha=alpha,
            WGA=np.ones(3),
            WMU=np.ones(3),
        )
        self.assertAlmostEqual(value, 0.0)

    def test_calculate_integrate(self):
        mi = make_instance()
        mi_speed, mi_acc, mi_total = mi.calculate_integrate()
        self.assertEqual((mi_speed, mi_acc, mi_total), (0.0, 0.0, 0.0))

    def test_calculate(self):
        mi = make_instance()
        z_speed, z_acc, mi_total = mi.calculate()
        self.assertEqual((z_speed, z_acc, mi_total), (0.0, 0.0, 0.0))
