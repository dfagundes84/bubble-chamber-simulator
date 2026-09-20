"""Processos eletromagnéticos que um feixe de prótons (ou qualquer partícula
carregada, ou um fóton) sofre ao atravessar o líquido da câmara, além da
ionização contínua já descrita pela fórmula de Bethe-Bloch
(`bethe_bloch.py`) e da produção de pares (`pair_production.py`).

Reproduz as quatro assinaturas discutidas no roteiro do S'Cool LAB/CERN
(Woithe, Schmidt & Naumann, 2018, *Student worksheet: Bubble chamber
pictures*, Atividade 3):

    - "Electron"          -> espalhamento elástico feixe + elétron do meio
                              (raio-delta / knock-on electron)
    - "Proton"             -> espalhamento elástico feixe + próton do meio
                              (mesma física, alvo diferente)
    - "Compton electron"   -> espalhamento Compton de um fóton com um
                              elétron do meio
    - "Positron"           -> produção de pares (já implementada em
                              `pair_production.py`)

Espalhamento elástico (raio-delta / recuo de próton)
-----------------------------------------------------
Para uma partícula de feixe (massa M, quadrimomento `beam_vec`) colidindo
elasticamente com um alvo em repouso (massa `target_mass_mev`), a energia
cinética T transferida ao alvo está relacionada ao ângulo de emissão no
referencial do centro de massa, `theta_cm`, por uma expressão *linear* em
cos(theta_cm) -- consequência direta do boost do CM para o laboratório:

    T(theta_cm) = gamma_boost * (E_alvo* + beta_boost * p* * cos(theta_cm)) - m_alvo

com `E_alvo*`, `p*` a energia e o momento do alvo no referencial do centro
de massa (a mesma função de Källén usada em `kinematics.two_body_split`) e
`gamma_boost`, `beta_boost` o fator de Lorentz e a velocidade desse
referencial em relação ao laboratório. Como a relação é linear, ela pode
ser invertida em forma fechada -- sem iteração -- para amostrar T a partir
da distribuição diferencial correta,

    dσ/dT ∝ 1/T²        (fórmula de Rutherford/Møller, o mesmo resultado
                          por trás do termo T_max da fórmula de Bethe-Bloch),

e então obter o `theta_cm` correspondente, que é passado a
`kinematics.two_body_split` para gerar o quadrimomento final exato de
ambas as partículas -- garantindo conservação de energia-momento pela
mesma rotina já testada em `tests/test_kinematics.py`.

Espalhamento Compton (γ + e⁻ → γ' + e⁻')
------------------------------------------
Cinemática fechada padrão (fóton sem massa, portanto fora do escopo de
`two_body_split`, que assume duas partículas massivas no estado final).
O ângulo de espalhamento do fóton é amostrado uniformemente -- uma
simplificação deliberada (a seção de choque real, Klein-Nishina, favorece
ângulos pequenos em altas energias), no mesmo espírito de outras
aproximações já documentadas neste pacote (ver README, seção
"Limitações conhecidas").
"""
from __future__ import annotations

import math
import random

from .kinematics import FourVector, kallen_momentum, rotate_momentum, two_body_split


def elastic_scatter_tmax_mev(beam_vec: FourVector, beam_mass_mev: float,
                              target_mass_mev: float) -> float:
    """Energia cinética máxima transferível ao alvo (theta_cm = 0)."""
    parent = beam_vec + FourVector(target_mass_mev, 0.0, 0.0)
    M = parent.mass
    if M < beam_mass_mev + target_mass_mev:
        return 0.0
    gamma_boost = parent.E / M
    beta_boost = math.hypot(parent.px, parent.py) / parent.E
    E_target_star = (M * M + target_mass_mev * target_mass_mev - beam_mass_mev * beam_mass_mev) / (2.0 * M)
    p_star = kallen_momentum(M, beam_mass_mev, target_mass_mev)
    return gamma_boost * (E_target_star + beta_boost * p_star) - target_mass_mev


