"""
ApertureMetric.py

This module is a Python port of namespace Complexity.ApertureMetric of the Eclipse plug-in script used in the study:
[Predicting deliverability of volumetric-modulated arc therapy (VMAT) plans using aperture complexity analysis]
(http://www.jacmp.org/index.php/jacmp/article/view/6241).
Also, see the blog post [Calculating Aperture Complexity Metrics]
(http://www.carlosjanderson.com/calculating-aperture-complexity-metrics).

Notes
-----

.. Original Code:
   https://github.com/umro/Complexity

   Python port by Victor Gabriel Leandro Alves
    victorgabr@gmail.com

"""


class Rect:
    def __init__(self, left: float, top: float, right: float, bottom: float) -> None:
        """
        Rectangular dimension, used for leaf and jaw positions.
        The values are relative to the top of the first leaf and the
        isocenter.
        :param left:
        :param top:
        :param right:
        :param bottom:
        """
        self.Left = left
        self.Top = top
        self.Right = right
        self.Bottom = bottom

    def __repr__(self):
        return "Position: left: %1.1f top: %1.1f right: %1.1f botton: %1.1f" % (
            self.Left,
            self.Top,
            self.Right,
            self.Bottom,
        )


class Jaw:
    def __init__(self, left: float, top: float, right: float, bottom: float) -> None:
        self.jaw_position = Rect(left, top, right, bottom)

    @property
    def Position(self):
        return self.jaw_position

    @Position.setter
    def Position(self, value):
        self.jaw_position = value

    @property
    def Left(self):
        return self.jaw_position.Left

    @property
    def Top(self):
        return self.jaw_position.Top

    @property
    def Right(self):
        return self.jaw_position.Right

    @property
    def Bottom(self):
        return self.jaw_position.Bottom


class LeafPair:
    def __init__(self, left, right, width, top, jaw):
        """
        Left and right represent banks A and B, respectively.
        :param left: float
        :param right: float
        :param width: float
        :param top: float
        :param jaw: Jaw object
        """
        self.position = Rect(left, top, right, top - width)
        self.width = width
        self.jaw = jaw

    @property
    def Position(self):
        return self.position

    @Position.setter
    def Position(self, value):
        self.position = value

    @property
    def Left(self):
        return self.position.Left

    @property
    def Top(self):
        return self.position.Top

    @property
    def Right(self):
        return self.position.Right

    @property
    def Bottom(self):
        return self.position.Bottom

    @property
    def Width(self):
        return self.width

    @Width.setter
    def Width(self, value):
        self.width = value

    @property
    def Jaw(self):
        """
        Return the jaw referenced by this leaf pair.
        :return:
        """
        return self.jaw

    @Jaw.setter
    def Jaw(self, value):
        self.jaw = value

    def FieldSize(self):
        if self.IsOutsideJaw():
            return 0.0

        left = max(self.Jaw.Left, self.Left)
        right = min(self.Jaw.Right, self.Right)
        return right - left

    def FieldArea(self):
        return self.FieldSize() * self.OpenLeafWidth()

    def IsOutsideJaw(self):
        """
        This method uses <= and >=, not < and >. If a jaw edge equals a
        leaf edge, the method counts the leaf as outside. This avoids
        counting the shared edge twice, once for the leaf and once for
        the jaw.
        """
        return (
            (self.Jaw.Top <= self.Bottom)
            or (self.Jaw.Bottom >= self.Top)
            or (self.Jaw.Left >= self.Right)
            or (self.Jaw.Right <= self.Left)
        )

    def IsOpen(self):
        return self.FieldSize() > 0.0

    def IsOpenButBehindJaw(self):
        """
        Return True if the leaf pair is open but behind the jaws.
        This warns the user that a leaf is open and behind the jaws,
        even when it is inside the top and bottom jaw edges.
        """
        return (self.FieldSize() > 0.0) and (
            self.Jaw.Left > self.Left or self.Jaw.Right < self.Right
        )

    def OpenLeafWidth(self):
        """
        Return the leaf width that is open inside the jaws.
        """
        if self.IsOutsideJaw():
            return 0.0

        top = min(self.Jaw.Top, self.Top)
        bottom = max(self.Jaw.Bottom, self.Bottom)

        return top - bottom


