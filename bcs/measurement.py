"""Ferramenta de medição: ajuste de círculo a pontos clicados sobre um
traço, replicando a régua/compasso virtual do simulador de Gagnon (2011) —
"a virtual tool is built in to facilitate the measurement of the radius of
curvature of trajectories" — mas aqui devolvendo também o momento via
p[GeV/c] = 0.3 * B[T] * R[m] (Eq. 17 do artigo), para as Atividades 2 e 3.
"""
from __future__ import annotations

import math

from .kinematics import momentum_perp_gev


def fit_circle_kasa(points: list[tuple[float, float]]) -> tuple[float, float, float]:
    """Ajuste algébrico de círculo (método de Kása) a >= 3 pontos (x, y).

    Retorna (cx, cy, R). É o método padrão para estimar rapidamente o raio
    de curvatura a partir de poucos pontos marcados manualmente sobre uma
    fotografia -- rápido e não-iterativo, adequado ao uso interativo.
    """
    n = len(points)
    if n < 3:
        raise ValueError("São necessários pelo menos 3 pontos para ajustar um círculo.")

    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    mean_x, mean_y = sum_x / n, sum_y / n

    u = [p[0] - mean_x for p in points]
    v = [p[1] - mean_y for p in points]

    Suu = sum(ui * ui for ui in u)
    Svv = sum(vi * vi for vi in v)
    Suv = sum(ui * vi for ui, vi in zip(u, v))
    Suuu = sum(ui ** 3 for ui in u)
    Svvv = sum(vi ** 3 for vi in v)
    Suvv = sum(ui * vi * vi for ui, vi in zip(u, v))
    Svuu = sum(vi * ui * ui for ui, vi in zip(u, v))

    A = [[Suu, Suv], [Suv, Svv]]
    b = [0.5 * (Suuu + Suvv), 0.5 * (Svvv + Svuu)]
    det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
    if abs(det) < 1e-12:
        # pontos quase colineares -- raio muito grande (traço quase reto)
        return (math.inf, math.inf, math.inf)

    uc = (b[0] * A[1][1] - b[1] * A[0][1]) / det
    vc = (A[0][0] * b[1] - A[1][0] * b[0]) / det

    cx, cy = uc + mean_x, vc + mean_y
    R = math.sqrt(uc ** 2 + vc ** 2 + (Suu + Svv) / n)
    return (cx, cy, R)


def estimate_curvature_sign(points: list[tuple[float, float]]) -> int:
    """Sinal da curvatura ao longo da sequência de pontos (+1 = horário,
    -1 = anti-horário), usado para inferir o sinal da carga elétrica a
    partir da orientação do campo (ver Seção II.A.3 do artigo)."""
    if len(points) < 3:
        return 0
    cross_sum = 0.0
    for i in range(1, len(points) - 1):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        v1 = (x1 - x0, y1 - y0)
        v2 = (x2 - x1, y2 - y1)
        cross_sum += v1[0] * v2[1] - v1[1] * v2[0]
    if cross_sum == 0:
        return 0
    return -1 if cross_sum > 0 else 1  # convenção consistente com track_builder


def measure(points: list[tuple[float, float]], B_tesla: float) -> dict:
    cx, cy, R = fit_circle_kasa(points)
    if not math.isfinite(R):
        return {"radius_m": None, "momentum_gev": None, "momentum_mev": None,
                "center": None, "curvature_sign": 0}
    p_gev = momentum_perp_gev(B_tesla, R)
    sign = estimate_curvature_sign(points)
    return {
        "radius_m": R, "momentum_gev": p_gev, "momentum_mev": p_gev * 1000.0,
        "center": {"x": cx, "y": cy}, "curvature_sign": sign,
    }
