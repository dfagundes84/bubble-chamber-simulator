"""Gerador de eventos: monta a árvore completa de colisão + decaimentos em
cascata + conversão de fótons, e converte cada ramo em geometria de
trajetória (via `track_builder.integrate_track`) pronta para o frontend.

Este módulo é o ponto de encontro dos dois artigos-referência: usa o
formalismo de quadrivetores/Mandelstam do artigo à RBEF (via
`kinematics.two_body_split`) para gerar cinematicamente cada vértice --
sejam colisões (como em Gagnon 2011) ou decaimentos --, e integra cada traço
com curvatura + perda de energia (`track_builder`), unificando na mesma
rotina numérica a Atividade 1 (MCU), a Atividade 2 (perda de energia /
espirais) e a Atividade 3 (produção de pares) do artigo.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from . import particles as particle_db
from .kinematics import (FourVector, four_vector_from_pmag, radius_from_momentum_mev,
                          rotate_momentum, two_body_split, decay_length_m as mean_decay_length_m)
from .materials import MATERIALS, DEFAULT_CHAMBER_MATERIAL, nucleus_mass_mev
from .pair_production import generate_pair_event
from .reactions import CASCADE_BY_ID
from .track_builder import integrate_track

DEFAULT_HALF_WIDTH_M = 1.00
DEFAULT_HALF_HEIGHT_M = 0.55
MAX_GENERATIONS = 7
MAX_TRACKS = 60


@dataclass
class Chamber:
    half_width_m: float = DEFAULT_HALF_WIDTH_M
    half_height_m: float = DEFAULT_HALF_HEIGHT_M


@dataclass
class _BuildState:
    rng: random.Random
    B_tesla: float
    material_key: str
    chamber: Chamber
    gamma_conversion_probability: float
    tracks: list[dict] = field(default_factory=list)
    vertices: list[dict] = field(default_factory=list)
    next_id: int = 0

    def new_id(self) -> int:
        self.next_id += 1
        return self.next_id


def _material(material_key: str):
    return MATERIALS.get(material_key, MATERIALS[DEFAULT_CHAMBER_MATERIAL])


def _decay_recursive(state: _BuildState, symbol: str, vec: FourVector,
                      pos: tuple[float, float], generation: int,
                      parent_track_id: int | None, vertex_type: str) -> None:
    if generation > MAX_GENERATIONS or len(state.tracks) > MAX_TRACKS:
        return

    part = particle_db.get(symbol)
    material = _material(state.material_key)

    if symbol == "gamma":
        _handle_photon(state, vec, pos, generation, parent_track_id, vertex_type)
        return

    # comprimento de decaimento (None = estável na escala da câmara)
    decay_len = None
    if not part.is_stable_in_chamber:
        mean_len = mean_decay_length_m(vec.p, part.mass_mev, part.mean_lifetime_s)
        if math.isfinite(mean_len):
            decay_len = state.rng.expovariate(1.0 / mean_len) if mean_len > 0 else 0.0

    seg = integrate_track(
        start_pos=pos, start_angle_rad=vec.angle, p0_mev=vec.p, mass_mev=part.mass_mev,
        charge=part.charge, B_tesla=state.B_tesla, material=material,
        chamber_half_width_m=state.chamber.half_width_m,
        chamber_half_height_m=state.chamber.half_height_m,
        decay_length_m=decay_len,
    )

    track_id = state.new_id()
    radius_start_m = (radius_from_momentum_mev(state.B_tesla, seg.p_start_mev)
                       if part.charge != 0 else None)
    state.tracks.append({
        "id": track_id, "parent_id": parent_track_id, "particle": symbol,
        "name_pt": part.name_pt, "charge": part.charge,
        "points": [[round(x, 5), round(y, 5)] for x, y in seg.points],
        "p_start_mev": round(seg.p_start_mev, 4), "p_end_mev": round(seg.p_end_mev, 4),
        "radius_start_m": round(radius_start_m, 5) if radius_start_m is not None else None,
        "is_spiral": seg.is_spiral, "visible": part.charge != 0,
        "stop_reason": seg.stop_reason, "vertex_type": vertex_type,
        "generation": generation,
    })

    if seg.stop_reason == "decayed" and not part.is_stable_in_chamber and part.decays:
        channel = _pick_channel(state.rng, part.decays)
        state.vertices.append({"x": seg.end_pos[0], "y": seg.end_pos[1], "type": "decay",
                                "label": channel.label or f"{symbol} decai"})
        if channel.daughters:
            parent_vec = four_vector_from_pmag(seg.p_end_mev, seg.end_angle_rad, part.mass_mev)
            _split_and_recurse(state, parent_vec, channel.daughters, seg.end_pos,
                                generation + 1, track_id, "decay")


def _handle_photon(state: _BuildState, vec: FourVector, pos: tuple[float, float],
                    generation: int, parent_track_id: int | None, vertex_type: str) -> None:
    material = _material(state.material_key)
    max_flight = 0.9 * (2 * state.chamber.half_width_m)
    mean_flight = 0.30 * (2 * state.chamber.half_width_m)
    flight = min(state.rng.expovariate(1.0 / mean_flight), max_flight)

    dx, dy = math.cos(vec.angle) * flight, math.sin(vec.angle) * flight
    conv_x, conv_y = pos[0] + dx, pos[1] + dy
    exited = (abs(conv_x) > state.chamber.half_width_m or abs(conv_y) > state.chamber.half_height_m)

    track_id = state.new_id()
    end_pos = (conv_x, conv_y) if not exited else (
        pos[0] + dx * 0.999, pos[1] + dy * 0.999)
    state.tracks.append({
        "id": track_id, "parent_id": parent_track_id, "particle": "gamma",
        "name_pt": "fóton", "charge": 0,
        "points": [[round(pos[0], 5), round(pos[1], 5)], [round(end_pos[0], 5), round(end_pos[1], 5)]],
        "p_start_mev": round(vec.p, 4), "p_end_mev": round(vec.p, 4),
        "radius_start_m": None, "is_spiral": False, "visible": False,
        "stop_reason": "exited_chamber" if exited else "converted",
        "vertex_type": vertex_type, "generation": generation,
    })

    if exited or state.rng.random() > state.gamma_conversion_probability:
        return

    nucleus_mev = nucleus_mass_mev(material)
    result = generate_pair_event(photon_energy_mev=vec.p, nucleus_mass_mev=nucleus_mev, rng=state.rng)
    if result is None:
        return  # abaixo do limiar (Eq. 27) -- fóton simplesmente não converte

    state.vertices.append({"x": conv_x, "y": conv_y, "type": "conversion",
                            "label": "γ → e⁺ + e⁻ (conversão no campo do núcleo)"})

    for key, symbol in (("electron", "e-"), ("positron", "e+")):
        d = result[key]
        local_vec = four_vector_from_pmag(d["p_mev"], d["angle_rad"], particle_db.get(symbol).mass_mev)
        lab_vec = rotate_momentum(local_vec, vec.angle)
        _decay_recursive(state, symbol, lab_vec, (conv_x, conv_y), generation + 1,
                          track_id, "conversion")


def _pick_channel(rng: random.Random, channels):
    # normaliza pela soma total das razoes de ramificacao modeladas, para
    # continuar correto mesmo quando canais raros foram propositalmente
    # omitidos da tabela de particulas (ver bcs/particles.py)
    total = sum(ch.branching_ratio for ch in channels)
    r = rng.random() * total
    acc = 0.0
    for ch in channels:
        acc += ch.branching_ratio
        if r <= acc:
            return ch
    return channels[-1]


def _split_and_recurse(state: _BuildState, parent_vec: FourVector, daughter_symbols,
                        pos: tuple[float, float], generation: int,
                        parent_track_id: int, vertex_type: str) -> None:
    if len(daughter_symbols) == 1:
        # decaimento com filhos invisíveis omitidos (ex.: nu) -- reatribui
        # o quadrimomento integralmente à única filha rastreável
        sym = daughter_symbols[0]
        m = particle_db.get(sym).mass_mev
        p_mag = math.sqrt(max(parent_vec.E ** 2 - m ** 2, 0.0))
        vec = four_vector_from_pmag(p_mag, parent_vec.angle, m)
        _decay_recursive(state, sym, vec, pos, generation, parent_track_id, vertex_type)
        return

    sym1, sym2 = daughter_symbols
    m1, m2 = particle_db.get(sym1).mass_mev, particle_db.get(sym2).mass_mev
    theta_cm = state.rng.uniform(0.0, 2.0 * math.pi)
    v1, v2 = two_body_split(parent_vec, m1, m2, theta_cm)
    _decay_recursive(state, sym1, v1, pos, generation, parent_track_id, vertex_type)
    _decay_recursive(state, sym2, v2, pos, generation, parent_track_id, vertex_type)


# ---------------------------------------------------------------------------
# API de alto nível
# ---------------------------------------------------------------------------

def generate_cascade_event(*, reaction_id: str, beam_momentum_gev: float, B_tesla: float,
                            material_key: str = DEFAULT_CHAMBER_MATERIAL, seed: int | None = None,
                            gamma_conversion_probability: float = 0.65,
                            n_background_tracks: int = 4,
                            chamber: Chamber | None = None) -> dict:
    if reaction_id == "random":
        reaction_id = random.Random(seed).choice(list(CASCADE_BY_ID.keys()))
    reaction = CASCADE_BY_ID[reaction_id]
    rng = random.Random(seed)
    chamber = chamber or Chamber()
    state = _BuildState(rng=rng, B_tesla=B_tesla, material_key=material_key, chamber=chamber,
                         gamma_conversion_probability=gamma_conversion_probability)

    beam_part = particle_db.get(reaction.beam)
    target_part = particle_db.get(reaction.target)
    p_beam_mev = beam_momentum_gev * 1000.0

    vertex_x = rng.uniform(-0.55, 0.05) * chamber.half_width_m
    vertex_pos = (vertex_x, 0.0)

    # traços de fundo: feixe que não interage (mesma curvatura/direção, offsets em y)
    for i in range(n_background_tracks):
        y0 = ((i - (n_background_tracks - 1) / 2.0) * 0.09) * chamber.half_height_m
        start = (-chamber.half_width_m, y0)
        vec = four_vector_from_pmag(p_beam_mev, 0.0, beam_part.mass_mev)
        _decay_recursive(state, reaction.beam, vec, start, 0, None, "beam_background")

    # colisão principal: feixe (ao longo de +x) contra alvo em repouso
    beam_vec = four_vector_from_pmag(p_beam_mev, 0.0, beam_part.mass_mev)
    target_vec = FourVector(target_part.mass_mev, 0.0, 0.0)
    total_vec = beam_vec + target_vec
    state.vertices.append({"x": vertex_pos[0], "y": vertex_pos[1], "type": "collision",
                            "label": reaction.label})

    _split_and_recurse(state, total_vec, (reaction.product1, reaction.product2),
                        vertex_pos, 1, None, "collision")

    return {
        "reaction_id": reaction_id, "reaction_label": reaction.label,
        "beam": reaction.beam, "target": reaction.target,
        "beam_momentum_gev": beam_momentum_gev, "B_tesla": B_tesla,
        "material_key": material_key,
        "chamber": {"half_width_m": chamber.half_width_m, "half_height_m": chamber.half_height_m},
        "tracks": state.tracks, "vertices": state.vertices, "seed": seed,
    }


def generate_single_track_event(*, particle_symbol: str, momentum_mev: float,
                                 angle_deg: float, B_tesla: float,
                                 material_key: str = DEFAULT_CHAMBER_MATERIAL,
                                 start_x_m: float | None = None, start_y_m: float = 0.0,
                                 seed: int | None = None,
                                 chamber: Chamber | None = None) -> dict:
    """Traço único (Atividades 1 e 2 do artigo): MCU puro em alto momento, ou
    espiral de perda de energia bem visível em baixo momento."""
    rng = random.Random(seed)
    chamber = chamber or Chamber()
    state = _BuildState(rng=rng, B_tesla=B_tesla, material_key=material_key, chamber=chamber,
                         gamma_conversion_probability=0.0)
    part = particle_db.get(particle_symbol)
    x0 = start_x_m if start_x_m is not None else -chamber.half_width_m
    vec = four_vector_from_pmag(momentum_mev, math.radians(angle_deg), part.mass_mev)
    _decay_recursive(state, particle_symbol, vec, (x0, start_y_m), 0, None, "single")
    return {
        "particle": particle_symbol, "momentum_mev": momentum_mev, "B_tesla": B_tesla,
        "material_key": material_key,
        "chamber": {"half_width_m": chamber.half_width_m, "half_height_m": chamber.half_height_m},
        "tracks": state.tracks, "vertices": state.vertices, "seed": seed,
    }


def generate_pair_production_event(*, photon_energy_mev: float, B_tesla: float,
                                    material_key: str = DEFAULT_CHAMBER_MATERIAL,
                                    seed: int | None = None,
                                    chamber: Chamber | None = None) -> dict:
    """Atividade 3 do artigo: gamma + N -> e+ + e- + N, com verificação
    explícita do limiar (Eq. 27)."""
    rng = random.Random(seed)
    chamber = chamber or Chamber()
    material = _material(material_key)
    nucleus_mev = nucleus_mass_mev(material)
    threshold = 2.0 * particle_db.get("e-").mass_mev * (1.0 + particle_db.get("e-").mass_mev / nucleus_mev)

    state = _BuildState(rng=rng, B_tesla=B_tesla, material_key=material_key, chamber=chamber,
                         gamma_conversion_probability=1.0)

    x0 = -chamber.half_width_m
    conv_x = rng.uniform(-0.5, 0.3) * chamber.half_width_m
    photon_vec = FourVector(photon_energy_mev, photon_energy_mev, 0.0)

    below_threshold = photon_energy_mev < threshold
    track_id = state.new_id()
    state.tracks.append({
        "id": track_id, "parent_id": None, "particle": "gamma", "name_pt": "fóton", "charge": 0,
        "points": [[round(x0, 5), 0.0], [round(conv_x, 5), 0.0]],
        "p_start_mev": round(photon_energy_mev, 4), "p_end_mev": round(photon_energy_mev, 4),
        "radius_start_m": None, "is_spiral": False, "visible": False,
        "stop_reason": "below_threshold" if below_threshold else "converted",
        "vertex_type": "single", "generation": 0,
    })

    if below_threshold:
        return {
            "photon_energy_mev": photon_energy_mev, "threshold_mev": threshold,
            "below_threshold": True, "nucleus_mass_mev": nucleus_mev,
            "B_tesla": B_tesla, "material_key": material_key,
            "chamber": {"half_width_m": chamber.half_width_m, "half_height_m": chamber.half_height_m},
            "tracks": state.tracks, "vertices": [], "seed": seed,
        }

    result = generate_pair_event(photon_energy_mev=photon_energy_mev, nucleus_mass_mev=nucleus_mev, rng=rng)
    state.vertices.append({"x": conv_x, "y": 0.0, "type": "conversion",
                            "label": "γ → e⁺ + e⁻ (conversão no campo do núcleo)"})
    for key, symbol in (("electron", "e-"), ("positron", "e+")):
        d = result[key]
        vec = four_vector_from_pmag(d["p_mev"], d["angle_rad"], particle_db.get(symbol).mass_mev)
        _decay_recursive(state, symbol, vec, (conv_x, 0.0), 1, track_id, "conversion")

    return {
        "photon_energy_mev": photon_energy_mev, "threshold_mev": threshold,
        "below_threshold": False, "nucleus_mass_mev": nucleus_mev,
        "pair_invariant_mass_mev": result["pair_invariant_mass_mev"],
        "B_tesla": B_tesla, "material_key": material_key,
        "chamber": {"half_width_m": chamber.half_width_m, "half_height_m": chamber.half_height_m},
        "tracks": state.tracks, "vertices": state.vertices, "seed": seed,
    }
