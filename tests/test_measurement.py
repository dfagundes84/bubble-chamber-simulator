import math

import pytest

from bcs.measurement import fit_circle_kasa, measure


def _points_on_circle(cx, cy, R, angles):
    return [(cx + R * math.cos(a), cy + R * math.sin(a)) for a in angles]


def test_fit_circle_recovers_known_circle():
    cx, cy, R = 0.1, -0.05, 0.22
    pts = _points_on_circle(cx, cy, R, [0.1, 1.0, 2.3, 3.4])
    fx, fy, fR = fit_circle_kasa(pts)
    assert fx == pytest.approx(cx, abs=1e-6)
    assert fy == pytest.approx(cy, abs=1e-6)
    assert fR == pytest.approx(R, abs=1e-6)


def test_measure_recovers_momentum_via_eq17():
    B = 1.7
    R = 0.3
    pts = _points_on_circle(0.0, R, R, [0.2, 1.5, 2.8])  # circulo passando pela origem
    result = measure(pts, B)
    assert result["radius_m"] == pytest.approx(R, rel=1e-4)
    assert result["momentum_gev"] == pytest.approx(0.3 * B * R, rel=1e-3)


def test_measure_with_too_few_points_raises():
    with pytest.raises(ValueError):
        fit_circle_kasa([(0, 0), (1, 1)])
