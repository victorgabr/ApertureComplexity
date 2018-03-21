from complexity.PyComplexityMetric import PyComplexityMetric


def test_CalculateForPlan(plan_dcm):
    plan_dict = plan_dcm.get_plan()
    complexity_metric = PyComplexityMetric().CalculateForPlan(None, plan_dict)

    cp0 = 100 * 2 / (100 ** 2)
    cp1 = 50 * 2 / (50 ** 2)
    expected = (100 * cp0 + 100 * cp1) / 200.0
    assert complexity_metric == expected
