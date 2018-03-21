from unittest import TestCase

from complexity.ApertureMetric import Jaw, Rect

left, top, right, botton = -50, -50, 50, 50
jaw = Jaw(left, top, right, botton)


class TestJaw(TestCase):
    def test_Position(self):
        assert isinstance(jaw.Position, Rect)

    def test_Left(self):
        assert jaw.Left == -50

    def test_Top(self):
        assert jaw.Top == -50

    def test_Right(self):
        assert jaw.Right == 50

    def test_Bottom(self):
        assert jaw.Bottom == 50
