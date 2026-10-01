# Aperture Complexity

Complexity is a Python library and command-line tool. It measures the
geometric complexity of IMRT and VMAT treatment plans. It reads one DICOM
RT-PLAN file (`*.dcm`). It computes published complexity metrics for every
beam and control point.

The package is a port of the original
[Eclipse ESAPI plug-in](https://github.com/umro/Complexity). The package uses
the DICOM standard, so it runs on plans from any treatment planning system
(TPS).

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-green)](LICENSE)

## What is aperture complexity?

In intensity-modulated radiation therapy (IMRT) and volumetric modulated arc
therapy (VMAT), a multileaf collimator (MLC) shapes the beam. The MLC moves
many small leaves to draw the target shape at each control point.

Some shapes are easy to draw. A simple square field is easy. A shape with
many small, separated openings takes longer to deliver. Aperture complexity
metrics give a number for this difficulty. Studies connect high complexity
to longer delivery time, more machine motion, and harder plan verification.

Each metric takes the MLC leaf positions at one control point and returns
one number. The package also averages the numbers for a beam and for a
plan. The average uses the monitor units (MU) at each control point as its
weight.

## Metrics

| Metric | Class | Unit | Measures | Reference |
| --- | --- | --- | --- | --- |
| Aperture complexity (edge) | `PyComplexityMetric` | mm⁻¹ | Leaf-edge length per unit area | Younge et al., *IJRBP* 2012;82:1210-7 |
| Aperture irregularity | `ApertureIrregularityMetric` | – | Shape deviation from a circle (≥ 1) | Du et al., *Med Phys* 2014;41:21716 |
| Mean aperture area | `MeanAreaMetricEstimator` | mm² | MU-weighted mean opening | umro/Complexity |
| Total aperture area | `AreaMetricEstimator` | mm² | Sum of the openings | umro/Complexity |
| Leaf sequence variability | `LeafSequenceVariability` | – | Variation of leaf position across leaves | McNiven et al., *Med Phys* 2010;37:505-15 |
| Modulation complexity score | `ModulationComplexityScore` | – | Combined leaf-sequence and area variability | McNiven et al., *Med Phys* 2010;37:505-15 |
| Modulation index (score) | `ModulationIndexScore` | – | MLC and gantry motion per MU | Park et al., *Med Phys* 2014;59:7315 |
| Modulation index (total) | `ModulationIndexTotal` | – | Speed and acceleration modulation index | Park et al., *Med Phys* 2014;59:7315 |

The first four classes are in `complexity.PyComplexityMetric`. The last four
are in `complexity.misc`.

## Quick Start