def sample_elastic_knockon(*, beam_vec: FourVector, beam_mass_mev: float,
                            target_mass_mev: float, t_min_mev: float,
                            rng: random.Random | None = None
                            ) -> tuple[FourVector, FourVector] | None:
    """Amostra um espalhamento elástico feixe+alvo(em repouso), com a
    energia cinética T do alvo distribuída como dσ/dT ~ 1/T^2 (Rutherford)
    entre `t_min_mev` e o T máximo cinematicamente permitido.

    Retorna (feixe_depois, alvo_depois) em MeV, ou None se T_max <= t_min
    (momento do feixe baixo demais para gerar um traço visível).
    """
    rng = rng or random
    parent = beam_vec + FourVector(target_mass_mev, 0.0, 0.0)
    M = parent.mass
    gamma_boost = parent.E / M
    beta_boost = math.hypot(parent.px, parent.py) / parent.E
    E_target_star = (M * M + target_mass_mev * target_mass_mev - beam_mass_mev * beam_mass_mev) / (2.0 * M)
    p_star = kallen_momentum(M, beam_mass_mev, target_mass_mev)
    if p_star <= 0 or beta_boost <= 0:
        return None

    t_max = gamma_boost * (E_target_star + beta_boost * p_star) - target_mass_mev
    if t_max <= t_min_mev:
        return None

    u = rng.random()
    inv_t = (1.0 / t_min_mev) - u * ((1.0 / t_min_mev) - (1.0 / t_max))
    t = 1.0 / inv_t

    cos_theta_cm = ((t + target_mass_mev) / gamma_boost - E_target_star) / (beta_boost * p_star)
    cos_theta_cm = max(-1.0, min(1.0, cos_theta_cm))
    theta_cm_target = math.acos(cos_theta_cm)
    if rng.random() < 0.5:
        theta_cm_target = -theta_cm_target

    # `two_body_split(parent, m1, m2, theta_cm)` emite a partícula 1 (aqui, o
    # feixe) no ângulo `theta_cm` e a partícula 2 (o alvo) no ângulo oposto,
    # `theta_cm + pi` -- mas `theta_cm_target` acima foi derivado como o
    # ângulo do ALVO. Corrige o deslocamento de fase para que o alvo termine
    # exatamente no ângulo usado para calcular T.
    return two_body_split(parent, beam_mass_mev, target_mass_mev, theta_cm_target + math.pi)


def compton_scatter(*, photon_vec: FourVector, electron_mass_mev: float,
                     rng: random.Random | None = None) -> tuple[FourVector, FourVector]:
    """Espalhamento Compton γ + e⁻(repouso) → γ' + e⁻'.

    `photon_vec` é o quadrimomento do fóton incidente (E = p, ao longo de
    sua direção de voo). O ângulo de espalhamento do fóton é amostrado
    uniformemente em [0, 2π) (simplificação -- ver docstring do módulo).
    Retorna (fóton_depois, elétron_de_recuo).
    """
    rng = rng or random
    E_gamma = photon_vec.p
    theta = rng.uniform(0.0, 2.0 * math.pi)
    E_gamma_out = E_gamma / (1.0 + (E_gamma / electron_mass_mev) * (1.0 - math.cos(theta)))

    beam_angle = photon_vec.angle
    photon_out_local = FourVector(E_gamma_out, E_gamma_out * math.cos(theta), E_gamma_out * math.sin(theta))
    electron_px_local = E_gamma - E_gamma_out * math.cos(theta)
    electron_py_local = -E_gamma_out * math.sin(theta)
    electron_E_local = E_gamma - E_gamma_out + electron_mass_mev
    electron_local = FourVector(electron_E_local, electron_px_local, electron_py_local)

    photon_out = rotate_momentum(photon_out_local, beam_angle)
    electron_out = rotate_momentum(electron_local, beam_angle)
    return photon_out, electron_out


def compton_vs_pair_probability(photon_energy_mev: float, pair_threshold_mev: float) -> float:
    """Probabilidade (heurística, não uma seção de choque real) de que um
    fóton que interage no meio o faça por produção de pares em vez de
    espalhamento Compton, como função da energia.

    Fisicamente, a seção de choque de produção de pares só existe acima do
    limiar (Eq. 27 do artigo) e cresce lentamente com a energia até
    dominar sobre Compton bem acima dele; a de Compton (Klein-Nishina)
    domina perto do limiar e decresce lentamente em energias mais altas.
    Aproximamos essa transição com uma sigmoide centrada numa dezena de
    vezes o limiar -- suficiente para dar, de forma qualitativamente
    correta, "quase sempre Compton perto do limiar" e "pares favorecidos
    bem acima dele", sem pretender reproduzir Klein-Nishina/Bethe-Heitler
    quantitativamente (ver README, "Limitações conhecidas").
    """
    if photon_energy_mev < pair_threshold_mev:
        return 0.0
    x = photon_energy_mev / (10.0 * pair_threshold_mev)
    return x / (1.0 + x)
