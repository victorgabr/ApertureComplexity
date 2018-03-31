#Typing imports
from typing import List, Dict
from pydicom.dataset import Dataset

import numpy as np

from complexity.ApertureMetric import Aperture, LeafPair, Jaw


class PyLeafPair(LeafPair):

    def __init__(self, left: float, right: float, width: float, top: float, jaw: Jaw) -> None:
        super().__init__(left, right, width, top, jaw)

    def __repr__(self):
        txt = 'Leaf Pair: left: %1.1f top: %1.1f right: %1.1f botton: %1.1f' \
              % (self.Left, self.Top, self.Right, self.Bottom)

        return txt


class PyAperture(Aperture):

    def __init__(self, leaf_positions: np.ndarray, leaf_widths: np.ndarray, jaw: List[float],
                 gantry_angle: float) -> None:
        super().__init__(leaf_positions, leaf_widths, jaw)
        self.gantry_angle = gantry_angle

    def CreateLeafPairs(self, positions: np.ndarray, widths: np.ndarray,
                        jaw: Jaw) -> List[PyLeafPair]:
        leaf_tops = self.GetLeafTops(widths)

        pairs = []
        for i in range(len(widths)):
            lp = PyLeafPair(positions[0, i], positions[1, i], widths[i], leaf_tops[i], jaw)
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
        jaw = self.CreateJaw(beam)

        for controlPoint in beam['ControlPointSequence']:
            gantry_angle = float(controlPoint.GantryAngle) if 'GantryAngle' in controlPoint else beam[
                'GantryAngle']
            leafPositions = self.GetLeafPositions(controlPoint)
            if leafPositions is not None:
                apertures.append(PyAperture(leafPositions, leafWidths, jaw, gantry_angle))

        return apertures

    @staticmethod
    def CreateJaw(beam: dict) -> List[float]:
        """
            but the Aperture class expects cartesian y axis
        :param beam:
        :return:
        """

        # if there is no X jaws, consider open 400 mm
        left = float(beam['ASYMX'][0]) if 'ASYMX' in beam else -200.0
        right = float(beam['ASYMX'][1]) if 'ASYMX' in beam else 200.0
        top = float(beam['ASYMY'][0]) if 'ASYMY' in beam else -200.0
        bottom = float(beam['ASYMY'][1]) if 'ASYMY' in beam else 200.0

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

        bs = beam_dict['BeamLimitingDeviceSequence']
        # the script only takes MLCX as parameter
        for b in bs:
            if b.RTBeamLimitingDeviceType in ['MLCX', 'MLCX1', 'MLCX2']:
                return np.diff(b.LeafPositionBoundaries)

    def GetLeafTops(self, beam_dict: Dict) -> np.ndarray:
        """
            Get MLCX leaf Tops from  BeamLimitingDeviceSequence
            (300a, 00be) Leaf Position Boundaries Tag
        :param beam_dict: Dicomparser Beam dict from plan_dict
        :return: MLCX leaf width
        """
        bs = beam_dict['BeamLimitingDeviceSequence']
        for b in bs:
            if b.RTBeamLimitingDeviceType == 'MLCX':
                return np.array(b.LeafPositionBoundaries[:-1], dtype=float)

    def GetLeafPositions(self, control_point: Dataset) -> np.ndarray:
        """
            Leaf positions are given from bottom to top by ESAPI,
            but the Aperture class expects them from top to bottom
            Leaf Positions are mechanical boundaries projected onto Isocenter plane
            # TODO add halcyon MLC positions
        :param control_point:
        """
        if 'BeamLimitingDevicePositionSequence' in control_point:
            pos = control_point.BeamLimitingDevicePositionSequence[-1]
            mlc_open = pos.LeafJawPositions
            n_pairs = int(len(mlc_open) / 2)
            bank_a_pos = mlc_open[:n_pairs]
            bank_b_pos = mlc_open[n_pairs:]

            return np.vstack((bank_a_pos, bank_b_pos))


class PyMetersetsFromMetersetWeightsCreator:

    def Create(self, beam: Dict[str, str]) -> np.ndarray:
        if beam['PrimaryDosimeterUnit'] != 'MU':
            return None

        metersetWeights = self.GetMetersetWeights(beam['ControlPointSequence'])
        metersets = self.ConvertMetersetWeightsToMetersets(beam['MU'], metersetWeights)

        return self.UndoCummulativeSum(metersets)

    def GetCumulativeMetersets(self, beam):
        metersetWeights = self.GetMetersetWeights(beam['ControlPointSequence'])
        metersets = self.ConvertMetersetWeightsToMetersets(beam['MU'], metersetWeights)
        return metersets

    @staticmethod
    def GetMetersetWeights(ControlPoints):
        return np.array([cp.CumulativeMetersetWeight for cp in ControlPoints], dtype=float)

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
