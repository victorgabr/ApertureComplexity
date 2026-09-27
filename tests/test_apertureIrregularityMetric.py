"""
Tests for the aperture perimeter definitions and for the aperture irregularity
metric of Du W, Cho SH, Zhang X, Hoffman KE, Kudchadker RJ. Quantification of
beam complexity in intensity-modulated radiation therapy treatment plans.
Med Phys 2014;41:021716. http://dx.doi.org/10.1118/1.4861821.

The paper defines AI = AP^2 / (4 * pi * AA), where AP is the perimeter of the
whole aperture contour (all edges: leaf-end edges and leaf-side edges) and AA
is the aperture area. AI is 1 for a circle, 4/pi = 1.273 for a square, and
greater than 1 for any other shape (isoperimetric inequality).
"""

from unittest import TestCase

import numpy as np

from complexity.PyApertureMetric import PyAperture
from complexity.PyComplexityMetric import ApertureIrregularity, PyEdgeMetricBase

# left, top, right, bottom; fully open jaw (ESAPI convention: top > bottom)
OPEN_JAW = [-400.0, 200.0, 400.0, -200.0]


def aperture_from_positions(lefts, rights, widths, jaw=OPEN_JAW):
    """
        Build an aperture from one position per bank.
        Leaf pairs are ordered from top to bottom.
    :param lefts: bank A (left) leaf positions, top to bottom
    :param rights: bank B (right) leaf positions, top to bottom
    :param widths: leaf pair widths, top to bottom
    :param jaw: jaw position [left, top, right, bottom]
    """
    positions = np.array([list(lefts), list(rights)], dtype=float)
    return PyAperture(positions, np.array(widths, dtype=float), list(jaw), 0.0)


def uniform_aperture(n_leaves, leaf_width, left, right, jaw=OPEN_JAW):
    """Aperture of n identical leaf pairs, all opened from left to right."""
    return aperture_from_positions(
        [left] * n_leaves, [right] * n_leaves, [leaf_width] * n_leaves, jaw
    )


def square_aperture():
    """100 mm x 100 mm open field: 10 leaf pairs of 10 mm, opened over 100 mm."""
    return uniform_aperture(10, 10.0, 0.0, 100.0)


def narrow_aperture():
    """100 mm tall, 20 mm wide aperture (sliding-window like segment)."""
    return uniform_aperture(10, 10.0, 0.0, 20.0)


def two_islands_aperture():
    """
        Two separated openings: the top leaf pair opened over [0, 50] mm and
        the bottom leaf pair opened over [100, 200] mm, 8 closed pairs between.
        The top and bottom leaf pairs do not overlap in the leaf travel
        direction, so they expose each other's ends if the perimeter routine
        wraps around from the last leaf pair to the first one.
    """
    lefts = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0]
    rights = [50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 200.0]
    return aperture_from_positions(lefts, rights, [10.0] * 10)


def disc_aperture(n_leaves=100, leaf_width=1.0, radius=50.0):
    """
        Staircase approximation of a disc of 50 mm radius, sampled with
        n_leaves leaf pairs of leaf_width mm.
    """
    lefts, rights = [], []
    for i in range(n_leaves):
        # leaf pair centre height relative to the isocentre
        y_center = radius - (i + 0.5) * leaf_width
        half_chord = np.sqrt(max(radius**2 - y_center**2, 0.0))
        lefts.append(-half_chord)
        rights.append(half_chord)
    return aperture_from_positions(lefts, rights, [leaf_width] * n_leaves)


def random_aperture(rng, n_leaves=40, leaf_width=5.0):
    """Random aperture made of open and closed leaf pairs."""
    lefts, rights = [], []
    left = 0.0
    for _ in range(n_leaves):
        left += rng.uniform(-8.0, 8.0)
        left = float(np.clip(left, -150.0, 150.0))
        opening = rng.choice([0.0, rng.uniform(4.0, 60.0)])
        lefts.append(left)
        rights.append(left + opening)
    return aperture_from_positions(lefts, rights, [leaf_width] * n_leaves)


