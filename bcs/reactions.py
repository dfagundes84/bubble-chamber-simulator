"""Catálogo de reações de colisão inicial (feixe + próton-alvo -> N corpos).

Inspirado nas oito reações do simulador de Gagnon (2011, Figura 3), mas
implementado de forma genérica: a partir daqui, toda a cascata de
decaimentos subsequente é gerada automaticamente por `event.py` a partir da
tabela de partículas (`particles.py`), e não por lógica dedicada a cada
reação. Isso torna trivial adicionar novas reações ou novas partículas.

A maioria das reações tem exatamente 2 produtos na colisão inicial, mas
`products` aceita qualquer número >= 2 -- necessário, por exemplo, para a
reação de descoberta do Ω⁻ (Barnes et al., BNL 1964), que é um processo de
3 corpos: K⁻ + p -> Ω⁻ + K⁺ + K⁰. `event.py` decompõe N > 2 produtos em
splits sequenciais de 2 corpos (mesma técnica usada em
`pair_production.py`), então nenhuma física nova precisa existir aqui --
só a lista de partículas finais.

Todas as reações abaixo conservam explicitamente carga elétrica, número
bariônico e estranheza (verificado em `tests/`), os mesmos números
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
    products: tuple[str, ...] = ()


CASCADE_REACTIONS: list[CascadeReaction] = [
    CascadeReaction("pi_charge_exchange", "π⁻ + p → π⁰ + n", "pi-", "p", ("pi0", "n")),
    CascadeReaction("pi_sigma_minus_kplus", "π⁻ + p → Σ⁻ + K⁺", "pi-", "p", ("Sigma-", "K+")),
    CascadeReaction("pi_sigma0_k0", "π⁻ + p → Σ⁰ + K⁰", "pi-", "p", ("Sigma0", "K0S")),
    CascadeReaction("pi_lambda_k0", "π⁻ + p → Λ + K⁰", "pi-", "p", ("Lambda0", "K0S")),
    CascadeReaction("k_lambda_pi0", "K⁻ + p → Λ + π⁰", "K-", "p", ("Lambda0", "pi0")),
    CascadeReaction("k_sigma_plus_pi_minus", "K⁻ + p → Σ⁺ + π⁻", "K-", "p", ("Sigma+", "pi-")),
    CascadeReaction("k_sigma_minus_pi_plus", "K⁻ + p → Σ⁻ + π⁺", "K-", "p", ("Sigma-", "pi+")),
    CascadeReaction("k_xi_minus_kplus", "K⁻ + p → Ξ⁻ + K⁺ (dupla estranheza)", "K-", "p", ("Xi-", "K+")),
    CascadeReaction("k_omega_discovery", "K⁻ + p → Ω⁻ + K⁺ + K⁰ (descoberta do Ω⁻, BNL 1964)",
                     "K-", "p", ("Omega-", "K+", "K0S")),
]

CASCADE_BY_ID: dict[str, CascadeReaction] = {r.id: r for r in CASCADE_REACTIONS}


def as_table() -> list[dict]:
    return [
        {"id": r.id, "label": r.label, "beam": r.beam, "target": r.target,
         "products": list(r.products)}
        for r in CASCADE_REACTIONS
    ]
