import math
import random

import pytest

from bcs.kinematics import (four_vector_from_pmag, kallen_momentum, momentum_perp_gev,
                             radius_from_momentum_gev, two_body_split)


def test_p_perp_matches_eq17():
    # p[GeV/c] = 0,3 * B[T] * R[m]  (Eq. 17 do artigo)
    p = momentum_perp_gev(B_tesla=1.7, radius_m=0.055)
    assert p == pytest.approx(0.3 * 1.7 * 0.055, rel=2e-3)


def test_radius_roundtrip():
    R = radius_from_momentum_gev(B_tesla=1.7, p_gev=24.0)
    p_back = momentum_perp_gev(B_tesla=1.7, radius_m=R)
    assert p_back == pytest.approx(24.0, rel=1e-9)


def test_kallen_momentum_two_equal_masses():
    # M -> m + m: p* = sqrt(M^2/4 - m^2)
    M, m = 1115.683, 500.0
    p_star = kallen_momentum(M, m, m)
    assert p_star == pytest.approx(math.sqrt((M / 2) ** 2 - m ** 2), rel=1e-9)


def test_kallen_momentum_forbidden_channel_is_zero():
    assert kallen_momentum(1.0, 10.0, 10.0) == 0.0


@pytest.mark.parametrize("seed", range(20))
def test_two_body_split_conserves_energy_momentum_and_mass(seed):
    rng = random.Random(seed)
    p_parent = rng.uniform(0, 30000)
    M = rng.uniform(300, 3000)
    m1 = rng.uniform(0.5, M / 2 - 1)
    m2 = rng.uniform(0.5, M / 2 - 1)
    parent = four_vector_from_pmag(p_parent, rng.uniform(0, 2 * math.pi), M)
    theta = rng.uniform(0, 2 * math.pi)

    d1, d2 = two_body_split(parent, m1, m2, theta)
    total = d1 + d2

    assert total.E == pytest.approx(parent.E, abs=1e-6, rel=1e-9)
    assert total.px == pytest.approx(parent.px, abs=1e-6, rel=1e-9)
    assert total.py == pytest.approx(parent.py, abs=1e-6, rel=1e-9)
    assert d1.mass == pytest.approx(m1, abs=1e-5)
    assert d2.mass == pytest.approx(m2, abs=1e-5)
