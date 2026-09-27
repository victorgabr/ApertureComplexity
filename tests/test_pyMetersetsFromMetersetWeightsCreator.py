from types import SimpleNamespace
from unittest import TestCase

import numpy as np

from complexity.PyApertureMetric import PyMetersetsFromMetersetWeightsCreator


def make_control_point(weight):
    return SimpleNamespace(CumulativeMetersetWeight=weight)


def make_beam(meterset_unit, total_mu, cumulative_weights):
    return {
        "PrimaryDosimeterUnit": meterset_unit,
        "MU": total_mu,
        "ControlPointSequence": [make_control_point(w) for w in cumulative_weights],
    }


class TestPyMetersetsFromMetersetWeightsCreator(TestCase):
    def test_Create(self):
        # 100 MU beam, cumulative weights 0/50/100: the middle control point
        # carries the full MU step, the end points half of it
        beam = make_beam("MU", 100.0, [0.0, 50.0, 100.0])
        metersets = PyMetersetsFromMetersetWeightsCreator().Create(beam)
        np.testing.assert_array_almost_equal(metersets, [25.0, 50.0, 25.0])

    def test_Create_returns_none_for_non_mu_unit(self):
        beam = make_beam("cGy", 100.0, [1.0, 2.0])
        self.assertIsNone(PyMetersetsFromMetersetWeightsCreator().Create(beam))

    def test_GetCumulativeMetersets(self):
        beam = make_beam("MU", 100.0, [50.0, 100.0])
        cumulative = PyMetersetsFromMetersetWeightsCreator().GetCumulativeMetersets(beam)
        np.testing.assert_array_almost_equal(cumulative, [50.0, 100.0])

    def test_GetMetersetWeights(self):
        control_points = [make_control_point(w) for w in (0.0, 50.0, 100.0)]
        weights = PyMetersetsFromMetersetWeightsCreator.GetMetersetWeights(control_points)
        np.testing.assert_array_equal(weights, [0.0, 50.0, 100.0])

    def test_ConvertMetersetWeightsToMetersets(self):
        metersets = (
            PyMetersetsFromMetersetWeightsCreator.ConvertMetersetWeightsToMetersets(
                100.0, np.array([50.0, 100.0])
            )
        )
        np.testing.assert_array_equal(metersets, [50.0, 100.0])

    def test_UndoCummulativeSum(self):
        values = PyMetersetsFromMetersetWeightsCreator.UndoCummulativeSum(
            [0.0, 50.0, 100.0]
        )
        np.testing.assert_array_almost_equal(values, [25.0, 50.0, 25.0])
        self.assertAlmostEqual(sum(values), 100.0)
