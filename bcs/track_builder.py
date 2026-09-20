"""Integração de trajetórias na câmara: movimento circular num campo B
uniforme (Seção II.A do artigo) acoplado, passo a passo, à perda de momento
por ionização (Bethe-Bloch, Seção II.C) — é exatamente esse acoplamento que
faz uma trajetória inicialmente circular "degenerar numa espiral de raio
decrescente até o traço colapsar" (conforme discutido no artigo).

Convenção geométrica: campo magnético sempre para fora do plano da imagem
(+z, como em todas as figuras do artigo e do Gagnon 2011). Com essa
convenção, F = q*v×B faz partículas de carga positiva curvarem no sentido
horário (dtheta/ds < 0) e partículas de carga negativa no sentido
anti-horário (dtheta/ds > 0).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .bethe_bloch import linear_stopping_power_mev_per_cm
from .kinematics import energy_from_momentum, radius_from_momentum_mev
from .materials import Material

MEV_PER_CM_TO_MEV_PER_M = 100.0
MIN_VISIBLE_RADIUS_M = 0.0015   # abaixo disso, consideramos o traço "colapsado"
MIN_MOMENTUM_MEV = 0.5
MAX_POINTS_PER_TRACK = 480      # suficiente para ~2 voltas de uma espiral bem amostrada
MAX_ITERATIONS = 20_000         # cinto de segurança (nunca deveria ser atingido; ver comentário abaixo)
ANGLE_RESOLUTION_RAD = 0.025    # densidade de amostragem da polilinha


@dataclass
class TrackSegment:
    points: list[tuple[float, float]] = field(default_factory=list)
    p_start_mev: float = 0.0
    p_end_mev: float = 0.0
    end_pos: tuple[float, float] = (0.0, 0.0)
    end_angle_rad: float = 0.0
    path_length_m: float = 0.0
    stop_reason: str = "max_steps"   # exited_chamber | decayed | ranged_out | max_steps
    is_spiral: bool = False          # True se a curvatura variou visivelmente (perda de energia relevante)


def integrate_track(*, start_pos: tuple[float, float], start_angle_rad: float,
                     p0_mev: float, mass_mev: float, charge: int,
                     B_tesla: float, material: Material,
                     chamber_half_width_m: float, chamber_half_height_m: float,
                     decay_length_m: float | None = None,
                     step_length_m: float = 0.004) -> TrackSegment:
    """Integra uma trajetória carregada passo a passo.

    Partículas neutras (charge == 0) seguem reta e não perdem energia
    (fótons, nêutrons e neutrinos não ionizam o meio -- Gagnon 2011).
    """
    x, y = start_pos
    theta = start_angle_rad
    p = p0_mev
    path_length = 0.0
    points = [(x, y)]
    last_stored_theta = theta
    stop_reason = "max_steps"
    max_r_seen = 0.0
    min_r_seen = math.inf

    if charge == 0:
        # trajetória reta; percorre até sair da câmara ou atingir o comprimento de decaimento
        max_len = decay_length_m if decay_length_m is not None else 10.0
        dx, dy = math.cos(theta), math.sin(theta)
        n_steps = max(2, int(min(max_len, 10.0) / step_length_m))
        for _ in range(n_steps):
            x_new, y_new = x + dx * step_length_m, y + dy * step_length_m
            path_length += step_length_m
            if abs(x_new) > chamber_half_width_m or abs(y_new) > chamber_half_height_m:
                stop_reason = "exited_chamber"
                break
            x, y = x_new, y_new
            if decay_length_m is not None and path_length >= decay_length_m:
                stop_reason = "decayed"
                break
        else:
            stop_reason = "decayed" if decay_length_m is not None else "exited_chamber"
        points.append((x, y))
        return TrackSegment(points=points, p_start_mev=p0_mev, p_end_mev=p0_mev,
                             end_pos=(x, y), end_angle_rad=theta,
                             path_length_m=path_length, stop_reason=stop_reason,
                             is_spiral=False)

    # Cota de iterações: na prática o laço sempre termina bem antes disso,
    # pois um ponto é gravado a cada ANGLE_RESOLUTION_RAD de rotação (ou, no
    # mínimo, a cada 40 passos) -- então MAX_POINTS_PER_TRACK já limita o
    # número de iterações a poucos milhares mesmo numa espiral bem fechada
    # com perda de energia muito lenta (ex. gás de baixa densidade). Este
    # `MAX_ITERATIONS` é só uma defesa extra contra combinações não previstas
    # de parâmetros.
    n_steps = 0
    while n_steps < MAX_ITERATIONS:
        n_steps += 1
        beta_gamma = p / mass_mev
        radius_m = radius_from_momentum_mev(B_tesla, p)
        max_r_seen = max(max_r_seen, radius_m)
        min_r_seen = min(min_r_seen, radius_m)

        if radius_m < MIN_VISIBLE_RADIUS_M or p < MIN_MOMENTUM_MEV:
            stop_reason = "ranged_out"
            break

        ds = min(step_length_m, max(radius_m * ANGLE_RESOLUTION_RAD, 1e-4))
        dtheta = -charge * (ds / radius_m)

        # ponto médio do arco (integração tipo midpoint, mais estável para R pequeno)
        theta_mid = theta + dtheta / 2.0
        x_new = x + ds * math.cos(theta_mid)
        y_new = y + ds * math.sin(theta_mid)
        theta_new = theta + dtheta

        path_length_new = path_length + ds

        if abs(x_new) > chamber_half_width_m or abs(y_new) > chamber_half_height_m:
            stop_reason = "exited_chamber"
            break

        # perda de energia por ionização ao longo do passo ds (Bethe-Bloch)
        dedx_mev_per_m = linear_stopping_power_mev_per_cm(beta_gamma, mass_mev, material) * MEV_PER_CM_TO_MEV_PER_M
        E = energy_from_momentum(p, mass_mev)
        E_new = max(E - dedx_mev_per_m * ds, mass_mev * 1.0001)
        p_new = math.sqrt(max(E_new * E_new - mass_mev * mass_mev, 0.0))

        x, y, theta, p, path_length = x_new, y_new, theta_new, p_new, path_length_new

        if abs(theta - last_stored_theta) >= ANGLE_RESOLUTION_RAD or n_steps % 40 == 0:
            points.append((x, y))
            last_stored_theta = theta
            if len(points) >= MAX_POINTS_PER_TRACK:
                stop_reason = "max_steps"
                break

        if decay_length_m is not None and path_length >= decay_length_m:
            stop_reason = "decayed"
            break
    else:
        stop_reason = "max_steps"

    if points[-1] != (x, y):
        points.append((x, y))

    is_spiral = (max_r_seen > 0) and ((max_r_seen - min_r_seen) / max_r_seen > 0.03)

    return TrackSegment(points=points, p_start_mev=p0_mev, p_end_mev=p,
                         end_pos=(x, y), end_angle_rad=theta,
                         path_length_m=path_length, stop_reason=stop_reason,
                         is_spiral=is_spiral)
