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
                txt = f"{file_name} - Beam name: {beam['BeamName']} - {cc.__name__}"
                ax.set_title(txt)
                plt.show()

```
## Aperture geometry used by the metrics

`Aperture` exposes two different perimeters, because the published metrics need two
different definitions:

| Method | Definition | Used by |
| --- | --- | --- |
| `side_perimeter()` | Edges perpendicular to the leaf travel direction: leaf-end edges between adjacent leaf pairs plus the top and bottom ends of the open region | Edge metric (Younge et al., *IJRBP* 2012;82:1210-7) |
| `leaf_side_perimeter()` | Edges parallel to the leaf travel direction: the two lateral sides of every open leaf pair | — |
| `perimeter()` | `side_perimeter() + leaf_side_perimeter()`, i.e. the whole closed contour of the aperture | Aperture irregularity (Du et al., *Med Phys* 2014;41:021716) |

`ApertureIrregularityMetric` computes `AI = P^2 / (4 * pi * A)` from the closed-contour
perimeter `P` and the aperture area `A`. `AI` is a dimensionless shape factor: 1 for a
circle, `4/pi` = 1.273 for a square, and larger for narrower or more irregular
apertures. An MLC aperture is a staircase, so the value a rounded aperture approaches
is `16/pi^2` = 1.62, and any open aperture returns `AI` >= 1.

## Example result
Beam 1 

![beam_1_complexity](https://user-images.githubusercontent.com/6777517/37774893-336082a8-2dc0-11e8-9c3f-6b15d8488d9f.png)

      
## Requirements

Python 3.12+ and [uv](https://docs.astral.sh/uv/).

- Core: `pydicom`, `numpy`, `pandas`, `scipy`
- Optional (plotting): `matplotlib`
- Dev (testing): `pytest`

## Installing

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
# create the virtual environment and install the project + dependencies
uv sync

# run the CLI
uv run python ComplexityScript.py path_to_dicom_RP_file

# run the unit tests
uv run pytest
```

Or install the package into an existing environment:

```bash
uv pip install .
```

## Contributing

Any bug fixes or improvements are welcome.

## Author
    Victor Gabriel Leandro Alves, D.Sc.
    Copyright 2017-2018
    
## Acknowledgments

University of Michigan, Radiation Oncology
[https://github.com/umro/Complexity](https://github.com/umro/Complexity)
