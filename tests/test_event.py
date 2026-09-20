import math

import pytest

from bcs import event as ev
from bcs import particles as pdb
from bcs.reactions import CASCADE_REACTIONS, CASCADE_BY_ID


@pytest.mark.parametrize("reaction", CASCADE_REACTIONS, ids=lambda r: r.id)
def test_cascade_event_generates_tracks_and_conserves_charge_at_collision(reaction):
    data = ev.generate_cascade_event(reaction_id=reaction.id, beam_momentum_gev=24.0,
                                      B_tesla=1.7, material_key="h2_liquid", seed=123)
    assert len(data["tracks"]) > 0
    assert any(v["type"] == "collision" for v in data["vertices"])
    # todo traco deve ter pelo menos 2 pontos
    for t in data["tracks"]:
        assert len(t["points"]) >= 2


def test_single_track_high_momentum_is_nearly_circular_not_flagged_spiral():
    data = ev.generate_single_track_event(particle_symbol="p", momentum_mev=24000.0,
                                           angle_deg=0, B_tesla=1.7, material_key="h2_liquid", seed=1)
    t = data["tracks"][0]
    assert t["is_spiral"] is False
    # perda de momento desprezivel numa unica travessia da camara
    assert t["p_end_mev"] == pytest.approx(t["p_start_mev"], rel=0.02)


def test_single_track_low_momentum_electron_spirals_and_loses_significant_momentum():
    data = ev.generate_single_track_event(particle_symbol="e-", momentum_mev=15.0,
                                           angle_deg=0, B_tesla=1.7, material_key="h2_liquid", seed=1)
    t = data["tracks"][0]
    assert t["is_spiral"] is True
    assert t["p_end_mev"] < 0.9 * t["p_start_mev"]


def test_photon_event_below_threshold_compton_scatters_instead_of_nothing():
    data = ev.generate_photon_interaction_event(photon_energy_mev=0.5, B_tesla=1.7,
                                                  material_key="h2_liquid", seed=1)
    assert data["below_threshold"] is True
    assert data["process"] == "compton"
    assert any(v["type"] == "compton" for v in data["vertices"])
    symbols = [t["particle"] for t in data["tracks"]]
    assert "e-" in symbols and "e+" not in symbols
    assert data["compton_electron_energy_mev"] > 0


def test_photon_event_above_threshold_creates_electron_and_positron():
    data = ev.generate_photon_interaction_event(photon_energy_mev=50.0, B_tesla=1.7,
                                                  material_key="h2_liquid", seed=1)
    assert data["below_threshold"] is False
    assert data["process"] == "pair"
    symbols = [t["particle"] for t in data["tracks"]]
    assert "e-" in symbols and "e+" in symbols
    e_track = next(t for t in data["tracks"] if t["particle"] == "e-")
    p_track = next(t for t in data["tracks"] if t["particle"] == "e+")
    assert e_track["charge"] == -1
    assert p_track["charge"] == +1


@pytest.mark.parametrize("seed", range(15))
def test_omega_discovery_reaction_produces_omega_track(seed):
    # feixe bem acima do limiar (~3.2 GeV/c) de K- + p -> Omega- + K+ + K0
    data = ev.generate_cascade_event(reaction_id="k_omega_discovery", beam_momentum_gev=24.0,
                                      B_tesla=1.7, material_key="h2_liquid", seed=seed,
                                      n_background_tracks=0)
    symbols = [t["particle"] for t in data["tracks"] if t["generation"] == 1]
    assert "Omega-" in symbols, f"seed={seed}: Omega- ausente entre os produtos da colisao"


def _initial_four_vector(track):
    """Reconstrói o quadrivetor de um traço no início (antes de qualquer
    perda de energia), a partir de p_start_mev, da massa da partícula e da
    direção inicial (dada pelos dois primeiros pontos do traço)."""
    mass = pdb.get(track["particle"]).mass_mev
    p = track["p_start_mev"]
    E = math.sqrt(p * p + mass * mass)
    (x0, y0), (x1, y1) = track["points"][0], track["points"][1]
    angle = math.atan2(y1 - y0, x1 - x0)
    return E, p * math.cos(angle), p * math.sin(angle)


