"""
EsapiApertureMetric.py

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

from complexity import ApertureMetric
from complexity.ApertureMetric import Aperture


class ComplexityMetric:
    """
    Abstract class that represents any complexity metric. It
    implements many common methods. Subclasses implement the metric
    calculation.
    """

    def CalculateForPlan(self, patient, plan):
        """
        Return the complexity metric of a plan. The method computes it
        as the weighted sum of the metrics of each beam.
        :param patient: Patient Class
        :param plan: Plan class
        :return: metric
        """
        weights = self.GetWeightsPlan(plan)
        metrics = self.GetMetricsPlan(patient, plan)
        return self.WeightedSum(weights, metrics)

    def GetWeightsPlan(self, plan):
        """
        Return the weights of the beams of a plan. By default, the
        weights are the meterset values of each beam.
        :param plan: DicomParser plan dict
        """
        return self.GetMeterSetsPlan(plan)

    def GetMeterSetsPlan(self, plan):
        """
        Return the total metersets of the beams of a plan.
        :param plan:
        :return: metersets of the beams of the plan
        """
        return NotImplementedError

    def GetMetricsPlan(self, patient, plan):
        """
        Return the unweighted metrics of the beams of a plan.
        :param patient:
        :param plan:
        :return:
        """
        return self.CalculateForPlanPerBeam(patient, plan)

    def CalculateForPlanPerBeam(self, patient, plan):
        """
        Return the unweighted metrics of the non-setup beams of a plan.
        :param patient:
        :param plan:
        :return:
        """
        return NotImplementedError

    def CalculateForBeam(self, patient, plan, beam):
        """
        Return the complexity metric of a beam. The method computes it
        as the weighted sum of the metrics of each control point.
        :param patient:
        :param plan:
        :param beam:
        :return:
        """
        weights = self.GetWeightsBeam(beam)
        values = self.GetMetricsBeam(patient, plan, beam)

        return self.WeightedSum(weights, values)

    def GetWeightsBeam(self, beam):
        """
        Return the weights of the control points of a beam. By
        default, the weights are the meterset values of each control
        point.
        :param beam:
        :return:
        """
        return self.GetMetersetsBeam(beam)

    def GetMetersetsBeam(self, beam):
        """
        Return the metersets of the control points of a beam.
        :param beam:
        :return:
        """

        return MetersetsFromMetersetWeightsCreator().Create(beam)

    def GetMetricsBeam(self, patient, plan, beam):
        """
        Return the unweighted metrics of the control points of a beam.
        :param patient:
        :param plan:
        :param beam:
        :return:
        """
        return self.CalculateForBeamPerAperture(patient, plan, beam)

    def CalculateForBeamPerAperture(self, patient, plan, beam):
        apertures = self.CreateApertures(patient, plan, beam)
        return self.CalculatePerAperture(apertures)

    def CalculatePerAperture(self, param):
        """
        Return the unweighted metrics of a list of apertures.
        A subclass must override this method.
        :param param:
        :return:
        """
        return NotImplementedError

    def CreateApertures(self, patient, plan, beam):
        """
        Return the apertures created from a beam.
        :param patient:
        :param plan:
        :param beam:
        :return:
        """
        return AperturesFromBeamCreator().Create(patient, plan, beam)

    def CalculatePerControlPointWeighted(self, patient, plan, beam):
        """
        Return the weighted metrics of the control points of a beam.
        :param patient:
        :param plan:
        :param beam:
        :return:
        """
        return self.WeightedValues(
            self.GetWeightsBeam(beam), self.GetMetricsBeam(patient, plan, beam)
        )

    def CalculatePerControlPointUnweighted(self, patient, plan, beam):
        """
        Return the unweighted metrics of the control points of a beam.
        :param patient:
        :param plan:
        :param beam:
        :return:
        """
        return self.GetMetricsBeam(patient, plan, beam)

    def CalculatePerControlPointWeightsOnly(self, beam):
        """
        Return the weights of the control points of a beam.
        :param beam:
        :return:
        """
        return self.GetWeightsBeam(beam)

    def WeightedSum(self, weights, values):
        """
        Return the weighted sum of the given values and weights.
        :param weights:
        :param values:
        :return:
        """
        return sum(self.WeightedValues(weights, values))

    @staticmethod
    def WeightedValues(weights, values):
        weightSum = sum(weights)
        result = []
        for i in range(len(values)):
            v = (weights[i] / weightSum) * values[i]
            result.append(v)
        return result


class MetersetsFromMetersetWeightsCreator:
    def Create(self, beam):
        if beam["PrimaryDosimeterUnit"] != "MU" or "MU" not in beam:
            return None

        metersetWeights = self.GetMetersetWeights(beam["ControlPointSequence"])
        metersets = self.ConvertMetersetWeightsToMetersets(beam["MU"], metersetWeights)

        return self.UndoCummulativeSum(metersets)

    @staticmethod
    def GetMetersetWeights(ControlPoints):
        return [float(cp.CumulativeMetersetWeight) for cp in ControlPoints]

    @staticmethod
    def ConvertMetersetWeightsToMetersets(beamMeterset, metersetWeights):
        finalMetersetWeight = metersetWeights[-1]
        return [beamMeterset * x / finalMetersetWeight for x in metersetWeights]

    @staticmethod
    def UndoCummulativeSum(cummulativeSum):
        """
        Return the values whose cumulative sum equals the input array.
        :param cummulativeSum:
        :return:
        """
        values = [0] * len(cummulativeSum)

        delta_prev = 0.0
        for i in range(len(values) - 1):
            delta_curr = cummulativeSum[i + 1] - cummulativeSum[i]
            values[i] = 0.5 * delta_prev + 0.5 * delta_curr
            delta_prev = delta_curr

        values[-1] = 0.5 * delta_prev

        return values


class AperturesFromBeamCreator:
    def Create(self, patient, plan, beam):
        apertures = []
        leafWidths = self.GetLeafWidths(patient, plan, beam)

        for controlPoint in beam.ControlPointSequence:
            leafPositions = self.GetLeafPositions(controlPoint)
            jaw = self.CreateJaw(controlPoint)
            apertures.append(Aperture(leafPositions, leafWidths, jaw))

        return apertures

    @staticmethod
    def CreateJaw(cp):
        left = cp.JawPositions.X1
        top = cp.JawPositions.Y2
        right = cp.JawPositions.X2
        bottom = cp.JawPositions.Y1

        return [left, top, right, bottom]

    def GetLeafWidths(self, patient, plan, beam):
        return self.GetLeafWidthsFromAria(patient, plan, beam)

    def GetLeafWidthsFromAria(self, patient, plan, beam):
        return NotImplementedError

    def GetLeafPositions(self, controlPoint):
        # Leaf positions are given from bottom to top by ESAPI,
        # but the Aperture class expects them from top to bottom
        #                leafPositions[i, j] = controlPoint.LeafPositions[i, n - j - 1]

        #       return leafPositions
        return NotImplementedError


class EdgeMetric(ComplexityMetric):
    def CalculatePerAperture(self, apertures):
        metric = ApertureMetric.EdgeMetricBase()
        return [metric.Calculate(aperture) for aperture in apertures]
