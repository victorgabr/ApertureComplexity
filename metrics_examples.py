import matplotlib.pyplot as plt
import os

from complexity.PyComplexityMetric import (
    PyComplexityMetric,
    MeanAreaMetricEstimator,
    AreaMetricEstimator,
    ApertureIrregularityMetric,
)
from complexity.dicomrt import RTPlan

if __name__ == "__main__":
    # Path to DICOM RTPLAN file - IMRT/VMAT
    # pfile = "RP.dcm"
    path_to_rtplan_file = "RP.dcm"

    # Getting planning data from DICOM file.
    plan_info = RTPlan(filename=path_to_rtplan_file)
    plan_dict = plan_info.get_plan()

    metrics_list = [
        PyComplexityMetric,
        MeanAreaMetricEstimator,
        AreaMetricEstimator,
        ApertureIrregularityMetric,
    ]
    units = ["CI [mm^-1]", "mm^2", "mm^2", "dimensionless"]

    # plotting results
    for unit, cc in zip(units, metrics_list):
        cc_obj = cc()
        # compute per plan
        plan_metric = cc_obj.CalculateForPlan(None, plan_dict)
        print(f"{cc.__name__} Plan Metric - {plan_metric} {unit}")
        for k, beam in plan_dict["beams"].items():
            # skip setup fields
            if beam["TreatmentDeliveryType"] == "TREATMENT" and beam["MU"] > 0:
                fig = plt.figure(figsize=(6, 6))
                # create a subplot
                ax = fig.add_subplot(111)
                cpx_beam_cp = cc_obj.CalculateForBeamPerAperture(
                    None, plan_dict, beam
                )
                ax.plot(cpx_beam_cp)
                ax.set_xlabel("Control Point")
                ax.set_ylabel(f"${unit}$")
                txt = f"Output - Beam name: {beam['BeamName']} - {cc.__name__}"
                ax.set_title(txt)
                plt.show()
