"""Meios de detecção (líquidos/gases de câmaras de bolhas e alvos sólidos
usados apenas para fins comparativos, como na Figura 3 do artigo à RBEF).

Z, A: número atômico e massa molar [g/mol] (para compostos, valores
efetivos <Z> e <A>).
I: potencial médio de ionização [eV].
rho: densidade [g/cm^3].
conductor: usado apenas para escolher os parâmetros do efeito de
densidade de Sternheimer-Peierls (Seção `bethe_bloch.py`).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    key: str
    name_pt: str
    Z: float
    A: float
    I_eV: float
    rho_gcm3: float
    conductor: bool = False


MATERIALS: dict[str, Material] = {
    "h2_liquid": Material("h2_liquid", "Hidrogênio líquido (câmara CERN)", 1.0, 1.008, 21.8, 0.0708),
    "propane_liquid": Material("propane_liquid", "Propano líquido (C₃H₈)", 2.667, 5.334, 45.0, 0.493),
    "he_gas": Material("he_gas", "Hélio gasoso (CTPN)", 2.0, 4.002602, 41.8, 1.663e-4),
    "carbon": Material("carbon", "Carbono (grafite)", 6.0, 12.011, 78.0, 2.0),
    "aluminum": Material("aluminum", "Alumínio", 13.0, 26.9815, 166.0, 2.70, conductor=True),
    "iron": Material("iron", "Ferro", 26.0, 55.845, 286.0, 7.874, conductor=True),
    "tin": Material("tin", "Estanho", 50.0, 118.71, 488.0, 7.310, conductor=True),
    "lead": Material("lead", "Chumbo", 82.0, 207.2, 823.0, 11.35, conductor=True),
}

DEFAULT_CHAMBER_MATERIAL = "h2_liquid"

_AMU_MEV = 931.49410242  # 1 u em MeV/c^2 (CODATA)


def nucleus_mass_mev(material: Material) -> float:
    """Massa aproximada de um núcleo representativo do meio, M_N ~= A * u,
    ignorando o pequeno defeito de massa de ligação nuclear -- suficiente
    para a demonstração didática da correção de recuo na Eq. 27 do artigo."""
    return material.A * _AMU_MEV


def as_table() -> list[dict]:
    return [
        {
            "key": m.key, "name_pt": m.name_pt, "Z": m.Z, "A": m.A,
            "I_eV": m.I_eV, "rho_gcm3": m.rho_gcm3, "conductor": m.conductor,
        }
        for m in MATERIALS.values()
    ]
