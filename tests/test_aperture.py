from unittest import TestCase

import numpy as np

from complexity.ApertureMetric import Aperture, Jaw, LeafPair
from tests.helpers import OPEN_JAW, make_aperture


def leaf_pair(left, right, width, top, jaw):
    return LeafPair(left, right, width, top, jaw)


class TestAperture(TestCase):
    def test_CreateLeafPairs(self):
        aperture = make_aperture([0.0, 0.0, 0.0], [50.0, 50.0, 50.0], [10.0] * 3)
        self.assertEqual(len(aperture.LeafPairs), 3)
        for leaf_pair in aperture.LeafPairs:
            self.assertIsInstance(leaf_pair, LeafPair)
        # the middle leaf is centred on the isocentre
        self.assertAlmostEqual(aperture.LeafPairs[0].Top, 10.0)
        self.assertAlmostEqual(aperture.LeafPairs[1].Top, 0.0)
        self.assertAlmostEqual(aperture.LeafPairs[2].Top, -10.0)

    def test_GetLeafTops(self):
        tops = Aperture.GetLeafTops([10.0, 20.0, 30.0, 40.0])
        self.assertEqual(tops, [30.0, 20.0, 0.0, -30.0])

    def test_CreateJaw(self):
        jaw = Aperture.CreateJaw([1.0, 2.0, 3.0, 4.0])
        self.assertIsInstance(jaw, Jaw)
        self.assertEqual((jaw.Left, jaw.Top, jaw.Right, jaw.Bottom), (1.0, 2.0, 3.0, 4.0))

    def test_Jaw(self):
        aperture = make_aperture([0.0], [50.0], [10.0])
        self.assertIsInstance(aperture.Jaw, Jaw)
        self.assertEqual(
            (aperture.Jaw.Left, aperture.Jaw.Top, aperture.Jaw.Right, aperture.Jaw.Bottom),
            tuple(OPEN_JAW),
        )

    def test_LeafPairs(self):
        aperture = make_aperture([0.0, 0.0], [50.0, 50.0], [10.0, 10.0])
        self.assertEqual(len(aperture.LeafPairs), 2)
        self.assertAlmostEqual(aperture.LeafPairs[0].Left, 0.0)
        self.assertAlmostEqual(aperture.LeafPairs[0].Right, 50.0)

    def test_HasOpenLeafBehindJaws(self):
        # leaf opens beyond the jaw in x
        aperture = make_aperture(
            [-50.0], [50.0], [10.0], jaw=[-40.0, 200.0, 40.0, -200.0]
        )
        self.assertTrue(aperture.HasOpenLeafBehindJaws())
        # fully open jaw: nothing is behind it
        aperture = make_aperture([0.0], [50.0], [10.0])
        self.assertFalse(aperture.HasOpenLeafBehindJaws())

    def test_Area(self):
        aperture = make_aperture([0.0, 0.0, 0.0], [50.0, 50.0, 50.0], [10.0] * 3)
        self.assertAlmostEqual(aperture.Area(), 1500.0)

    def test_side_perimeter(self):
        # 100 mm wide square field: top end + bottom end, no steps
        aperture = make_aperture(
            [0.0] * 10, [100.0] * 10, [10.0] * 10
        )
        self.assertAlmostEqual(aperture.side_perimeter(), 200.0)

    def test_SidePerimeter(self):
        aperture = make_aperture([0.0], [50.0], [10.0])
        jaw = aperture.Jaw
        # overlapping openings: one step per bank
        top = leaf_pair(0.0, 50.0, 10.0, 0.0, jaw)
        bottom = leaf_pair(10.0, 60.0, 10.0, -10.0, jaw)
        self.assertAlmostEqual(aperture.SidePerimeter(top, bottom), 20.0)
        # disjoint openings: both leaf ends are exposed
        top = leaf_pair(0.0, 50.0, 10.0, 0.0, jaw)
        bottom = leaf_pair(60.0, 100.0, 10.0, -10.0, jaw)
        self.assertAlmostEqual(aperture.SidePerimeter(top, bottom), 90.0)
        # both leaf pairs outside the jaw: no edge
        top = leaf_pair(0.0, 50.0, 10.0, 300.0, jaw)
        bottom = leaf_pair(0.0, 50.0, 10.0, 310.0, jaw)
        self.assertAlmostEqual(aperture.SidePerimeter(top, bottom), 0.0)

    def test_LeafPairsAreOutsideJaw(self):
        aperture = make_aperture([0.0], [50.0], [10.0])
        jaw = aperture.Jaw
        inside = leaf_pair(0.0, 50.0, 10.0, 0.0, jaw)
        outside = leaf_pair(0.0, 50.0, 10.0, 300.0, jaw)
        self.assertTrue(aperture.LeafPairsAreOutsideJaw(outside, outside))
        self.assertFalse(aperture.LeafPairsAreOutsideJaw(inside, inside))
        self.assertFalse(aperture.LeafPairsAreOutsideJaw(inside, outside))

    def test_JawTopIsBelowTopLeafPair(self):
        aperture = make_aperture([0.0], [50.0], [10.0])
        jaw = aperture.Jaw
        above = leaf_pair(0.0, 50.0, 10.0, 300.0, jaw)
        inside = leaf_pair(0.0, 50.0, 10.0, 0.0, jaw)
        self.assertTrue(aperture.JawTopIsBelowTopLeafPair(above))
        self.assertFalse(aperture.JawTopIsBelowTopLeafPair(inside))

    def test_JawBottomIsAboveBottomLeafPair(self):
        aperture = make_aperture([0.0], [50.0], [10.0])
        jaw = aperture.Jaw
        below = leaf_pair(0.0, 50.0, 10.0, -300.0, jaw)
        inside = leaf_pair(0.0, 50.0, 10.0, 0.0, jaw)
        self.assertTrue(aperture.JawBottomIsAboveBottomLeafPair(below))
        self.assertFalse(aperture.JawBottomIsAboveBottomLeafPair(inside))

    def test_LeafPairsAreDisjoint(self):
        aperture = make_aperture([0.0], [50.0], [10.0])
        jaw = aperture.Jaw
        top = leaf_pair(0.0, 50.0, 10.0, 0.0, jaw)
        disjoint = leaf_pair(60.0, 100.0, 10.0, -10.0, jaw)
        overlapping = leaf_pair(40.0, 90.0, 10.0, -10.0, jaw)
        self.assertTrue(aperture.LeafPairsAreDisjoint(top, disjoint))
        self.assertFalse(aperture.LeafPairsAreDisjoint(top, overlapping))
