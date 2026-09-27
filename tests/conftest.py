import os

import pytest

from complexity.dicomrt import RTPlan

DATA_DIR = os.path.join(os.path.dirname(__file__), "tests_data")


@pytest.fixture()
def plan_dcm():
    plan_file = os.path.join(DATA_DIR, "RP_FiF.dcm")
    plan_info = RTPlan(filename=plan_file)
    return plan_info
