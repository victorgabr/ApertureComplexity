from complexity.PyApertureMetric import PyAperturesFromBeamCreator


def test_Create(plan_dcm):
    # given 10 x 10 cm field size
    plan_dict = plan_dcm.get_plan()
    beam = plan_dict['beams'][1]
    apertures = PyAperturesFromBeamCreator().Create(beam)

    assert apertures[1].side_perimeter() == 200.0
    assert apertures[3].side_perimeter() == 100.0
    assert len(apertures) == 4
    assert apertures[0].Area() == 100 * 100
    assert apertures[2].Area() == 50 * 50
