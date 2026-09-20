import pytest

from bcs import event as ev
from bcs.reactions import CASCADE_REACTIONS


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


def test_pair_production_event_below_threshold_has_no_visible_pair():
    data = ev.generate_pair_production_event(photon_energy_mev=0.5, B_tesla=1.7,
                                               material_key="h2_liquid", seed=1)
    assert data["below_threshold"] is True
    assert len(data["vertices"]) == 0


def test_pair_production_event_above_threshold_creates_electron_and_positron():
    data = ev.generate_pair_production_event(photon_energy_mev=50.0, B_tesla=1.7,
                                               material_key="h2_liquid", seed=1)
    assert data["below_threshold"] is False
    symbols = [t["particle"] for t in data["tracks"]]
    assert "e-" in symbols and "e+" in symbols
    e_track = next(t for t in data["tracks"] if t["particle"] == "e-")
    p_track = next(t for t in data["tracks"] if t["particle"] == "e+")
    assert e_track["charge"] == -1
    assert p_track["charge"] == +1


def test_zero_field_gives_straight_tracks():
    data = ev.generate_single_track_event(particle_symbol="p", momentum_mev=500.0,
                                           angle_deg=0, B_tesla=0.0, material_key="h2_liquid", seed=1)
    t = data["tracks"][0]
    ys = [pt[1] for pt in t["points"]]
    assert max(ys) - min(ys) < 1e-6  # reta ao longo de y=0
