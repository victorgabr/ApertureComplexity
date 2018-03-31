import os
import sys
import time

from complexity.PyComplexityMetric import PyComplexityMetric
from complexity.dicomrt import RTPlan

if len(sys.argv) != 2:
    print("Usage: %s path to DICOM RT-PLAN file *.dcm" % (sys.argv[0]))
    sys.exit(1)

st = time.time()
plan_info = RTPlan(filename=sys.argv[1])
plan_dict = plan_info.get_plan()
beams = [beam for k, beam in plan_dict['beams'].items()]
complexity_obj = PyComplexityMetric()

complexity_metric = complexity_obj.CalculateForPlan(None, plan_dict)
ed = time.time()
print('elapsed', ed - st)

_, plan_file = os.path.split(sys.argv[1])

print("Reference: https://github.com/umro/Complexity")
print("Python version by Victor Gabriel Leandro Alves, D.Sc. - victorgabr@gmail.com")
print("Plan %s aperture complexity: %1.3f [mm-1]: " % (sys.argv[1], complexity_metric))