Install [uv](https://docs.astral.sh/uv/). Then run:

```bash
# 1. Create the environment and install the project + dependencies
uv sync

# 2. Run the CLI on the bundled sample plan (no data needed)
uv run aperture-complexity tests/tests_data/RP_FiF.dcm
```

Expected output:

```
elapsed 0.05
Reference: https://github.com/umro/Complexity
Python version by Victor Gabriel Leandro Alves, D.Sc. - victorgabr@gmail.com
Plan tests/tests_data/RP_FiF.dcm aperture complexity: 0.030 [mm-1]:
```

The sample plan has one 100 × 100 mm square field. This field gives a low
edge metric (0.030 mm⁻¹). The aperture irregularity is the exact value for
a square, `4/π` = 1.273.

To measure your own plan, replace the path with the path to your DICOM
RT-PLAN file:

```bash
uv run aperture-complexity /path/to/your/RP.dcm
```

## Library Example

```python
import matplotlib.pyplot as plt

from complexity.PyComplexityMetric import (
    PyComplexityMetric,
    MeanAreaMetricEstimator,
    AreaMetricEstimator,
    ApertureIrregularityMetric,
)
from complexity.dicomrt import RTPlan

# Path to a DICOM RT-PLAN file (IMRT/VMAT)
path_to_rtplan_file = "RP.dcm"

# Read the plan
plan_dict = RTPlan(filename=path_to_rtplan_file).get_plan()

metrics = [
    (PyComplexityMetric, "CI [mm^-1]"),
    (MeanAreaMetricEstimator, "mm^2"),
    (AreaMetricEstimator, "mm^2"),
    (ApertureIrregularityMetric, "dimensionless"),
]

for metric_class, unit in metrics:
    metric = metric_class()

    # One number for the whole plan (MU-weighted)
    print(f"{metric_class.__name__} plan: {metric.CalculateForPlan(None, plan_dict):.4f} {unit}")

    # One number per control point, for each beam
    for beam in plan_dict["beams"].values():
        if beam["TreatmentDeliveryType"] == "TREATMENT" and beam["MU"] > 0:
            values = metric.CalculateForBeamPerAperture(None, plan_dict, beam)
            plt.plot(values)
            plt.xlabel("Control point")
            plt.ylabel(unit)
            plt.title(f"{beam['BeamName']} - {metric_class.__name__}")
            plt.show()
```

Every metric class has the same three methods:

| Method | Returns |
| --- | --- |
| `CalculatePerAperture(apertures)` | One value per control point |
| `CalculateForBeamPerAperture(patient, plan, beam)` | One value per control point of a beam |
| `CalculateForPlan(patient, plan)` | One MU-weighted value for the plan |

A `PyAperture` object (see `complexity.PyApertureMetric`) holds the leaf
positions, the jaw positions, and the gantry angle of one control point.
Build a `PyAperture` object from a beam dict with
`PyAperturesFromBeamCreator().Create(beam)`.

## Command Line

The CLI has three forms:

```bash
uv run aperture-complexity path/to/RP.dcm     # console script
uv run python -m complexity path/to/RP.dcm    # module form
uv run python ComplexityScript.py path/to/RP.dcm   # legacy wrapper
```

## Project Layout

```
complexity/
  dicomrt.py            Read a DICOM RT-PLAN into a plain dict
  ApertureMetric.py     Aperture geometry: area, perimeter, leaf pairs
  PyApertureMetric.py   Build Aperture objects from a beam dict
  PyComplexityMetric.py Edge, area, and irregularity metrics
  misc.py               LSV, modulation complexity, and modulation index metrics
  __main__.py           Command-line interface
ComplexityScript.py     Legacy entry point (kept for old scripts)
tests/                  Unit tests and a sample RT-PLAN file
```

## Aperture Geometry Used by the Metrics

`Aperture` has two perimeter definitions, because the published metrics
need two definitions:

| Method | Definition | Used by |
| --- | --- | --- |
| `side_perimeter()` | Edges perpendicular to the leaf travel direction: leaf-end edges between adjacent leaf pairs plus the top and bottom ends of the open region | Edge metric (Younge et al., *IJRBP* 2012;82:1210-7) |
| `leaf_side_perimeter()` | Edges parallel to the leaf travel direction: the two lateral sides of every open leaf pair | – |
| `perimeter()` | `side_perimeter() + leaf_side_perimeter()`, that is, the whole closed contour of the aperture | Aperture irregularity (Du et al., *Med Phys* 2014;41:21716) |

`ApertureIrregularityMetric` computes `AI = P^2 / (4 * pi * A)` from the
closed-contour perimeter `P` and the aperture area `A`. `AI` is a
dimensionless shape factor. A circle gives 1. A square gives `4/pi` =
1.273. Narrower and more irregular apertures give larger values. An MLC
aperture is a staircase shape. A rounded aperture approaches `16/pi^2` =
1.62. Every open aperture gives `AI` >= 1.

## Example Result

Beam 1

![beam_1_complexity](https://user-images.githubusercontent.com/6777517/37774893-336082a8-2dc0-11e8-9c3f-6b15d8488d9f.png)

## Requirements

Python 3.12+ and [uv](https://docs.astral.sh/uv/).

- Core: `pydicom`, `numpy`, `pandas`, `scipy`
- Optional (plotting): `matplotlib`
- Dev (testing): `pytest`

## Installation

Use [uv](https://docs.astral.sh/uv/):

```bash
uv sync                    # environment + project + dependencies
uv run aperture-complexity path/to/RP.dcm
uv run pytest              # run the unit tests
```

To install the package into an existing environment, run:

```bash
uv pip install .
```

## Run the Tests

The test suite covers the aperture geometry, the leaf-pair model, and
every metric class. The tests use synthetic apertures and the bundled
sample plan. No external data is needed.

Run the tests with:

```bash
uv run pytest
```

## Contributing

Bug fixes and improvements are welcome. Before you open a pull request, run
the tests:

```bash
uv run pytest
```

## Author

Victor Gabriel Leandro Alves, D.Sc.
Copyright 2017-2018

## Acknowledgments

University of Michigan, Radiation Oncology
[https://github.com/umro/Complexity](https://github.com/umro/Complexity)
