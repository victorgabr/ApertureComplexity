from unittest import TestCase

import numpy as np

from complexity.misc import ModulationIndexScore
from tests.helpers import make_beam, make_plan

# static beam: 3 control points, the MLC and the gantry do not move
OPENINGS = [(0.0, 100.0)] * 10
BEAM = make_beam([0.0, 50.0, 100.0], [OPENINGS, OPENINGS, OPENINGS])
PLAN = make_plan({1: BEAM})


class TestModulationIndexScore(TestCase):
    def test_CalculateForBeam(self):
        result = ModulationIndexScore().CalculateForBeam(None, PLAN, BEAM)
        self.assertEqual(len(result), 3)
        for value in result:
            self.assertTrue(np.isfinite(value))
        # a static beam has no modulation
        for value in result:
            self.assertAlmostEqual(value, 0.0)

    def test_CalculateForPlan(self):
        result = ModulationIndexScore().CalculateForPlan(None, PLAN)
        self.assertEqual(len(result), 3)
        for value in result:
            self.assertTrue(np.isfinite(value))
            self.assertAlmostEqual(value, 0.0)
