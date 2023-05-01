# Typing imports
from typing import List, Dict
from pydicom.dataset import Dataset

import numpy as np

from complexity.ApertureMetric import Aperture, LeafPair, Jaw


class PyLeafPair(LeafPair):
    def __init__(
        self, left: float, right: float, width: float, top: float, jaw: Jaw
    ) -> None:
        super().__init__(left, right, width, top, jaw)

    def __repr__(self):
        txt = "Leaf Pair: left: %1.1f top: %1.1f right: %1.1f botton: %1.1f" % (
            self.Left,
            self.Top,
            self.Right,
            self.Bottom,
        )

        return txt


class PyAperture(Aperture):
    def __init__(
        self,
        leaf_positions: np.ndarray,
        leaf_widths: np.ndarray,
        jaw: List[float],
        gantry_angle: float,
    ) -> None:
        super().__init__(leaf_positions, leaf_widths, jaw)
        self.gantry_angle = gantry_angle

    def CreateLeafPairs(
        self, positions: np.ndarray, widths: np.ndarray, jaw: Jaw
    ) -> List[PyLeafPair]:
        leaf_tops = self.GetLeafTops(widths)

        pairs = []
        for i in range(len(widths)):
            lp = PyLeafPair(
                positions[0, i], positions[1, i], widths[i], leaf_tops[i], jaw
            )
            pairs.append(lp)
        return pairs

    @property
    def LeafPairArea(self) -> List[float]:
        return [lp.FieldArea() for lp in self.LeafPairs]

    @property
    def GantryAngle(self) -> float:
        return self.gantry_angle

    @GantryAngle.setter
    def GantryAngle(self, value: float):
        self.gantry_angle = value

    def __repr__(self):
        txt = "Aperture - Gantry: %1.1f" % self.GantryAngle
        return txt


