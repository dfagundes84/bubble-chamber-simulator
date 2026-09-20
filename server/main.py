"""Servidor da API do simulador de Câmara de Bolhas (BCS).

Serve tanto os endpoints de física (usados pelo frontend em `web/`) quanto,
como arquivos estáticos, a própria interface web.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from bcs import bethe_bloch as bb
from bcs import event as ev
from bcs import materials as materials_db
from bcs import measurement as meas
from bcs import particles as particles_db
from bcs import pair_production as pp
from bcs import reactions as reactions_db
from bcs.materials import MATERIALS, nucleus_mass_mev

from server.schemas import (CascadeEventRequest, DedxCurveRequest, MeasureRequest,
                             PairEventRequest, SingleTrackRequest, ThresholdCurveRequest)

WEB_DIR = ROOT_DIR / "web"

app = FastAPI(title="BCS -- Simulador de Câmara de Bolhas", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/particles")
def get_particles():
    return particles_db.as_table()


@app.get("/api/materials")
def get_materials():
    return materials_db.as_table()


@app.get("/api/reactions")
def get_reactions():
    return reactions_db.as_table()


@app.post("/api/event/cascade")
def post_event_cascade(req: CascadeEventRequest):
    if req.reaction_id != "random" and req.reaction_id not in reactions_db.CASCADE_BY_ID:
        raise HTTPException(404, f"Reação desconhecida: {req.reaction_id}")
    return ev.generate_cascade_event(
        reaction_id=req.reaction_id, beam_momentum_gev=req.beam_momentum_gev,
        B_tesla=req.B_tesla, material_key=req.material_key, seed=req.seed,
        gamma_conversion_probability=req.gamma_conversion_probability,
        n_background_tracks=req.n_background_tracks,
    )


@app.post("/api/event/single")
def post_event_single(req: SingleTrackRequest):
    if req.particle_symbol not in particles_db.PARTICLES:
        raise HTTPException(404, f"Partícula desconhecida: {req.particle_symbol}")
    return ev.generate_single_track_event(
        particle_symbol=req.particle_symbol, momentum_mev=req.momentum_mev,
        angle_deg=req.angle_deg, B_tesla=req.B_tesla, material_key=req.material_key,
        seed=req.seed,
    )


@app.post("/api/event/pair")
def post_event_pair(req: PairEventRequest):
    return ev.generate_pair_production_event(
        photon_energy_mev=req.photon_energy_mev, B_tesla=req.B_tesla,
        material_key=req.material_key, seed=req.seed,
    )


@app.post("/api/dedx_curve")
def post_dedx_curve(req: DedxCurveRequest):
    out = {}
    for key in req.material_keys:
        if key not in MATERIALS:
            raise HTTPException(404, f"Material desconhecido: {key}")
        out[key] = bb.dedx_curve(
            MATERIALS[key], beta_gamma_min=req.beta_gamma_min,
            beta_gamma_max=req.beta_gamma_max, n_points=req.n_points, M_mev=req.M_mev,
        )
    return out


@app.post("/api/pair_threshold_curve")
def post_pair_threshold_curve(req: ThresholdCurveRequest):
    return pp.threshold_curve(req.m_min_mev, req.m_max_mev, req.n_points)


@app.get("/api/pair_threshold/{material_key}")
def get_pair_threshold_for_material(material_key: str):
    if material_key not in MATERIALS:
        raise HTTPException(404, f"Material desconhecido: {material_key}")
    material = MATERIALS[material_key]
    M_N = nucleus_mass_mev(material)
    e_mass = particles_db.get("e-").mass_mev
    return {
        "material_key": material_key, "nucleus_mass_mev": M_N,
        "threshold_mev": pp.threshold_energy_mev(M_N, e_mass),
        "no_recoil_limit_mev": 2 * e_mass,
    }


@app.post("/api/measure")
def post_measure(req: MeasureRequest):
    return meas.measure(req.points, req.B_tesla)


# --- Arquivos estáticos do frontend ----------------------------------------
if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")

    @app.get("/")
    def index():
        return FileResponse(WEB_DIR / "index.html")
