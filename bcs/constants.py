"""Constantes físicas e fatores de conversão de unidades.

Convenções seguidas neste pacote (compatíveis com o artigo à RBEF):
    - Energia, momento e massa em MeV (ou GeV quando indicado).
    - `c` é mantido explícito nas fórmulas relativísticas (E² = (pc)² + (mc²)²),
      mas as unidades práticas (MeV, MeV/c, MeV/c²) tornam os fatores de `c`
      numericamente triviais (ver Tabela I do artigo).
    - Campo magnético em tesla, comprimentos em metros.
"""
from __future__ import annotations

# --- Constantes fundamentais (CODATA / PDG) -------------------------------
C_LIGHT = 2.99792458e8          # velocidade da luz no vácuo [m/s]
ELEMENTARY_CHARGE = 1.602176634e-19  # [C]
AVOGADRO = 6.02214076e23        # [1/mol]
ELECTRON_MASS_MEV = 0.51099895  # massa do elétron [MeV/c^2]
CLASSICAL_ELECTRON_RADIUS_CM = 2.8179403262e-13  # [cm]

# --- Conversões de unidades (Tabela I do artigo) ---------------------------
MEV_TO_JOULE = 1.602176634e-13
GEV_TO_JOULE = 1.602176634e-10
MEV_C_TO_SI = 5.344286e-22      # kg m/s por MeV/c
GEV_C_TO_SI = 5.344286e-19      # kg m/s por GeV/c
MEV_C2_TO_KG = 1.782662e-30     # kg por MeV/c^2
GEV_C2_TO_KG = 1.782662e-27     # kg por GeV/c^2

# --- Constante prática p[GeV/c] = K_PT * B[T] * R[m]  (Eq. 17 do artigo) ---
# K_PT = c / 1e9  (para carga |q| = e)
K_PT = C_LIGHT / 1e9  # ~0.2998 GeV/(T*m)
