"""Cinemática relativística: movimento circular em campo magnético e
decaimentos/colisões de dois corpos.

O tratamento de colisões e decaimentos de dois corpos segue o mesmo
formalismo introduzido na Seção II.B.1 do artigo à RBEF (quadrivetores e o
invariante de Mandelstam `s`), em vez da álgebra direta de Gagnon (2011,
Eqs. 5-12). As duas abordagens são fisicamente equivalentes; a usada aqui
tem a vantagem de reduzir *qualquer* processo 2→2 (colisão) ou 1→2
(decaimento) ao mesmo cálculo: obtém-se o referencial do centro de massa via
`s`, aplica-se a fórmula de Källén para o momento das partículas-filhas
nesse referencial e, por fim, faz-se o boost de volta ao laboratório.

Toda a cinemática é tratada em 2D (plano da fotografia da câmara de bolhas),
como em Gagnon (2011), o que é suficiente para preservar a conservação de
energia e momento e para reproduzir as assinaturas visuais discutidas no
artigo (cotovelos, "vês", espirais).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import K_PT


@dataclass(frozen=True)
class FourVector:
    """Quadrimomento na convenção P^mu = (E, p_x, p_y) [MeV] (2D)."""
    E: float
    px: float
    py: float

    def __add__(self, other: "FourVector") -> "FourVector":
        return FourVector(self.E + other.E, self.px + other.px, self.py + other.py)

    def __sub__(self, other: "FourVector") -> "FourVector":
        return FourVector(self.E - other.E, self.px - other.px, self.py - other.py)

    @property
    def p(self) -> float:
        return math.hypot(self.px, self.py)

    @property
    def mass2(self) -> float:
        return self.E ** 2 - self.px ** 2 - self.py ** 2

    @property
    def mass(self) -> float:
        return math.sqrt(max(self.mass2, 0.0))

    @property
    def beta_vec(self) -> tuple[float, float]:
        return (self.px / self.E, self.py / self.E)

    @property
    def angle(self) -> float:
        return math.atan2(self.py, self.px)


def energy_from_momentum(p: float, m: float) -> float:
    """E^2 = p^2 + m^2 (Eq. 2 de Gagnon / Eq. 19 do artigo com c=1)."""
    return math.sqrt(p * p + m * m)


def four_vector_from_pmag(p_mag: float, angle_rad: float, m: float) -> FourVector:
    E = energy_from_momentum(p_mag, m)
    return FourVector(E, p_mag * math.cos(angle_rad), p_mag * math.sin(angle_rad))


def lorentz_gamma_from_beta(beta: float) -> float:
    return 1.0 / math.sqrt(max(1.0 - beta * beta, 1e-15))


def boost(vec: FourVector, beta_vec: tuple[float, float]) -> FourVector:
    """Aplica um boost de Lorentz 2D para levar `vec` a um referencial que se
    move com velocidade `beta_vec` em relação ao referencial atual de `vec`.
    """
    bx, by = beta_vec
    beta2 = bx * bx + by * by
    if beta2 < 1e-24:
        return vec
    gamma = lorentz_gamma_from_beta(math.sqrt(beta2))
    bp = bx * vec.px + by * vec.py
    coeff = (gamma - 1.0) / beta2
    E2 = gamma * (vec.E - bp)
    px2 = vec.px + coeff * bp * bx - gamma * bx * vec.E
    py2 = vec.py + coeff * bp * by - gamma * by * vec.E
    return FourVector(E2, px2, py2)


def kallen_momentum(M: float, m1: float, m2: float) -> float:
    """Momento (módulo) de cada partícula-filha no referencial de centro de
    massa de um sistema de massa invariante M -> m1 + m2, via função de
    Källén: p* = sqrt(lambda(M^2, m1^2, m2^2)) / (2M).

    Retorna 0.0 (com um piso numérico) se o canal for cinematicamente
    proibido (M < m1 + m2).
    """
    if M < m1 + m2:
        return 0.0
    M2, m12, m22 = M * M, m1 * m1, m2 * m2
    lam = M2 * M2 + m12 * m12 + m22 * m22 - 2 * M2 * m12 - 2 * M2 * m22 - 2 * m12 * m22
    lam = max(lam, 0.0)
    return math.sqrt(lam) / (2.0 * M)


def two_body_split(parent: FourVector, m1: float, m2: float, theta_cm: float
                    ) -> tuple[FourVector, FourVector]:
    """Divide o quadrimomento `parent` em dois quadrimomentos de massas
    m1, m2, com ângulo de emissão `theta_cm` sorteado no referencial de
    centro de massa (CM) do próprio `parent`.

    Funciona tanto para uma colisão (parent = feixe + alvo) quanto para um
    decaimento (parent = partícula-mãe) — a mesma matemática (Seção II.B.1
    do artigo; Eqs. 5-12 de Gagnon 2011, aqui reescritas via invariante s).
    """
    M = parent.mass
    p_star = kallen_momentum(M, m1, m2)
    E1_star = energy_from_momentum(p_star, m1)
    E2_star = energy_from_momentum(p_star, m2)

    # Quadrimomentos no CM (repouso do `parent`)
    d1_cm = FourVector(E1_star, p_star * math.cos(theta_cm), p_star * math.sin(theta_cm))
    d2_cm = FourVector(E2_star, -p_star * math.cos(theta_cm), -p_star * math.sin(theta_cm))

    # Boost de volta ao referencial em que `parent` foi definido (lab)
    beta_vec = (parent.px / parent.E, parent.py / parent.E)
    # boost() leva vec *para* o referencial que se move com +beta_vec em
    # relação ao referencial atual; para "desfazer" o CM->lab precisamos do
    # boost com -beta_vec aplicado a um quadrivetor cujo referencial de
    # repouso é o CM. Equivalente: aplicar boost(-beta) inverso.
    d1_lab = _boost_to_frame_moving_at(d1_cm, beta_vec)
    d2_lab = _boost_to_frame_moving_at(d2_cm, beta_vec)
    return d1_lab, d2_lab


def _boost_to_frame_moving_at(vec_rest: FourVector, beta_vec: tuple[float, float]) -> FourVector:
    """Dado um quadrivetor definido no referencial de repouso de um sistema
    que se move com velocidade `beta_vec` em relação ao laboratório, retorna
    o quadrivetor no laboratório (boost com -beta_vec, na convenção usual)."""
    bx, by = -beta_vec[0], -beta_vec[1]
    return boost(vec_rest, (bx, by))


# --- Movimento circular em campo magnético (Seção II.A do artigo) ----------

def momentum_perp_gev(B_tesla: float, radius_m: float) -> float:
    """p_perp [GeV/c] = K_PT * B[T] * R[m]  (Eq. 17)."""
    return K_PT * B_tesla * radius_m


def radius_from_momentum_gev(B_tesla: float, p_gev: float) -> float:
    """R[m] = p[GeV/c] / (K_PT * B[T])  — inverso da Eq. 17."""
    if B_tesla <= 0:
        return math.inf
    return p_gev / (K_PT * B_tesla)


def radius_from_momentum_mev(B_tesla: float, p_mev: float) -> float:
    return radius_from_momentum_gev(B_tesla, p_mev / 1000.0)


def momentum_perp_mev(B_tesla: float, radius_m: float) -> float:
    return momentum_perp_gev(B_tesla, radius_m) * 1000.0


def rotate_momentum(vec: FourVector, dtheta: float) -> FourVector:
    """Rotaciona a parte espacial de `vec` por `dtheta` (rad), mantendo E e
    o módulo do momento. Útil para levar um resultado calculado com o feixe
    ao longo de +x para a direção real de voo (ex.: conversão de um fóton
    que já não se propaga mais ao longo do eixo do feixe original)."""
    c, s = math.cos(dtheta), math.sin(dtheta)
    return FourVector(vec.E, vec.px * c - vec.py * s, vec.px * s + vec.py * c)


def decay_length_m(p_mev: float, mass_mev: float, mean_lifetime_s: float,
                    c: float = 2.99792458e8) -> float:
    """Comprimento médio de decaimento no laboratório: <L> = beta*gamma*c*tau.

    beta*gamma = p/m (identidade relativística), o que evita calcular beta e
    gamma separadamente.
    """
    if mean_lifetime_s is None or mass_mev <= 0:
        return math.inf
    beta_gamma = p_mev / mass_mev
    return beta_gamma * c * mean_lifetime_s