class PyAperturesFromBeamCreator:
    def Create(self, beam: Dict[str, str]) -> List[PyAperture]:

        apertures = []

        leafWidths = self.GetLeafWidths(beam)
        cp_jaw = self.CreateJaw(beam)
        for controlPoint in beam["ControlPointSequence"]:
            gantry_angle = (
                float(controlPoint.GantryAngle)
                if "GantryAngle" in controlPoint
                else beam["GantryAngle"]
            )
            leafPositions = self.GetLeafPositions(controlPoint)
            new_jaw_position = self.get_jaw_position_per_control_point(controlPoint, leafWidths)
            if new_jaw_position:
                cp_jaw = new_jaw_position
            if leafPositions is not None:
                apertures.append(
                    PyAperture(leafPositions, leafWidths, cp_jaw, gantry_angle)
                )

        return apertures

    @staticmethod
    def CreateJaw(beam: dict) -> List[float]:
        """
            but the Aperture class expects cartesian y-axis
        :param beam:
        :return:
        """

        # if there is no X jaws, consider open 400 mm
        left = float(beam["ASYMX"][0]) if "ASYMX" in beam else -200.0
        right = float(beam["ASYMX"][1]) if "ASYMX" in beam else 200.0
        top = float(beam["ASYMY"][0]) if "ASYMY" in beam else -200.0
        bottom = float(beam["ASYMY"][1]) if "ASYMY" in beam else 200.0

        # invert y axis to match apperture class -top, -botton that uses Varian standard ESAPI
        return [left, -top, right, -bottom]

    def GetLeafWidths(self, beam_dict: Dict) -> np.ndarray:
        """
            Get MLCX leaf width from  BeamLimitingDeviceSequence
            (300a, 00be) Leaf Position Boundaries Tag

            #TODO HALCYON leaf widths
        :param beam_dict: Dicomparser Beam dict from plan_dict
        :return: MLCX leaf width
        """

        bs = beam_dict["BeamLimitingDeviceSequence"]
        # the script only takes MLCX as parameter
        for b in bs:
            if b.RTBeamLimitingDeviceType in ["MLCX", "MLCX1", "MLCX2"]:
                return np.diff(b.LeafPositionBoundaries)

    def GetLeafTops(self, beam_dict: Dict) -> np.ndarray:
        """
            Get MLCX leaf Tops from  BeamLimitingDeviceSequence
            (300a, 00be) Leaf Position Boundaries Tag
        :param beam_dict: Dicomparser Beam dict from plan_dict
        :return: MLCX leaf width
        """
        bs = beam_dict["BeamLimitingDeviceSequence"]
        for b in bs:
            if b.RTBeamLimitingDeviceType == "MLCX":
                return np.array(b.LeafPositionBoundaries[:-1], dtype=float)

    def GetLeafPositions(self, control_point: Dataset) -> np.ndarray:
        """
            Leaf positions are given from bottom to top by ESAPI,
            but the Aperture class expects them from top to bottom
            Leaf Positions are mechanical boundaries projected onto Isocenter plane
            # TODO add halcyon MLC positions
        :param control_point:
        """
        if "BeamLimitingDevicePositionSequence" in control_point:
            pos = control_point.BeamLimitingDevicePositionSequence[-1]
            mlc_open = pos.LeafJawPositions
            n_pairs = int(len(mlc_open) / 2)
            bank_a_pos = mlc_open[:n_pairs]
            bank_b_pos = mlc_open[n_pairs:]

            return np.vstack((bank_a_pos, bank_b_pos))

    def return_jaw_position_from_mlc(self, positions, leafwidths: np.ndarray):
        """
        Finding left/right isn't hard, just take min and max when they aren't equal
        Finding top/bottom is difficult. We need to find the first and last leaf pairs that are touching
        Then use the leaf thicknesses to identify that physical location as a distance from the center
        """
        left_leaves = np.asarray(positions[:len(positions) // 2])
        right_leaves = np.asarray(positions[len(positions) // 2:])
        left = np.min(left_leaves[left_leaves != right_leaves])
        right = np.max(right_leaves[left_leaves != right_leaves])
        center = len(positions)//4
        top_bottom = np.where(left_leaves != right_leaves)
        diff_bottom = center - top_bottom[0][0]
        if diff_bottom > 0:
            bottom = np.sum(leafwidths[center-diff_bottom:center])
        else:
            bottom = -np.sum(leafwidths[center:center-diff_bottom])
        diff_top = center - top_bottom[0][-1]
        if diff_top > 0:
            top = np.sum(leafwidths[center-diff_top:center])
        else:
            top = -np.sum(leafwidths[center:center-diff_top])
        return [left, top, right, bottom]

    def get_jaw_position_per_control_point(self, control_point: Dataset, leafwidths: np.ndarray) -> List[float]:
        """
            Get jaw positions from control point
        :param
        """
        if "BeamLimitingDevicePositionSequence" in control_point:
            sequence = control_point.BeamLimitingDevicePositionSequence
            # check if there's a jaw position per control point
            mlc_jaws = [s.LeafJawPositions for s in sequence if s.RTBeamLimitingDeviceType.find("MLCX") == 0]
            x_jaws = [s.LeafJawPositions for s in sequence if s.RTBeamLimitingDeviceType == "X"]
            y_jaws = [s.LeafJawPositions for s in sequence if s.RTBeamLimitingDeviceType == "Y"]
            x_jaws_asym = [s.LeafJawPositions for s in sequence if s.RTBeamLimitingDeviceType == "ASYMX"]
            y_jaws_asym = [s.LeafJawPositions for s in sequence if s.RTBeamLimitingDeviceType == "ASYMY"]
            """
            Checking first to see if we have jaw positions, which will be 2 points
            """
            if ((x_jaws and y_jaws) or (x_jaws_asym and y_jaws_asym)) and len(leafwidths) != 28:
                if x_jaws:
                    left, right = x_jaws[0]
                    top, bottom = y_jaws[0]
                    return [float(left), float(-top), float(right), float(-bottom)]
                if x_jaws_asym:
                    left, right = x_jaws_asym[0]
                    top, bottom = y_jaws_asym[0]
                    return [float(left), float(-top), float(right), float(-bottom)]
            elif mlc_jaws and len(leafwidths) == 28:  # Make sure it is a Halcyon MLC
                """
                If we have halcyon style, which has 2N values, 101, 102, ..., 201, 202, ...
                https://dicom.innolitics.com/ciods/rt-image/rt-image/30020030/300a00b6/300a011c
                """
                for mlc_jaw in mlc_jaws:
                    left, top, right, bottom = self.return_jaw_position_from_mlc(mlc_jaw, leafwidths)
                    return [float(left), float(-top), float(right), float(-bottom)]
            return []

class PyMetersetsFromMetersetWeightsCreator:
    def Create(self, beam: Dict[str, str]) -> np.ndarray:
        if beam["PrimaryDosimeterUnit"] != "MU":
            return None

        metersetWeights = self.GetMetersetWeights(beam["ControlPointSequence"])
        metersets = self.ConvertMetersetWeightsToMetersets(beam["MU"], metersetWeights)

        return self.UndoCummulativeSum(metersets)

    def GetCumulativeMetersets(self, beam):
        metersetWeights = self.GetMetersetWeights(beam["ControlPointSequence"])
        metersets = self.ConvertMetersetWeightsToMetersets(beam["MU"], metersetWeights)
        return metersets

    @staticmethod
    def GetMetersetWeights(ControlPoints):
        return np.array(
            [cp.CumulativeMetersetWeight for cp in ControlPoints], dtype=float
        )

    @staticmethod
    def ConvertMetersetWeightsToMetersets(beamMeterset, metersetWeights):
        return beamMeterset * metersetWeights / metersetWeights[-1]

    @staticmethod
    def UndoCummulativeSum(cummulativeSum):
        """
            Returns the values whose cummulative sum is "cummulativeSum"
        :param cummulativeSum:
        :return:
        """

        values = np.zeros(len(cummulativeSum))
        delta_prev = 0.0
        for i in range(len(values) - 1):
            delta_curr = cummulativeSum[i + 1] - cummulativeSum[i]
            values[i] = 0.5 * delta_prev + 0.5 * delta_curr
            delta_prev = delta_curr

        values[-1] = 0.5 * delta_prev

        return values