def test_omega_discovery_conserves_energy_momentum_at_collision():
    reaction = CASCADE_BY_ID["k_omega_discovery"]
    beam_momentum_gev = 24.0
    data = ev.generate_cascade_event(reaction_id="k_omega_discovery", beam_momentum_gev=beam_momentum_gev,
                                      B_tesla=1.7, material_key="h2_liquid", seed=7,
                                      n_background_tracks=0)

    gen1_tracks = [t for t in data["tracks"] if t["generation"] == 1]
    assert {t["particle"] for t in gen1_tracks} == set(reaction.products)

    E_sum = px_sum = py_sum = 0.0
    for t in gen1_tracks:
        E, px, py = _initial_four_vector(t)
        E_sum += E; px_sum += px; py_sum += py

    beam = pdb.get(reaction.beam)
    target = pdb.get(reaction.target)
    p_beam_mev = beam_momentum_gev * 1000.0
    E_beam = math.sqrt(p_beam_mev ** 2 + beam.mass_mev ** 2)
    E_total = E_beam + target.mass_mev

    # tolerância folgada (erro observado empiricamente < 0,2%): a direção
    # inicial de cada traço é reconstruída a partir dos dois primeiros
    # pontos armazenados da polilinha (não do ângulo exato passado ao
    # integrador), o que introduz um pequeno erro de discretização
    # (~ANGLE_RESOLUTION_RAD/2, ver track_builder.py)
    assert E_sum == pytest.approx(E_total, rel=0.01)
    assert px_sum == pytest.approx(p_beam_mev, rel=0.01)
    assert py_sum == pytest.approx(0.0, abs=0.01 * p_beam_mev)


def test_single_track_forced_scattering_produces_scatter_vertex_and_recoil():
    data = ev.generate_single_track_event(particle_symbol="p", momentum_mev=24000.0,
                                           angle_deg=0, B_tesla=1.7, material_key="h2_liquid",
                                           seed=1, allow_scattering=True, scatter_probability=1.0)
    assert any(v["type"] == "scatter" for v in data["vertices"])
    gen1 = [t for t in data["tracks"] if t["generation"] == 1]
    assert len(gen1) == 2
    symbols = {t["particle"] for t in gen1}
    assert symbols == {"p", "e-"} or symbols == {"p", "p"}


def test_single_track_no_scattering_by_default():
    data = ev.generate_single_track_event(particle_symbol="p", momentum_mev=24000.0,
                                           angle_deg=0, B_tesla=1.7, material_key="h2_liquid", seed=1)
    assert data["vertices"] == []
    assert len(data["tracks"]) == 1


@pytest.mark.parametrize("seed", range(10))
def test_beam_scattering_conserves_energy_momentum(seed):
    p_beam_mev = 24000.0
    data = ev.generate_single_track_event(particle_symbol="p", momentum_mev=p_beam_mev,
                                           angle_deg=0, B_tesla=1.7, material_key="h2_liquid",
                                           seed=seed, allow_scattering=True, scatter_probability=1.0)
    scatter_track = data["tracks"][0]  # traço do feixe ate o ponto de espalhamento
    gen1 = [t for t in data["tracks"] if t["generation"] == 1]

    m_p = pdb.get("p").mass_mev
    E_before = math.sqrt(scatter_track["p_end_mev"] ** 2 + m_p ** 2)
    m_target = pdb.get(gen1[1]["particle"] if gen1[0]["particle"] == "p" else gen1[0]["particle"]).mass_mev
    E_target_before = m_target  # alvo em repouso
    E_total_before = E_before + E_target_before

    E_sum = px_sum = py_sum = 0.0
    for t in gen1:
        E, px, py = _initial_four_vector(t)
        E_sum += E; px_sum += px; py_sum += py

    assert E_sum == pytest.approx(E_total_before, rel=0.02)
    assert px_sum == pytest.approx(scatter_track["p_end_mev"], rel=0.02)


def test_cascade_beam_scattering_can_be_disabled():
    data = ev.generate_cascade_event(reaction_id="k_xi_minus_kplus", beam_momentum_gev=24.0,
                                      B_tesla=1.7, material_key="h2_liquid", seed=1,
                                      beam_scatter_probability=0.0)
    assert not any(v["type"] == "scatter" for v in data["vertices"])


def test_zero_field_gives_straight_tracks():
    data = ev.generate_single_track_event(particle_symbol="p", momentum_mev=500.0,
                                           angle_deg=0, B_tesla=0.0, material_key="h2_liquid", seed=1)
    t = data["tracks"][0]
    ys = [pt[1] for pt in t["points"]]
    assert max(ys) - min(ys) < 1e-6  # reta ao longo de y=0
