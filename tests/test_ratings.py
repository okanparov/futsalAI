import numpy as np

from src.rating_system import RatingSystem, normalize_distance
from src.stats_calculator import StatsCalculator


def test_rating_bounds_and_missing_components():
    r = RatingSystem()
    assert r.calculate({"positioning": 1.0, "physical": 1.0}) == 99
    assert r.calculate({"positioning": 0.0}) == 0
    assert r.calculate({}) is None
    # eksik bilesenler atlanir: sadece positioning varsa agirlik yeniden normalize edilir
    assert r.calculate({"positioning": 0.5}, "defans") == r.calculate({"positioning": 0.5, "pass_accuracy": None}, "defans")


def test_position_weights_differ():
    r = RatingSystem()
    comp = {"shots_on_target": 1.0, "positioning": 0.0}
    assert r.calculate(comp, "forvard") > r.calculate(comp, "defans") or r.calculate(comp, "defans") == 0


def test_distance_and_jump_filter():
    s = StatsCalculator((400, 200), (40.0, 20.0))  # 10 px = 1 m
    for i in range(5):  # 1 m / 0.5 s = 2 m/s
        s.add_frame(i * 0.5, np.array([[i * 10 - 2, 0, i * 10 + 2, 100, 1, .9]]))
    assert abs(s.distance(1) - 4.0) < 1e-6
    s.add_frame(2.6, np.array([[398, 0, 398, 100, 1, .9]]))  # sicrama: atlanmali
    assert abs(s.distance(1) - 4.0) < 1e-6
    assert normalize_distance(6000) == 1.0
