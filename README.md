# Aperture Complexity - IMRT/VMAT Plans

It is a Python 3.x port of the Eclipse ESAPI plug-in script. 
As such, it aims to contain the complete functionality of  the aperture complexity analysis.

Since it uses DICOM standard, this module extends the methodology to any TPS that exports DICOM-RP files.

More on misc.py file

## Getting Started

Calculating weighed plan complexity - only IMRT or VMAT.


    python ComplexityScript.py path_to_dicom_RP_file

Plotting aperture complexity per beam aperture using matplotlib.

```python
import matplotlib.pyplot as plt

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
            if beam["TreatmentDeliveryType"] == "TREATMENT" and beam["MU"] > 0.0:
                fig = plt.figure(figsize=(6, 6))
                # create a subplot
                ax = fig.add_subplot(111)
                cpx_beam_cp = cc_obj.CalculateForBeamPerAperture(
                    None, plan_dict, beam
                )
                ax.plot(cpx_beam_cp)
                ax.set_xlabel("Control Point")
                ax.set_ylabel(f"${unit}$")
                txt = f"{file_name} - Beam name: {beam['BeamName']} - {cc.__name__}"
                ax.set_title(txt)
                plt.show()

            fig, ax = plt.subplots()
            cpx_beam_cp = cc_obj.CalculateForBeamPerAperture(None, plan_dict, beam)
            ax.plot(cpx_beam_cp)
            ax.set_xlabel("Control Point")
            ax.set_ylabel(f"${unit}$")
            txt = f"Beam name: {k} - {cc.__name__} per control point"
            ax.set_title(txt)
            plt.show()
```
## Example result
Beam 1 

![beam_1_complexity](https://user-images.githubusercontent.com/6777517/37774893-336082a8-2dc0-11e8-9c3f-6b15d8488d9f.png)

      
## Requirements
    pydicom, numpy, pandas, pytest for unit testing
    
## Installing
    python setup.py install

## Contributing

Any bug fixes or improvements are welcome.

## Author
    Victor Gabriel Leandro Alves, D.Sc.
    Copyright 2017-2018
    
## Acknowledgments

University of Michigan, Radiation Oncology
[https://github.com/umro/Complexity](https://github.com/umro/Complexity)
