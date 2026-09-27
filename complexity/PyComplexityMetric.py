import numpy
import numpy as np

from complexity.ApertureMetric import EdgeMetricBase
from complexity.EsapiApertureMetric import ComplexityMetric
from complexity.PyApertureMetric import (
    PyAperturesFromBeamCreator,
    PyMetersetsFromMetersetWeightsCreator,
    PyAperture,
)

from typing import Any


class PyEdgeMetricBase(EdgeMetricBase):
    def Calculate(self, aperture: PyAperture) -> float:
        return self.DivisionOrDefault(aperture.side_perimeter(), aperture.Area())

    @staticmethod
    def DivisionOrDefault(a: float, b: float) -> float:
        return a / b if b != 0 else 0.0


class PyComplexityMetric(ComplexityMetric):
    # TODO add unit tests

    def CalculateForPlan(
        self, patient: None = None, plan: dict[str, Any] | None = None
    ) -> float:
        """
            Returns the complexity metric of a plan, calculated as
            the weighted sum of the individual metrics for each beam
        :param patient: Patient Class
        :param plan: Plan class
        :return: metric
        """
        weights = self.GetWeightsPlan(plan)
        metrics = self.GetMetricsPlan(patient, plan)

        return self.WeightedSum(weights, metrics)

    def GetWeightsPlan(self, plan: dict[str, Any]) -> list[float]:
        """
             Returns the weights of a plan's beams
             by default, the weights are the meterset values per beam
        :param plan: DicomParser plan dict
        """
        return self.GetMeterSetsPlan(plan)

    def GetMeterSetsPlan(self, plan: dict[str, Any]) -> list[float]:
        """
            Returns the total metersets of a plan's beams
        :param plan: DicomParser plan dictionaty
        :return: metersets of a plan's beams
        """

        metersets = []
        for k, beam in plan["beams"].items():
            if "MU" in beam:
                if beam["MU"] > 0:
                    metersets.append(float(beam["MU"]))

        return metersets

    def GetMetersetsBeam(self, beam: dict[str, Any]) -> np.ndarray:
        """
            Returns the metersets of a beam's control points
        :param beam:
        :return:
        """
        return PyMetersetsFromMetersetWeightsCreator().Create(beam)

    def CalculateForPlanPerBeam(
        self, patient: None, plan: dict[str, Any]
    ) -> list[float]:
        """
            Returns the unweighted metrics of a plan's non-setup beams
        :param patient:
        :param plan:
        :return:
        """
        values = []
        for k, beam in plan["beams"].items():
            # check if treatment beam
            if beam["TreatmentDeliveryType"] == "TREATMENT":
                if beam["MU"] > 0.0:
                    v = self.CalculateForBeam(patient, plan, beam)
                    values.append(v)

        return values

    def CalculatePerAperture(self, apertures: list[PyAperture]) -> list[float]:
        metric = PyEdgeMetricBase()
        return [metric.Calculate(aperture) for aperture in apertures]

    def CalculateForBeamPerAperture(
        self, patient: None, plan: dict[str, Any], beam: dict[str, Any]
    ) -> list[float]:
        apertures = self.CreateApertures(patient, plan, beam)
        return self.CalculatePerAperture(apertures)

    def CreateApertures(
        self, patient: None, plan: dict[str, Any], beam: dict[str, Any]
    ) -> list[PyAperture]:
        """
            Added default parameter to meet Liskov substitution principle
        :param patient:
        :param plan:
        :param beam:
        :return:
        """
        return PyAperturesFromBeamCreator().Create(beam)


class MeanApertureAreaMetric:
    def Calculate(self, aperture):
        """
            Calculates the mean aperture area of all leaf pairs
        :param aperture:
        :return:
        """
        areas = np.array(aperture.LeafPairArea)
        return areas[np.nonzero(areas)].mean()


class MeanAreaMetricEstimator(PyComplexityMetric):
    def CalculatePerAperture(self, apertures):
        metric = MeanApertureAreaMetric()
        return [metric.Calculate(aperture) for aperture in apertures]


class ApertureAreaMetric:
    def Calculate(self, aperture):
        """
            return the aperture area.
        :param aperture:
        :return:
        """
        return aperture.Area()


class AreaMetricEstimator(PyComplexityMetric):
    def CalculatePerAperture(self, apertures):
        metric = ApertureAreaMetric()
        return [metric.Calculate(aperture) for aperture in apertures]


class ApertureIrregularity:
    def Calculate(self, aperture):
        """
            Aperture irregularity (non-circularity) of a single aperture:

                AI = P^2 / (4 * pi * A)

            P is the length of the whole closed aperture contour (leaf-end
            edges and leaf-side edges) and A is the aperture area, as defined
            by Du et al., Med Phys 2014;41:021716, Eqs. (1) and (2).
            AI = 1 for a circle, 4/pi = 1.273 for a square, and grows with the
            narrowness/irregularity of the aperture shape.
        :param aperture: PyAperture class
        :return: dimensionless irregularity >= 1 for open apertures, 0 if closed
        """
        aa = aperture.Area()
        ap = aperture.perimeter()
        return self.DivisionOrDefault(ap ** 2, 4 * np.pi * aa)

    @staticmethod
    def DivisionOrDefault(a, b):
        return a / b if b != 0 else 0


class ApertureIrregularityMetric(PyComplexityMetric):
    def CalculatePerAperture(self, apertures):
        """
            Du W, Cho SH, Zhang X, Hoffman KE, Kudchadker RJ. Quantification of beam
            complexity in intensity-modulated radiation therapy treatment plans. Med
            Phys 2014;41:21716. http://dx.doi.org/10.1118/1.4861821.
        :param apertures: list of beam apertures
        :return:
        """
        metric = ApertureIrregularity()
        return [metric.Calculate(aperture) for aperture in apertures]
