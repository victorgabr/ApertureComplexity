from unittest import TestCase

from complexity.ApertureMetric import LeafPair, Jaw, Rect

left, top, right, botton = -50, -50, 50, 50
jaw = Jaw(left, top, right, botton)
lp = LeafPair(-25, 25, 5, -5, jaw)


class TestLeafPair(TestCase):
    def test_Position(self):
        assert isinstance(lp.Position, Rect)

    def test_Left(self):
        self.assertAlmostEqual(lp.Left, -25)

    def test_Top(self):
        self.assertAlmostEqual(lp.Top, 5)

    def test_Right(self):
        self.assertAlmostEqual(lp.Right, 25)

    def test_Bottom(self):
        self.assertAlmostEqual(lp.Bottom, 0)

    def test_Width(self):
        self.assertAlmostEqual(lp.Width, 0)

    def test_Jaw(self):
        assert lp.jaw.Left == -50

        assert lp.jaw.Top == -50

        assert lp.jaw.Right == 50

        assert lp.jaw.Bottom == 50

    def test_FieldSize(self):
        target = 50 * 5
        self.assertAlmostEqual(lp.FieldSize(), target)

    def test_FieldArea(self):
        self.fail()

    def test_IsOutsideJaw(self):
        self.fail()

    def test_IsOpen(self):
        self.fail()

    def test_IsOpenButBehindJaw(self):
        self.fail()

    def test_OpenLeafWidth(self):
        self.fail()
