"""Classes to estimate many complexity metrics"""
# Copyright (c) 2017-2018 Victor G. L. Alves

import numpy as np
import pandas as pd
from scipy import integrate

from complexity.PyApertureMetric import (
    PyMetersetsFromMetersetWeightsCreator,
    PyAperturesFromBeamCreator,
)
from complexity.PyComplexityMetric import PyComplexityMetric


class LeafSequenceVariability:
    def Calculate(self, aperture, aav_norm):
        """
            variability in segment shape for a
            specific plan. The shape of each segment is considered,
            based on the change in leaf position between adjacent MLC
            leaves. This is calculated for leaves on each bank that define
            a specific segment. The LSV is defined using N, the number
            of open leaves constituting the beam and the coordinates of
            the leaf positions. Leaves are not considered if they are
            positioned under the jaws. The position of each leaf is incor-
            porated by defining pos max .
            The second IMRT segment characteristic that is considered
            for the overall determination of complexity is the area
            of the beam aperture. The aperture area variability AAV is
            used to characterize the variation in segment area relative to
            the maximum aperture defined by all of the segments. Segments
            that are more similar in area to the maximum beam
            aperture contribute to a larger score.

            Reference:
            McNiven AL, Sharpe MB, Purdie TG. A new metric for assessing IMRT
            modulation complexity and plan deliverability. Med Phys 2010;37:505–15.
            http://dx.doi.org/10.1118/1.3276775.

        :param aav_norm: Maximum aperture area
        :param aperture: Control point PyAperture class
        :return: product LSV * AAV
        """

        pos = [
            (lp.Left, lp.Right) for lp in aperture.LeafPairs if not lp.IsOutsideJaw()
        ]
        N = len(pos)
        pos_max = np.max(pos, axis=0) - np.min(pos, axis=0)
        tmp = np.sum(pos_max + np.diff(pos, axis=0), axis=0) / (N * pos_max)
        LSV = np.prod(tmp)

        num = sum(
            ([lp.FieldSize() for lp in aperture.LeafPairs if not lp.IsOutsideJaw()])
        )
        AAV = self.DivisionOrDefault(num, aav_norm)

        return LSV * AAV

    @staticmethod
    def DivisionOrDefault(a, b):
        return a / b if b != 0 else 0


class ModulationComplexityScore(PyComplexityMetric):
    """ Reference:
            McNiven AL, Sharpe MB, Purdie TG. A new metric for assessing IMRT
            modulation complexity and plan deliverability. Med Phys 2010;37:505–15.
            http://dx.doi.org/10.1118/1.3276775."""

    def CalculatePerAperture(self, apertures):
        aav_norm = 0
        for aperture in apertures:
            posi = [
                (lp.Left, lp.Right)
                for lp in aperture.LeafPairs
                if not lp.IsOutsideJaw()
            ]
            posi_max = np.max(posi, axis=0)
            aav_norm += abs(posi_max[1] - posi_max[0])
        metric = LeafSequenceVariability()

        return [metric.Calculate(aperture, aav_norm) for aperture in apertures]


class ModulationIndexScore(PyComplexityMetric):

    def CalculateForPlan(self, patient=None, plan=None, k=0.02):
        """
            Jong Min Park et al - "Modulation indices for volumetric modulated arc therapy"
            https://iopscience.iop.org/article/10.1088/0031-9155/59/23/7315
            See table 1
        """
        apertures = []
        cumulative_metersets = []
        meterset_creator = PyMetersetsFromMetersetWeightsCreator()
        for k, beam in plan["beams"].items():
            apertures += PyAperturesFromBeamCreator().Create(beam)
            cum = meterset_creator.GetCumulativeMetersets(beam)
            cumulative_metersets.append(cum)

        cumulative_mu = np.concatenate(cumulative_metersets)
        mid = ModulationIndexTotal(apertures, cumulative_mu)
        return mid.calculate_integrate(k=k)

    def CalculateForBeam(self, patient, plan, beam, k=0.02):
        apertures = PyAperturesFromBeamCreator().Create(beam)
        cumulative_metersets = PyMetersetsFromMetersetWeightsCreator().GetCumulativeMetersets(
            beam
        )
        mid = ModulationIndexTotal(apertures, cumulative_metersets)
        return mid.calculate_integrate(k=k)


