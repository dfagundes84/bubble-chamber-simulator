"""Modelos Pydantic para as requisições/respostas da API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CascadeEventRequest(BaseModel):
    reaction_id: str = "random"
    beam_momentum_gev: float = Field(24.0, gt=0, le=1000)
    B_tesla: float = Field(1.7, ge=0, le=10)
    material_key: str = "h2_liquid"
    seed: int | None = None
    photon_interaction_probability: float = Field(0.65, ge=0, le=1)
    n_background_tracks: int = Field(4, ge=0, le=12)
    beam_scatter_probability: float = Field(0.15, ge=0, le=1)


class SingleTrackRequest(BaseModel):
    particle_symbol: str = "p"
    momentum_mev: float = Field(1000.0, gt=0, le=1_000_000)
    angle_deg: float = Field(0.0, ge=-180, le=180)
    B_tesla: float = Field(1.7, ge=0, le=10)
    material_key: str = "h2_liquid"
    seed: int | None = None
    allow_scattering: bool = False
    scatter_probability: float = Field(0.5, ge=0, le=1)


class PhotonEventRequest(BaseModel):
    photon_energy_mev: float = Field(50.0, gt=0, le=1_000_000)
    B_tesla: float = Field(1.7, ge=0, le=10)
    material_key: str = "h2_liquid"
    seed: int | None = None


class DedxCurveRequest(BaseModel):
    material_keys: list[str] = Field(default_factory=lambda: ["h2_liquid"])
    M_mev: float = Field(938.27208816, gt=0)
    beta_gamma_min: float = Field(0.1, gt=0)
    beta_gamma_max: float = Field(1.0e4, gt=0)
    n_points: int = Field(200, ge=10, le=2000)


class ThresholdCurveRequest(BaseModel):
    m_min_mev: float = Field(200.0, gt=0)
    m_max_mev: float = Field(2.0e5, gt=0)
    n_points: int = Field(200, ge=10, le=2000)


class MeasureRequest(BaseModel):
    points: list[tuple[float, float]] = Field(..., min_length=3)
    B_tesla: float = Field(1.7, ge=0, le=10)
