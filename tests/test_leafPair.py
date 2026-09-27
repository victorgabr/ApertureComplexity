from unittest import TestCase

from complexity.ApertureMetric import LeafPair, Jaw, Rect

# left, top, right, bottom (top > bottom convention of the Aperture class)
jaw = Jaw(-50, 50, 50, -50)
lp = LeafPair(-25, 25, 5, -5, jaw)
# leaf top (60) above the jaw top (50)
lp_outside = LeafPair(-25, 25, 5, 60, jaw)
# closed leaf pair
lp_closed = LeafPair(0, 0, 5, -5, jaw)
# open leaf pair that extends beyond the jaw in x
lp_behind = LeafPair(-60, 60, 5, -5, jaw)


class TestLeafPair(TestCase):
    def test_Position(self):
        self.assertIsInstance(lp.Position, Rect)

    def test_Left(self):
        self.assertAlmostEqual(lp.Left, -25)

    def test_Top(self):
        self.assertAlmostEqual(lp.Top, -5)

    def test_Right(self):
        self.assertAlmostEqual(lp.Right, 25)

    def test_Bottom(self):
        self.assertAlmostEqual(lp.Bottom, -10)

    def test_Width(self):
        self.assertAlmostEqual(lp.Width, 5)

    def test_Jaw(self):
        self.assertEqual(lp.jaw.Left, -50)
        self.assertEqual(lp.jaw.Top, 50)
        self.assertEqual(lp.jaw.Right, 50)
        self.assertEqual(lp.jaw.Bottom, -50)

    def test_FieldSize(self):
        self.assertAlmostEqual(lp.FieldSize(), 50.0)

    def test_FieldArea(self):
        self.assertAlmostEqual(lp.FieldArea(), 250.0)

    def test_IsOutsideJaw(self):
        self.assertFalse(lp.IsOutsideJaw())
        self.assertTrue(lp_outside.IsOutsideJaw())

    def test_IsOpen(self):
        self.assertTrue(lp.IsOpen())
        self.assertFalse(lp_closed.IsOpen())

    def test_IsOpenButBehindJaw(self):
        self.assertFalse(lp.IsOpenButBehindJaw())
        self.assertTrue(lp_behind.IsOpenButBehindJaw())

    def test_OpenLeafWidth(self):
        self.assertAlmostEqual(lp.OpenLeafWidth(), 5.0)
        self.assertAlmostEqual(lp_outside.OpenLeafWidth(), 0.0)
