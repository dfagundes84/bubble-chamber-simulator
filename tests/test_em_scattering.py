import math
import random

import pytest

from bcs import bethe_bloch as bb
from bcs.constants import ELECTRON_MASS_MEV
from bcs.em_scattering import compton_scatter, compton_vs_pair_probability, \
    elastic_scatter_tmax_mev, sample_elastic_knockon
from bcs.kinematics import FourVector, four_vector_from_pmag


def test_elastic_tmax_matches_bethe_bloch_formula():
    # a formula de T_max derivada via boost do CM deve bater com a ja usada
    # (e testada) na formula de Bethe-Bloch para o mesmo par feixe-alvo
    p_beam, m_p = 24000.0, 938.27208816
    beam_vec = four_vector_from_pmag(p_beam, 0.0, m_p)
    beta_gamma = p_beam / m_p
    tmax_new = elastic_scatter_tmax_mev(beam_vec, m_p, ELECTRON_MASS_MEV)
    tmax_bb = bb.max_energy_transfer_mev(beta_gamma, m_p)
    assert tmax_new == pytest.approx(tmax_bb, rel=1e-6)


@pytest.mark.parametrize("target_mass", [ELECTRON_MASS_MEV, 938.27208816])
@pytest.mark.parametrize("seed", range(10))
def test_elastic_knockon_conserves_energy_momentum_and_mass(target_mass, seed):
    rng = random.Random(seed)
    p_beam, m_p = 24000.0, 938.27208816
    beam_vec = four_vector_from_pmag(p_beam, 0.0, m_p)
    result = sample_elastic_knockon(beam_vec=beam_vec, beam_mass_mev=m_p,
                                     target_mass_mev=target_mass, t_min_mev=1.0, rng=rng)
    assert result is not None
    beam_after, target_after = result
    parent = beam_vec + FourVector(target_mass, 0.0, 0.0)
    total = beam_after + target_after

    assert total.E == pytest.approx(parent.E, rel=1e-9)
    assert total.px == pytest.approx(parent.px, abs=1e-6)
    assert total.py == pytest.approx(parent.py, abs=1e-6)
    assert beam_after.mass == pytest.approx(m_p, abs=1e-5)
    assert target_after.mass == pytest.approx(target_mass, abs=1e-5)


def test_elastic_knockon_energy_transfer_follows_inverse_square_distribution():
    # dsigma/dT ~ 1/T^2 => mediana bem proxima de T_min, media puxada para
    # cima pela cauda longa ate T_max (assinatura caracteristica dessa lei)
    rng = random.Random(0)
    p_beam, m_p = 24000.0, 938.27208816
    beam_vec = four_vector_from_pmag(p_beam, 0.0, m_p)
    t_min = 1.0
    Ts = []
    for _ in range(5000):
        beam_after, target_after = sample_elastic_knockon(
            beam_vec=beam_vec, beam_mass_mev=m_p, target_mass_mev=ELECTRON_MASS_MEV,
            t_min_mev=t_min, rng=rng)
        Ts.append(target_after.E - ELECTRON_MASS_MEV)
    Ts.sort()
    median = Ts[len(Ts) // 2]
    frac_near_min = sum(1 for t in Ts if t < 2 * t_min) / len(Ts)
    # F(2*t_min) para 1/T^2 em [t_min, t_max>>t_min] vale ~0.5
    assert 0.4 < frac_near_min < 0.6
    assert median < 5 * t_min


def test_elastic_knockon_returns_none_when_kinematically_impossible():
    m_p = 938.27208816
    # feixe de momento muito baixo: T_max cai abaixo de t_min
    beam_vec = four_vector_from_pmag(5.0, 0.0, m_p)
    result = sample_elastic_knockon(beam_vec=beam_vec, beam_mass_mev=m_p,
                                     target_mass_mev=ELECTRON_MASS_MEV, t_min_mev=50.0,
                                     rng=random.Random(0))
    assert result is None


@pytest.mark.parametrize("seed", range(20))
def test_compton_scatter_conserves_energy_momentum(seed):
    rng = random.Random(seed)
    E_gamma = rng.uniform(1.0, 500.0)
    photon_vec = FourVector(E_gamma, E_gamma, 0.0)
    photon_out, electron_out = compton_scatter(photon_vec=photon_vec, electron_mass_mev=ELECTRON_MASS_MEV, rng=rng)
    parent = photon_vec + FourVector(ELECTRON_MASS_MEV, 0.0, 0.0)
    total = photon_out + electron_out

    assert total.E == pytest.approx(parent.E, rel=1e-6)
    assert total.px == pytest.approx(parent.px, abs=1e-6)
    assert total.py == pytest.approx(parent.py, abs=1e-6)
    assert photon_out.mass == pytest.approx(0.0, abs=1e-6)
    assert electron_out.mass == pytest.approx(ELECTRON_MASS_MEV, abs=1e-6)
    assert photon_out.p <= E_gamma + 1e-9  # o foton espalhado nunca ganha energia


def test_compton_vs_pair_probability_is_zero_below_threshold_and_rises_with_energy():
    threshold = 1.022
    assert compton_vs_pair_probability(threshold * 0.9, threshold) == 0.0
    p_near = compton_vs_pair_probability(threshold * 1.5, threshold)
    p_far = compton_vs_pair_probability(threshold * 100, threshold)
    assert 0.0 < p_near < p_far < 1.0
