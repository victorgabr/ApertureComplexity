import os

from complexity.dicomrt import RTPlan
import pytest


@pytest.fixture()
def plan_dcm():
    plan_file = os.path.join(DATA_DIR, "RP_FiF.dcm")
    plan_info = RTPlan(filename=plan_file)
    return plan_info
