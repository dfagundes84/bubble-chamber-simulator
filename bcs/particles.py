"""Tabela de partículas usada pelo simulador.

Valores de massa e vida média extraídos do Particle Data Group (PDG,
Physical Review D 110, 030001 (2024) — a mesma referência [19] citada no
artigo à RBEF para a fórmula de Bethe-Bloch).

Cada :class:`Particle` carrega os números quânticos necessários para
verificar, nas reações e decaimentos gerados, a conservação de carga
elétrica, número bariônico e estranheza — os mesmos "ingredientes" listados
por Gagnon (2011) na discussão de interpretação de fotografias.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DecayChannel:
    """Um canal de decaimento com sua razão de ramificação (branching ratio)."""
    daughters: tuple[str, ...]
    branching_ratio: float
    label: str = ""  # descrição legível, ex.: "Λ → p π⁻"


@dataclass(frozen=True)
class Particle:
    symbol: str
    name_pt: str
    mass_mev: float
    charge: int              # em unidades de |e|
    baryon_number: int
    strangeness: int
    mean_lifetime_s: float | None  # None => estável no detector
    decays: tuple[DecayChannel, ...] = field(default_factory=tuple)
    antiparticle_of: str | None = None

    @property
    def is_stable_in_chamber(self) -> bool:
        return self.mean_lifetime_s is None

    @property
    def is_neutral(self) -> bool:
        return self.charge == 0


# ---------------------------------------------------------------------------
# Tabela de partículas (massas em MeV/c^2, vida média em s)
# ---------------------------------------------------------------------------
PARTICLES: dict[str, Particle] = {}


def _add(p: Particle) -> None:
    PARTICLES[p.symbol] = p


_add(Particle("gamma", "fóton", 0.0, 0, 0, 0, None))

_add(Particle("e-", "elétron", 0.51099895, -1, 0, 0, None))
_add(Particle("e+", "pósitron", 0.51099895, +1, 0, 0, None))

_add(Particle("mu-", "múon", 105.6583755, -1, 0, 0, 2.1969811e-6,
              decays=(DecayChannel(("e-",), 1.0, "μ⁻ → e⁻ + ν̄ₑ + ν_μ (neutrinos invisíveis)"),)))
_add(Particle("mu+", "antimúon", 105.6583755, +1, 0, 0, 2.1969811e-6,
              decays=(DecayChannel(("e+",), 1.0, "μ⁺ → e⁺ + νₑ + ν̄_μ (neutrinos invisíveis)"),)))

_add(Particle("pi+", "píon positivo", 139.57039, +1, 0, 0, 2.6033e-8,
              decays=(DecayChannel(("mu+",), 1.0, "π⁺ → μ⁺ + ν_μ (invisível)"),)))
_add(Particle("pi-", "píon negativo", 139.57039, -1, 0, 0, 2.6033e-8,
              decays=(DecayChannel(("mu-",), 1.0, "π⁻ → μ⁻ + ν̄_μ (invisível)"),)))
_add(Particle("pi0", "píon neutro", 134.9768, 0, 0, 0, 8.43e-17,
              decays=(DecayChannel(("gamma", "gamma"), 1.0, "π⁰ → γ + γ"),)))

_add(Particle("K+", "káon positivo", 493.677, +1, 0, +1, 1.238e-8,
              decays=(DecayChannel(("mu+",), 1.0, "K⁺ → μ⁺ + ν_μ (invisível)"),)))
_add(Particle("K-", "káon negativo", 493.677, -1, 0, -1, 1.238e-8,
              decays=(DecayChannel(("mu-",), 1.0, "K⁻ → μ⁻ + ν̄_μ (invisível)"),)))
_add(Particle("K0S", "káon neutro (curto)", 497.611, 0, 0, +1, 8.954e-11,
              decays=(
                  DecayChannel(("pi+", "pi-"), 0.692, "K⁰ₛ → π⁺ + π⁻"),
                  DecayChannel((), 0.308, "K⁰ₛ → π⁰ + π⁰ (nenhum traço visível)"),
              )))

_add(Particle("p", "próton", 938.27208816, +1, +1, 0, None))
_add(Particle("n", "nêutron", 939.56542052, 0, +1, 0, 879.4,
              decays=(DecayChannel(("p", "e-"), 1.0, "n → p + e⁻ + ν̄ₑ (vida longa; efetivamente estável na câmara)"),)))

_add(Particle("Lambda0", "lambda", 1115.683, 0, +1, -1, 2.632e-10,
              decays=(DecayChannel(("p", "pi-"), 0.639, "Λ → p + π⁻"),
                       DecayChannel(("n", "pi0"), 0.358, "Λ → n + π⁰ (só o n, invisível)"),)))

_add(Particle("Sigma+", "sigma positivo", 1189.37, +1, +1, -1, 8.018e-11,
              decays=(DecayChannel(("p", "pi0"), 0.516, "Σ⁺ → p + π⁰ (só o p visível)"),
                       DecayChannel(("n", "pi+"), 0.483, "Σ⁺ → n + π⁺ (só o π⁺ visível, n invisível)"),)))
_add(Particle("Sigma-", "sigma negativo", 1197.449, -1, +1, -1, 1.479e-10,
              decays=(DecayChannel(("n", "pi-"), 0.999, "Σ⁻ → n + π⁻ (só o π⁻ visível, n invisível)"),)))
_add(Particle("Sigma0", "sigma neutro", 1192.642, 0, +1, -1, 7.4e-20,
              decays=(DecayChannel(("Lambda0", "gamma"), 1.0, "Σ⁰ → Λ + γ (praticamente no mesmo vértice)"),)))

_add(Particle("Xi0", "xi neutro", 1314.86, 0, +1, -2, 2.90e-10,
              decays=(DecayChannel(("Lambda0",), 1.0, "Ξ⁰ → Λ + π⁰ (só o Λ dá traço)"),)))
_add(Particle("Xi-", "xi negativo", 1321.71, -1, +1, -2, 1.639e-10,
              decays=(DecayChannel(("Lambda0", "pi-"), 1.0, "Ξ⁻ → Λ + π⁻"),)))

_add(Particle("Omega-", "ômega negativo", 1672.45, -1, +1, -3, 8.21e-11,
              decays=(DecayChannel(("Lambda0", "K-"), 0.678, "Ω⁻ → Λ + K⁻"),
                       DecayChannel(("Xi0", "pi-"), 0.236, "Ω⁻ → Ξ⁰ + π⁻"),
                       DecayChannel(("Xi-", "pi0"), 0.086, "Ω⁻ → Ξ⁻ + π⁰"),)))


def get(symbol: str) -> Particle:
    try:
        return PARTICLES[symbol]
    except KeyError as exc:
        raise KeyError(f"Partícula desconhecida: {symbol!r}") from exc


def as_table() -> list[dict]:
    """Serializa a tabela de partículas para consumo pela API/frontend."""
    out = []
    for p in PARTICLES.values():
        out.append({
            "symbol": p.symbol,
            "name_pt": p.name_pt,
            "mass_mev": p.mass_mev,
            "charge": p.charge,
            "baryon_number": p.baryon_number,
            "strangeness": p.strangeness,
            "mean_lifetime_s": p.mean_lifetime_s,
            "decays": [
                {"daughters": d.daughters, "branching_ratio": d.branching_ratio, "label": d.label}
                for d in p.decays
            ],
        })
    return out
