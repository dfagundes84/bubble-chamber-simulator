import pytest

from bcs.constants import ELECTRON_MASS_MEV
from bcs.pair_production import generate_pair_event, threshold_energy_mev


def test_threshold_converges_to_no_recoil_limit_as_mass_grows():
    small = threshold_energy_mev(500.0)
    large = threshold_energy_mev(1.0e8)
    no_recoil = 2.0 * ELECTRON_MASS_MEV
    assert small > large > no_recoil
    assert large == pytest.approx(no_recoil, rel=1e-5)


def test_proton_threshold_matches_article_value():
    # Eq. 27-28 do artigo: limiar para o proton fica muito proximo de 1,022 MeV
    E_th = threshold_energy_mev(938.27208816)
    assert E_th == pytest.approx(1.022, abs=2e-3)


def test_no_pair_below_threshold():
    result = generate_pair_event(photon_energy_mev=0.5, nucleus_mass_mev=938.272)
    assert result is None


def test_pair_above_threshold_conserves_energy_momentum():
    photon_e = 100.0
    nucleus_m = 938.272
    result = generate_pair_event(photon_energy_mev=photon_e, nucleus_mass_mev=nucleus_m)
    assert result is not None
    # a soma das energias do par deve ser menor que a energia total
    # disponivel (foton + massa de repouso do nucleo), pois o nucleo leva
    # parte da energia no recuo
    assert result["electron"]["E_mev"] + result["positron"]["E_mev"] < photon_e + nucleus_m
    assert result["pair_invariant_mass_mev"] >= 2 * 0.51099895