class Aperture:
    """
        The first dimension of leafPositions corresponds to the bank,
        and the second dimension corresponds to the leaf pair.
        Leaf coordinates follow the IEC 61217 standard:

                          Negative Y         x = isocenter (0, 0)
                              -
                              |
                              |
                              |
        Negative X |----------x----------| Positive X
                              |
                              |
                              |
                              -
                          Positive Y

        leafPositions and leafWidths must not be null, and they must
        have the same number of leaves.

        jaw is the jaw position (cannot be null), given as:

        left, top, right, bottom. A completely open jaw uses:

            new double[] { double.MinValue, double.MinValue,
                           double.MaxValue, double.MaxValue };
    """

    # todo translate this doc to python
    def __init__(self, leaf_positions, leaf_widths, jaw):
        """
        :param leaf_positions: Numpy 2D array of floats
        :param leaf_widths: Numpy array 1D
        :param jaw: list with jaw positions
        """
        self.jaw = self.CreateJaw(jaw)
        self.leaf_pairs = self.CreateLeafPairs(leaf_positions, leaf_widths, self.Jaw)

    def CreateLeafPairs(self, positions, widths, jaw):
        """
        Return the leaf pairs for the given positions and widths.
        :param positions:
        :param widths:
        :param jaw:
        :return:
        """
        leaf_tops = self.GetLeafTops(widths)

        pairs = []
        for i in range(len(widths)):
            lp = LeafPair(
                positions[0, i], positions[1, i], widths[i], leaf_tops[i], jaw
            )
            pairs.append(lp)
        return pairs

    @staticmethod
    def GetLeafTops(widths):
        """
        Return an array with the top position of every leaf, relative
        to the isocenter. The method computes the positions from the
        leaf widths.

        :param widths:
        :return:
        """
        # Todo add unit test
        leaf_tops = [0.0] * len(widths)

        # Leaf index right below isocenter
        middle_index = int(len(widths) / 2)

        # Do bottom half
        for i in range(middle_index + 1, len(widths)):
            leaf_tops[i] = leaf_tops[i - 1] - widths[i - 1]

        # Do top half
        i = middle_index - 1
        while i >= 0:
            leaf_tops[i] = leaf_tops[i + 1] + widths[i]
            i -= 1

        return leaf_tops

    @staticmethod
    def CreateJaw(pos):
        """
        Create a Jaw object from x and y positions.
        :param pos: [] position
        :return: Jaw
        """
        return Jaw(pos[0], pos[1], pos[2], pos[3])

    @property
    def Jaw(self):
        return self.jaw

    @Jaw.setter
    def Jaw(self, value):
        self.jaw = value

    @property
    def LeafPairs(self):
        return self.leaf_pairs

    @LeafPairs.setter
    def LeafPairs(self, value):
        self.leaf_pairs = value

    def HasOpenLeafBehindJaws(self):
        truth = [lp.IsOpenButBehindJaw() for lp in self.LeafPairs]
        return any(truth)

    def Area(self):
        return sum([lp.FieldArea() for lp in self.LeafPairs])

    def side_perimeter(self):
        """
        Return the length of the aperture edges perpendicular to the
        leaf travel direction. These are the leaf-end edges between
        adjacent leaf pairs, plus the top and bottom ends of the open
        region.
        The edge metric of Younge et al., Int J Radiat Oncol Biol Phys
        2012;82:1210-7, uses this perimeter.
        This is not the closed-contour perimeter that the aperture
        irregularity metric of Du et al. needs (see perimeter()).
        """
        # Python does not support method overloading
        if len(self.LeafPairs) == 0:
            return 0.0

        # Top end of first leaf pair
        perimeter = self.LeafPairs[0].FieldSize()

        # Edges between adjacent leaf pairs only: the first leaf pair has no
        # neighbour above it, so the loop starts at index 1
        for i in range(1, len(self.LeafPairs)):
            perimeter += self.SidePerimeter(self.LeafPairs[i - 1], self.LeafPairs[i])

        # Bottom end of last leaf pair

        perimeter += self.LeafPairs[-1].FieldSize()

        return perimeter

    def leaf_side_perimeter(self):
        """
        Return the length of the aperture edges parallel to the leaf
        travel direction. Each open leaf pair contributes its two
        lateral sides. Each side is as long as the leaf width that is
        open inside the jaws.
        """
        return 2.0 * sum(
            lp.OpenLeafWidth() for lp in self.LeafPairs if lp.IsOpen()
        )

    def perimeter(self):
        """
        Return the length of the whole closed contour of the aperture:
        the leaf-end edges (side_perimeter) plus the leaf-side edges
        (leaf_side_perimeter).
        The aperture irregularity metric of Du et al., Med Phys
        2014;41:021716, needs this perimeter. That metric computes
        AI = P^2 / (4*pi*A), which equals 1 for a circle and
        4/pi = 1.273 for a square.
        """
        return self.side_perimeter() + self.leaf_side_perimeter()

    def SidePerimeter(self, topLeafPair, bottomLeafPair):

        if self.LeafPairsAreOutsideJaw(topLeafPair, bottomLeafPair):
            #     _____         ________
            #          |       |
            #     _____|___    |________
            #      +-------|------|---+
            #     _|_______|      |___|_

            return 0.0

        if self.JawTopIsBelowTopLeafPair(topLeafPair):
            #
            #     _|___         ______|_
            #      +---|-------|------+
            #     _____|___    |________
            #              |      |
            #     _________|      |_____

            return bottomLeafPair.FieldSize()

        if self.JawBottomIsAboveBottomLeafPair(bottomLeafPair):
            # At this point, the edge between the top and bottom leaf pairs
            # should be fully or partially exposed (depending on the jaw)
            # ___    _______________
            #  +-|--|-------+
            # _|_|__|_______|_______
            #  +-------|----+ |
            # _________|      |_____
            return topLeafPair.FieldSize()

        if self.LeafPairsAreDisjoint(topLeafPair, bottomLeafPair):
            #  ___         __________
            #  +-|-------|--+
            # _|_|___    |__|_______
            #  +-----|------+ |
            # _______|        |_____

            return topLeafPair.FieldSize() + bottomLeafPair.FieldSize()

        topEdgeLeft = max(self.Jaw.Left, topLeafPair.Left)
        bottomEdgeLeft = max(self.Jaw.Left, bottomLeafPair.Left)
        topEdgeRight = min(self.Jaw.Right, topLeafPair.Right)
        bottomEdgeRight = min(self.Jaw.Right, bottomLeafPair.Right)

        return abs(topEdgeLeft - bottomEdgeLeft) + abs(topEdgeRight - bottomEdgeRight)

    def LeafPairsAreOutsideJaw(self, topLeafPair, bottomLeafPair):
        return topLeafPair.IsOutsideJaw() and bottomLeafPair.IsOutsideJaw()

    def JawTopIsBelowTopLeafPair(self, topLeafPair):
        return self.Jaw.Top <= topLeafPair.Bottom

    def JawBottomIsAboveBottomLeafPair(self, bottomLeafPair):
        return self.Jaw.Bottom >= bottomLeafPair.Top

    def LeafPairsAreDisjoint(self, topLeafPair, bottomLeafPair):

        return (bottomLeafPair.Left > topLeafPair.Right) or (
            bottomLeafPair.Right < topLeafPair.Left
        )


class EdgeMetricBase:
    def Calculate(self, aperture):
        return self.DivisionOrDefault(aperture.SidePerimeter(), aperture.Area())

    @staticmethod
    def DivisionOrDefault(a, b):
        return a / b if b != 0 else 0
