"""Limiar e cinemática da produção de pares e+e- por um fóton real no campo
coulombiano de um núcleo, γ + N → e+ + e- + N (Seção II.B do artigo).

    (E_gamma)_min = 2 m_e c^2 (1 + m_e/M_N)          (Eq. 27)
    (E_gamma)_min --> 2 m_e c^2 = 1.022 MeV  quando M_N -> infinito (Eq. 28)
"""
from __future__ import annotations

import math
import random

from .constants import ELECTRON_MASS_MEV
from .kinematics import FourVector, energy_from_momentum, kallen_momentum, two_body_split


def threshold_energy_mev(nucleus_mass_mev: float, m_e: float = ELECTRON_MASS_MEV) -> float:
    """(E_gamma)_min = 2 m_e c^2 (1 + m_e/M_N)  -- Eq. 27 do artigo."""
    return 2.0 * m_e * (1.0 + m_e / nucleus_mass_mev)


def threshold_curve(m_min_mev: float = 200.0, m_max_mev: float = 2.0e5,
                     n_points: int = 200) -> dict:
    """(E_gamma)_min em função de M_N, para ilustrar a correção de recuo
    (Eq. 27) e sua convergência ao valor sem recuo, 2 m_e c^2 (Eq. 28)."""
    log_min, log_max = math.log10(m_min_mev), math.log10(m_max_mev)
    masses, thresholds = [], []
    for i in range(n_points):
        t = i / (n_points - 1)
        M = 10 ** (log_min + t * (log_max - log_min))
        masses.append(M)
        thresholds.append(threshold_energy_mev(M))
    return {
        "nucleus_mass_mev": masses,
        "threshold_mev": thresholds,
        "no_recoil_limit_mev": 2.0 * ELECTRON_MASS_MEV,
    }


def generate_pair_event(*, photon_energy_mev: float, nucleus_mass_mev: float,
                         rng: random.Random | None = None) -> dict | None:
    """Gera a cinemática de um evento gamma + N -> e+ + e- + N no
    referencial de laboratório (fóton ao longo de +x, núcleo em repouso).

    Retorna None se `photon_energy_mev` estiver abaixo do limiar (Eq. 27) --
    fisicamente, o par não pode ser produzido (a "lacuna" discutida na
    Seção II.B.2 do artigo).

    Método: tratamos o processo como dois splits sucessivos de dois corpos
    (mesma técnica de `kinematics.two_body_split` usada nas cascatas de
    Gagnon): primeiro γ+N -> (par e+e-, massa invariante M_par) + N'; depois
    o "sistema par" decai em e+ e e-. Isso é equivalente a amostrar o espaço
    de fase de 3 corpos por decaimentos sequenciais -- uma técnica padrão.
    """
    rng = rng or random
    m_e = ELECTRON_MASS_MEV
    E_th = threshold_energy_mev(nucleus_mass_mev, m_e)
    if photon_energy_mev < E_th:
        return None

    photon = FourVector(photon_energy_mev, photon_energy_mev, 0.0)
    target = FourVector(nucleus_mass_mev, 0.0, 0.0)
    total = photon + target
    sqrt_s = total.mass

    m_pair_max = sqrt_s - nucleus_mass_mev
    if m_pair_max <= 2 * m_e:
        return None
    # amostra a massa invariante do par com leve preferência por valores
    # baixos (mais próximos do limiar), como tipicamente ocorre no processo real
    u = rng.random() ** 2
    m_pair = 2 * m_e + u * (m_pair_max - 2 * m_e)

    theta1 = rng.uniform(-math.pi / 10, math.pi / 10)  # pequeno ângulo de recuo do núcleo
    pair_system, nucleus_out = two_body_split(total, m_pair, nucleus_mass_mev, theta1)

    theta_pair_cm = rng.uniform(0, 2 * math.pi)
    electron, positron = two_body_split(pair_system, m_e, m_e, theta_pair_cm)

    return {
        "threshold_mev": E_th,
        "sqrt_s_mev": sqrt_s,
        "pair_invariant_mass_mev": m_pair,
        "electron": {"p_mev": electron.p, "angle_rad": electron.angle, "E_mev": electron.E},
        "positron": {"p_mev": positron.p, "angle_rad": positron.angle, "E_mev": positron.E},
        "nucleus_recoil": {"p_mev": nucleus_out.p, "angle_rad": nucleus_out.angle},
    }
