"""Catálogo de reações de colisão inicial (feixe + próton-alvo -> 2 corpos).

Inspirado nas oito reações do simulador de Gagnon (2011, Figura 3), mas
implementado de forma genérica: a partir daqui, toda a cascata de
decaimentos subsequente é gerada automaticamente por `event.py` a partir da
tabela de partículas (`particles.py`), e não por lógica dedicada a cada
reação. Isso torna trivial adicionar novas reações ou nem partículas.

Todas as reações abaixo conservam explicitamente carga elétrica, número
bariônico e estranheza (verificado em `bcs/tests`), os mesmos números
quânticos discutidos por Gagnon (2011, seção "Result of the initial
inelastic collision") na interpretação de fotografias.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CascadeReaction:
    id: str
    label: str          # ex.: "π⁻ + p → Σ⁻ + K⁺"
    beam: str            # símbolo da partícula do feixe
    target: str = "p"    # alvo, sempre um próton em repouso (núcleo de H líquido)
    product1: str = ""
    product2: str = ""


CASCADE_REACTIONS: list[CascadeReaction] = [
    CascadeReaction("pi_charge_exchange", "π⁻ + p → π⁰ + n", "pi-", "p", "pi0", "n"),
    CascadeReaction("pi_sigma_minus_kplus", "π⁻ + p → Σ⁻ + K⁺", "pi-", "p", "Sigma-", "K+"),
    CascadeReaction("pi_sigma0_k0", "π⁻ + p → Σ⁰ + K⁰", "pi-", "p", "Sigma0", "K0S"),
    CascadeReaction("pi_lambda_k0", "π⁻ + p → Λ + K⁰", "pi-", "p", "Lambda0", "K0S"),
    CascadeReaction("k_lambda_pi0", "K⁻ + p → Λ + π⁰", "K-", "p", "Lambda0", "pi0"),
    CascadeReaction("k_sigma_plus_pi_minus", "K⁻ + p → Σ⁺ + π⁻", "K-", "p", "Sigma+", "pi-"),
    CascadeReaction("k_sigma_minus_pi_plus", "K⁻ + p → Σ⁻ + π⁺", "K-", "p", "Sigma-", "pi+"),
    CascadeReaction("k_xi_minus_kplus", "K⁻ + p → Ξ⁻ + K⁺ (dupla estranheza)", "K-", "p", "Xi-", "K+"),
]

CASCADE_BY_ID: dict[str, CascadeReaction] = {r.id: r for r in CASCADE_REACTIONS}


def as_table() -> list[dict]:
    return [
        {"id": r.id, "label": r.label, "beam": r.beam, "target": r.target,
         "product1": r.product1, "product2": r.product2}
        for r in CASCADE_REACTIONS
    ]
