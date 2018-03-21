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

   Python port by. Victor Gabriel Leandro Alves
    victorgabr@gmail.com

"""


class Rect:
    def __init__(self, left, top, right, bottom):
        """
            Rectangular dimension (used for leaf and jaw positions)
            it is relative to the top of the first leaf and the isocenter
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
        return 'Position: left: %1.1f top: %1.1f right: %1.1f botton: %1.1f' \
               % (self.Left, self.Top, self.Right, self.Bottom)


class Jaw:
    def __init__(self, left, top, right, bottom):
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
             Left and right represent the bank A and B, respectively
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
            Each leaf pair contains a reference to the jaw
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
            The reason for <= or >= instead of just < or >
            is that if the jaw edge is equal to the leaf edge,
            it's as if the jaw edge was the leaf edge,
            so it's safer to count the leaf as outside,
            so that the edges are not counted twice (leaf and jaw edge)
        """
        return (self.Jaw.Top <= self.Bottom) or (self.Jaw.Bottom >= self.Top) \
               or (self.Jaw.Left >= self.Right) or (self.Jaw.Right <= self.Left)

    def IsOpen(self):
        return self.FieldSize() > 0.0

    def IsOpenButBehindJaw(self):
        """
        Used to warn the user that there is a leaf behind the jaws,
        even though it is open and within the top and bottom jaw edges
        """
        return (self.FieldSize() > 0.0) and (self.Jaw.Left > self.Left or self.Jaw.Right < self.Right)

    def OpenLeafWidth(self):
        """
        Returns the amount of leaf width that is open,
        considering the Position of the jaw
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

        leafPositions and leafWidths must not be null,
        and they must have the same number of leaves

        jaw is the Position of the jaw (cannot be null),
        given as:

        left, top, right, bottom; for a completely open jaw, use:

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

        :param positions:
        :param widths:
        :param jaw:
        :return:
        """
        leaf_tops = self.GetLeafTops(widths)

        pairs = []
        for i in range(len(widths)):
            lp = LeafPair(positions[0, i], positions[1, i], widths[i], leaf_tops[i], jaw)
            pairs.append(lp)
        return pairs

    @staticmethod
    def GetLeafTops(widths):
        """
        Using the leaf widths, creates an array of the location
        of all the leaf tops (relative to the isocenter)

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
            Creates Jaw object using x and y positions
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
        # Python does not support method overloading
        if len(self.LeafPairs) == 0:
            return 0.0

        # Top end of first leaf pair
        perimeter = self.LeafPairs[0].FieldSize()

        for i in range(len(self.LeafPairs)):
            perimeter += self.SidePerimeter(self.LeafPairs[i - 1], self.LeafPairs[i])

        # Bottom end of last leaf pair

        perimeter += self.LeafPairs[-1].FieldSize()

        return perimeter

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

        return abs(topEdgeLeft - bottomEdgeLeft) + \
               abs(topEdgeRight - bottomEdgeRight)

    def LeafPairsAreOutsideJaw(self, topLeafPair, bottomLeafPair):
        return topLeafPair.IsOutsideJaw() and bottomLeafPair.IsOutsideJaw()

    def JawTopIsBelowTopLeafPair(self, topLeafPair):
        return self.Jaw.Top <= topLeafPair.Bottom

    def JawBottomIsAboveBottomLeafPair(self, bottomLeafPair):
        return self.Jaw.Bottom >= bottomLeafPair.Top

    def LeafPairsAreDisjoint(self, topLeafPair, bottomLeafPair):

        return (bottomLeafPair.Left > topLeafPair.Right) or (bottomLeafPair.Right < topLeafPair.Left)


class EdgeMetricBase:
    def Calculate(self, aperture):
        return self.DivisionOrDefault(aperture.SidePerimeter(), aperture.Area())

    @staticmethod
    def DivisionOrDefault(a, b):
        return a / b if b != 0 else 0
