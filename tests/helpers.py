"""Shared builders for synthetic apertures, beams, and plans.

The builders produce plain objects (numpy arrays, dicts, pydicom
Datasets) that match what the DICOM parser returns, so the metric
classes can be tested without a DICOM file.
"""

import numpy as np
from pydicom.dataset import Dataset

from complexity.ApertureMetric import Aperture

# left, top, right, bottom; fully open jaw (top > bottom convention)
OPEN_JAW = [-400.0, 200.0, 400.0, -200.0]


def make_aperture(lefts, rights, widths, jaw=OPEN_JAW):
    """
        Aperture from one position per bank; leaf pairs ordered top to bottom.
    :param lefts: bank A (left) leaf positions, top to bottom
    :param rights: bank B (right) leaf positions, top to bottom
    :param widths: leaf pair widths, top to bottom
    :param jaw: jaw position [left, top, right, bottom]
    """
    positions = np.array([list(lefts), list(rights)], dtype=float)
    return Aperture(positions, np.array(widths, dtype=float), list(jaw))


def uniform_aperture(n_leaves, leaf_width, left, right, jaw=OPEN_JAW):
    """Aperture of n identical leaf pairs, all opened from left to right."""
    return make_aperture(
        [left] * n_leaves, [right] * n_leaves, [leaf_width] * n_leaves, jaw
    )


def make_mlc_dataset(n_pairs=10, leaf_width=10.0):
    """BeamLimitingDeviceSequence item with MLCX leaf position boundaries."""
    ds = Dataset()
    ds.RTBeamLimitingDeviceType = "MLCX"
    ds.LeafPositionBoundaries = [i * leaf_width for i in range(n_pairs + 1)]
    return ds


def make_control_point(cumulative_meterset_weight, leaf_openings, gantry_angle=0.0):
    """
        Control point with MLC positions.
    :param cumulative_meterset_weight: cumulative MU weight of the control point
    :param leaf_openings: list of (left, right) per leaf pair
    :param gantry_angle: gantry angle of the control point
    """
    cp = Dataset()
    cp.CumulativeMetersetWeight = cumulative_meterset_weight
    cp.GantryAngle = gantry_angle
    bank_a = [left for left, _ in leaf_openings]
    bank_b = [right for _, right in leaf_openings]
    blp = Dataset()
    blp.RTBeamLimitingDeviceType = "MLCX"
    blp.LeafJawPositions = bank_a + bank_b
    cp.BeamLimitingDevicePositionSequence = [blp]
    return cp


def make_beam(cumulative_meterset_weights, leaf_openings_per_cp, total_mu=None):
    """
        Beam dict as returned by RTPlan.get_beams for one treatment beam.
    :param cumulative_meterset_weights: cumulative MU weight per control point
    :param leaf_openings_per_cp: per control point, the (left, right) opening
        of each leaf pair
    :param total_mu: beam MU; defaults to the last cumulative weight
    """
    n_pairs = len(leaf_openings_per_cp[0])
    beam = {
        "PrimaryDosimeterUnit": "MU",
        "TreatmentDeliveryType": "TREATMENT",
        "GantryAngle": 0.0,
        "BeamLimitingDeviceSequence": [make_mlc_dataset(n_pairs)],
        "ControlPointSequence": [
            make_control_point(weight, openings)
            for weight, openings in zip(
                cumulative_meterset_weights, leaf_openings_per_cp
            )
        ],
    }
    if total_mu is None:
        total_mu = cumulative_meterset_weights[-1]
    beam["MU"] = float(total_mu)
    return beam


def make_plan(beams):
    """Plan dict as returned by RTPlan.get_plan."""
    return {"beams": beams}