class ModulationIndexTotal:
    def __init__(self, apertures, cumulative_mu):
        # beam data
        self.apertures = apertures
        self.Ncp = len(self.apertures)

        # meterset data
        self.cumulative_mu = self.get_mu_data(cumulative_mu)

        # MLC position data
        self.mlc_positions = self.get_positions(self.apertures)
        self.mlc_speed = (
            self.mlc_positions.diff().abs().T / self.cumulative_mu["time"]
        ).T
        self.mlc_speed_std = self.mlc_speed.std()
        self.mlc_acceleration = (
            self.mlc_speed.diff().abs().T / self.cumulative_mu["time"]
        ).T
        self.mlc_acceleration_std = self.mlc_acceleration.std()

        # gantry data
        gantry_angles = np.array([ap.GantryAngle for ap in self.apertures])
        self.gantry = pd.DataFrame(gantry_angles, columns=["gantry"])
        self.gantry["delta_gantry"] = self.rolling_apply(
            self.delta_gantry, gantry_angles
        )
        self.gantry["gantry_speed"] = (
            self.gantry["delta_gantry"] / self.cumulative_mu["time"]
        )
        self.gantry["delta_gantry_speed"] = self.gantry["gantry_speed"].diff().abs()
        self.gantry["gantry_acc"] = (
            self.gantry["delta_gantry_speed"] / self.cumulative_mu["time"]
        )

        # dose rate data
        self.dose_rate = pd.DataFrame(
            self.cumulative_mu["delta_mu"] / self.cumulative_mu["time"], columns=["DR"]
        )
        self.dose_rate["delta_dose_rate"] = self.dose_rate.diff().abs()

    def get_mu_data(self, cumulative_mu):
        # meterset data
        tmp = pd.DataFrame(cumulative_mu, columns=["MU"])
        tmp["delta_mu"] = tmp.diff().abs()
        tmp["time"] = tmp["delta_mu"].apply(self.calculate_time)
        return tmp

    @staticmethod
    def calculate_time(delta_mu):
        """
            Calculate time between control points in seconds
        :param delta_mu:
        :return: time in seconds
        """
        if delta_mu <= 4.238:
            return 2.0341 / 4.8
        elif delta_mu > 4.238:
            return delta_mu / 10

    @staticmethod
    def delta_gantry(param):
        alpha, beta = param
        phi = abs(beta - alpha) % 360
        return 360 - phi if phi > 180 else phi

    @staticmethod
    def rolling_apply(fun, a, w=2):
        r = np.empty(a.shape)
        r.fill(np.nan)
        for i in range(w - 1, a.shape[0]):
            r[i] = fun(a[(i - w + 1) : i + 1])
        return r

    @staticmethod
    def get_positions(apertures):
        pos = []
        for aperture in apertures:
            cp_pos = [(lp.Left, lp.Right) for lp in aperture.LeafPairs]
            arr = np.ravel(cp_pos)
            pos.append(arr)

        return pd.DataFrame(pos)

    def calc_mi_speed(self, mlc_speed, speed_std, k=1.0):

        calc_z = (
            lambda f: 1 / (self.Ncp - 1) * np.sum(np.sum(mlc_speed > f * speed_std))
        )
        res = integrate.quad(calc_z, 0, k)
        return res[0]

    def calc_mi_acceleration(
        self, mlc_speed, speed_std, mlc_acc, mlc_acc_std, k=1.0, alpha=1.0
    ):

        z_acc = lambda f: (1 / (self.Ncp - 2)) * np.nansum(
            np.nansum(
                np.logical_or(
                    mlc_speed > f * speed_std, mlc_acc > alpha * f * mlc_acc_std
                )
            )
        )
        res = integrate.quad(z_acc, 0, k)
        return res[0]

    def calc_mi_total(
        self,
        mlc_speed,
        speed_std,
        mlc_acc,
        mlc_acc_std,
        k=1.0,
        alpha=1.0,
        WGA=None,
        WMU=None,
    ):

        z_total = lambda f: (1 / (self.Ncp - 2)) * np.nansum(
            np.nansum(
                np.logical_or(
                    mlc_speed > f * speed_std, mlc_acc > alpha * f * mlc_acc_std
                ),
                axis=1,
            )
            * WGA
            * WMU
        )

        res = integrate.quad(z_total, 0, k)

        return res[0]

    def calculate_integrate(self, k=1.0, beta=2.0, alpha=2.0):

        # fill NAN
        mlc_speed = np.nan_to_num(self.mlc_speed)
        mlc_acc = np.nan_to_num(self.mlc_acceleration)

        mis = self.calc_mi_speed(mlc_speed, self.mlc_speed_std.values, k)

        alpha_acc = 1.0 / self.cumulative_mu["time"].mean()
        mia = self.calc_mi_acceleration(
            mlc_speed,
            self.mlc_speed_std.values,
            mlc_acc,
            self.mlc_acceleration_std.values,
            k=k,
            alpha=alpha_acc,
        )

        gantry_acc = self.gantry["gantry_acc"].values
        WGA = beta / (1 + (beta - 1) * np.exp(-gantry_acc / alpha))

        # Wmu
        delta_dose_rate = self.dose_rate["delta_dose_rate"].values
        WMU = beta / (1 + (beta - 1) * np.exp(-delta_dose_rate / alpha))

        mit = self.calc_mi_total(
            mlc_speed,
            self.mlc_speed_std.values,
            mlc_acc,
            self.mlc_acceleration_std.values,
            k=k,
            alpha=alpha_acc,
            WGA=WGA,
            WMU=WMU,
        )

        return mis, mia, mit

    def calculate(self, f=1.0, beta=2.0, alpha=2.0):

        # speed MI
        mask_speed_std = self.mlc_speed > f * self.mlc_speed_std
        Ns = mask_speed_std.sum().sum()
        z_speed = 1 / (self.Ncp - 1) * Ns

        # acc MI
        alpha_acc = 1.0 / self.cumulative_mu["time"].mean()
        mask_acc_std = self.mlc_acceleration > alpha_acc * f * self.mlc_acceleration_std

        mask_acc_mi = np.logical_or(mask_speed_std, mask_acc_std)
        Nacc = mask_acc_mi.sum().sum()
        z_acc = 1 / (self.Ncp - 2) * Nacc

        # Total MI
        gantry_acc = self.gantry["gantry_acc"]
        WGA = beta / (1 + (beta - 1) * np.exp(-gantry_acc / alpha))

        # Wmu
        delta_dose_rate = self.dose_rate["delta_dose_rate"]
        WMU = beta / (1 + (beta - 1) * np.exp(-delta_dose_rate / alpha))

        tmp = mask_acc_mi.multiply(WGA, axis="index").multiply(WMU, axis="index")
        Mti = tmp.sum().sum() / (self.Ncp - 2)

        return z_speed, z_acc, Mti