class TestAperturePerimeter(TestCase):
    def test_side_perimeter_counts_leaf_end_edges_only(self):
        # 100 mm wide square field: top end + bottom end, no steps between
        # adjacent leaf pairs.
        self.assertAlmostEqual(square_aperture().side_perimeter(), 200.0)

    def test_leaf_side_perimeter_counts_two_sides_of_each_open_leaf(self):
        # 10 open leaf pairs of 10 mm: 2 sides x 10 mm x 10 leaves
        self.assertAlmostEqual(square_aperture().leaf_side_perimeter(), 200.0)

    def test_perimeter_is_the_closed_contour(self):
        # square: 4 x 100 mm
        self.assertAlmostEqual(square_aperture().perimeter(), 400.0)

    def test_perimeter_of_narrow_aperture(self):
        # rectangle 100 mm x 20 mm
        self.assertAlmostEqual(narrow_aperture().perimeter(), 240.0)

    def test_perimeter_of_disjoint_openings(self):
        # 50 x 10 mm rectangle (perimeter 120) + 100 x 10 mm rectangle
        # (perimeter 220)
        ap = two_islands_aperture()
        self.assertAlmostEqual(ap.side_perimeter(), 300.0)
        self.assertAlmostEqual(ap.leaf_side_perimeter(), 40.0)
        self.assertAlmostEqual(ap.perimeter(), 340.0)

    def test_perimeter_of_jaw_clipped_aperture(self):
        # jaw top at 0 mm keeps the 5 lower leaf pairs: 100 x 50 mm rectangle
        jaw_clipped = uniform_aperture(10, 10.0, 0.0, 100.0, jaw=[-400.0, 0.0, 400.0, -200.0])
        self.assertAlmostEqual(jaw_clipped.Area(), 5000.0)
        self.assertAlmostEqual(jaw_clipped.perimeter(), 300.0)

    def test_perimeter_of_closed_aperture(self):
        closed = uniform_aperture(10, 10.0, 0.0, 0.0)
        self.assertAlmostEqual(closed.Area(), 0.0)
        self.assertAlmostEqual(closed.perimeter(), 0.0)

    def test_perimeter_of_stepped_aperture_matches_contour(self):
        """
            Each step between adjacent leaf pairs adds one leaf-end edge and
            one leaf-side edge of the same length, so the total contour of the
            staircase equals 2 * (total opening span + total open height).
        """
        n = 6
        w = 10.0
        lefts = [10.0 * i for i in range(n)]
        rights = [left + 20.0 for left in lefts]
        ap = aperture_from_positions(lefts, rights, [w] * n)
        # 60 mm tall; ends are 20 mm wide and the 5 steps are 10 mm wide per side
        self.assertAlmostEqual(ap.side_perimeter(), 2 * 20.0 + 2 * 50.0)
        self.assertAlmostEqual(ap.leaf_side_perimeter(), 2 * n * w)
        self.assertAlmostEqual(ap.perimeter(), 2 * (70.0 + 60.0))

    def test_isoperimetric_inequality_for_random_apertures(self):
        rng = np.random.default_rng(20140216)
        metric = ApertureIrregularity()
        for _ in range(200):
            ap = random_aperture(rng)
            area, perimeter = ap.Area(), ap.perimeter()
            if area == 0.0:
                continue
            self.assertGreaterEqual(perimeter**2, 4 * np.pi * area)
            self.assertGreaterEqual(metric.Calculate(ap), 1.0)


class TestApertureIrregularityMetric(TestCase):
    def test_Calculate_round_aperture_is_near_the_isoperimetric_floor(self):
        """
            An MLC aperture is a staircase, never a true circle, so the
            isoperimetric lower bound of 1 is not attainable. For a staircase
            disc the contour tends to 8 R (4 R horizontal + 4 R vertical) and
            the area to pi R^2, so AI tends to 16 / pi^2 = 1.62: the lowest
            value any MLC aperture shape gets close to.
        """
        ai = ApertureIrregularity().Calculate(disc_aperture())
        self.assertGreaterEqual(ai, 1.0)
        self.assertAlmostEqual(ai, 16.0 / np.pi**2, places=2)

    def test_Calculate_square_is_four_over_pi(self):
        ai = ApertureIrregularity().Calculate(square_aperture())
        self.assertAlmostEqual(ai, 4.0 / np.pi, places=6)

    def test_Calculate_narrow_aperture_is_more_irregular(self):
        metric = ApertureIrregularity()
        ai_narrow = metric.Calculate(narrow_aperture())
        ai_square = metric.Calculate(square_aperture())
        ai_round = metric.Calculate(disc_aperture())
        # rectangle 100 x 20 mm
        self.assertAlmostEqual(ai_narrow, 240.0**2 / (4 * np.pi * 2000.0), places=6)
        self.assertGreater(ai_narrow, ai_square)
        # Du et al.: a narrow aperture is more irregular than a rounded one
        self.assertGreater(ai_narrow, ai_round)

    def test_Calculate_closed_aperture_is_zero(self):
        self.assertEqual(
            ApertureIrregularity().Calculate(uniform_aperture(10, 10.0, 0.0, 0.0)), 0
        )

    def test_CalculatePerAperture(self):
        from complexity.PyComplexityMetric import ApertureIrregularityMetric

        apertures = [square_aperture(), narrow_aperture(), disc_aperture()]
        values = ApertureIrregularityMetric().CalculatePerAperture(apertures)
        self.assertEqual(len(values), len(apertures))
        for value in values:
            self.assertGreaterEqual(value, 1.0)

    def test_EdgeMetricIsUnchanged(self):
        """
            The edge metric of Younge et al. keeps using the leaf-end
            (side) perimeter only: 200 mm / 10000 mm^2.
        """
        metric = PyEdgeMetricBase()
        self.assertAlmostEqual(metric.Calculate(square_aperture()), 0.02)
        # narrow field: leaf-end edges are the 20 mm top and bottom ends only
        self.assertAlmostEqual(metric.Calculate(narrow_aperture()), 0.02)
