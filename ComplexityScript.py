import os
import sys
import time

from complexity import misc

from complexity.PyComplexityMetric import PyComplexityMetric
from complexity.dicomrt import RTPlan



filename = r"C:\Users\vl8fn\Downloads\RP_LUL_SBRT.dcm"
st = time.time()
plan_info = RTPlan(filename=filename)
plan_dict = plan_info.get_plan()
beams = [beam for k, beam in plan_dict["beams"].items()]
complexity_obj = PyComplexityMetric()
modIndex = misc.ModulationIndexScore().CalculateForPlan(None, plan_dict)

print(f'Modulation Index Score: {modIndex}')

# complexity_metric = complexity_obj.CalculateForPlan(None, plan_dict)
# ed = time.time()
# print("elapsed", ed - st)
#
# _, plan_file = os.path.split(sys.argv[1])
#
# print("Reference: https://github.com/umro/Complexity")
# print("Python version by Victor Gabriel Leandro Alves, D.Sc. - victorgabr@gmail.com")
# print("Plan %s aperture complexity: %1.3f [mm-1]: " % (sys.argv[1], complexity_metric))