"""Command-line interface for aperture complexity analysis.

Usage:
    aperture-complexity path_to_dicom_RP_file
    python -m complexity path_to_dicom_RP_file
"""

import sys
import time

from complexity.PyComplexityMetric import PyComplexityMetric
from complexity.dicomrt import RTPlan


def main(argv=None):
    """Compute the MU-weighted aperture complexity of a DICOM RT-PLAN file."""
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print("Usage: aperture-complexity path/to/RP.dcm")
        sys.exit(1)

    path = argv[0]
    st = time.time()
    plan_info = RTPlan(filename=path)
    plan_dict = plan_info.get_plan()
    complexity_obj = PyComplexityMetric()

    complexity_metric = complexity_obj.CalculateForPlan(None, plan_dict)
    ed = time.time()
    print("elapsed", ed - st)

    print("Reference: https://github.com/umro/Complexity")
    print("Python version by Victor Gabriel Leandro Alves, D.Sc. - victorgabr@gmail.com")
    print("Plan %s aperture complexity: %1.3f [mm-1]:" % (path, complexity_metric))


if __name__ == "__main__":
    main()
