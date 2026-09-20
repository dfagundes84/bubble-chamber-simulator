"""Perda de energia por ionização — Fórmula de Bethe-Bloch (Eq. 29 do artigo
à RBEF, referência [19,28,29]).

    <-dE/dx> = K z^2 (Z/A) (1/beta^2) [ (1/2) ln(2 m_e c^2 beta^2 gamma^2 Tmax / I^2)
                                          - beta^2 - delta(beta*gamma)/2 ]

em MeV cm^2/g (poder de freamento mássico, o mesmo plotado na Figura 3 do
artigo). O termo de correção de densidade delta(beta*gamma) é estimado pela
aproximação geral de Sternheimer-Peierls a partir de I, Z, A e rho do meio
--- um método padrão (ver Leo, "Techniques for Nuclear and Particle Physics
Experiments", ref. [30] do artigo) usado quando não se dispõe dos parâmetros
tabelados especificamente ajustados por elemento. Isso é adequado para fins
didáticos, mas não tem a precisão de metrologia de uma tabela oficial do PDG.
"""
from __future__ import annotations

import math

from .constants import ELECTRON_MASS_MEV
from .materials import Material

K_BETHE = 0.307075  # MeV cm^2 / mol  (=4*pi*N_A*r_e^2*m_e*c^2)
LN10 = math.log(10.0)


def beta_gamma_to_beta_gamma_factors(beta_gamma: float) -> tuple[float, float]:
    gamma = math.sqrt(1.0 + beta_gamma * beta_gamma)
    beta = beta_gamma / gamma
    return beta, gamma


def sternheimer_delta(beta_gamma: float, material: Material) -> float:
    """Correção de densidade delta(beta*gamma), aproximação de
    Sternheimer-Peierls (parâmetros derivados de I, Z, A, rho — não
    tabelados por elemento)."""
    if beta_gamma <= 0:
        return 0.0
    X = math.log10(beta_gamma)

    hwp_eV = 28.816 * math.sqrt(material.rho_gcm3 * material.Z / material.A)
    if hwp_eV <= 0:
        return 0.0
    Cbar = 2.0 * math.log(material.I_eV / hwp_eV) + 1.0

    if material.conductor:
        X0 = 0.2 if Cbar < 5.215 else 0.326 * Cbar - 1.5
        X1 = 3.0
    else:
        X0 = 0.2 if Cbar < 3.681 else 0.326 * Cbar - 1.0
        X1 = 2.0

    m_exp = 3.0
    denom = (X1 - X0) ** m_exp
    a = (Cbar - 2.0 * LN10 * X0) / denom if denom > 0 else 0.0

    if X < X0:
        return 0.0
    if X < X1:
        return 2.0 * LN10 * X - Cbar + a * (X1 - X) ** m_exp
    return 2.0 * LN10 * X - Cbar


def max_energy_transfer_mev(beta_gamma: float, M_mev: float) -> float:
    """T_max: energia máxima transferível a um elétron livre numa única
    colisão (fórmula relativística completa, considerando a massa M do
    projétil)."""
    beta, gamma = beta_gamma_to_beta_gamma_factors(beta_gamma)
    me = ELECTRON_MASS_MEV
    num = 2.0 * me * beta_gamma * beta_gamma
    den = 1.0 + 2.0 * gamma * me / M_mev + (me / M_mev) ** 2
    return num / den


def mass_stopping_power(beta_gamma: float, M_mev: float, material: Material,
                         z: int = 1) -> float:
    """<-dE/dx> em MeV cm^2/g (independe da densidade -- é o que a Figura 3
    do artigo mostra no eixo y)."""
    if beta_gamma <= 1e-6:
        return 0.0
    beta, gamma = beta_gamma_to_beta_gamma_factors(beta_gamma)
    me = ELECTRON_MASS_MEV
    Tmax = max_energy_transfer_mev(beta_gamma, M_mev)
    I_mev = material.I_eV * 1e-6
    delta = sternheimer_delta(beta_gamma, material)

    log_arg = 2.0 * me * beta_gamma * beta_gamma * Tmax / (I_mev * I_mev)
    if log_arg <= 0:
        return 0.0
    bracket = 0.5 * math.log(log_arg) - beta * beta - delta / 2.0
    bracket = max(bracket, 0.0)  # evita divergência não-física abaixo do limiar de Cherenkov/ionização

    return K_BETHE * (z ** 2) * (material.Z / material.A) / (beta * beta) * bracket


def linear_stopping_power_mev_per_cm(beta_gamma: float, M_mev: float,
                                      material: Material, z: int = 1) -> float:
    """<-dE/dx> em MeV/cm (poder de freamento físico, = poder mássico * rho)."""
    return mass_stopping_power(beta_gamma, M_mev, material, z) * material.rho_gcm3


def dedx_curve(material: Material, beta_gamma_min: float = 0.1,
               beta_gamma_max: float = 1.0e4, n_points: int = 200,
               M_mev: float = 938.27208816) -> dict:
    """Reproduz a Figura 3 do artigo: <-dE/dx> vs beta*gamma, em escala
    log-log, para um meio arbitrário (a curva é universal em beta*gamma,
    válida para qualquer partícula carregada pesada — Seção II.C)."""
    log_min, log_max = math.log10(beta_gamma_min), math.log10(beta_gamma_max)
    xs, ys = [], []
    for i in range(n_points):
        t = i / (n_points - 1)
        bg = 10 ** (log_min + t * (log_max - log_min))
        xs.append(bg)
        ys.append(mass_stopping_power(bg, M_mev, material))
    return {"beta_gamma": xs, "dedx_mev_cm2_g": ys}
