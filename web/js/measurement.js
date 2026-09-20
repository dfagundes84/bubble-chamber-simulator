import { api } from "./api.js";

// Ferramenta de medição: clique em 3 pontos sobre um traço para ajustar um
// círculo e estimar p = 0,3 * B * R (Eq. 17 do artigo) -- réplica moderna
// do "virtual tool" de medição de raio do simulador de Gagnon (2011).

export class MeasurementTool {
  constructor({ canvas, renderer, readoutEl, textEl, getB, onResult }) {
    this.canvas = canvas;
    this.renderer = renderer;
    this.readoutEl = readoutEl;
    this.textEl = textEl;
    this.getB = getB;
    this.onResult = onResult || (() => {});
    this.active = false;
    this._onClick = this._onClick.bind(this);
  }

  setActive(active) {
    this.active = active;
    this.renderer.resetMeasure();
    this.readoutEl.classList.toggle("hidden", !active);
    if (active) {
      this.textEl.textContent = "clique em 3 pontos ao longo de um traço";
      this.canvas.addEventListener("click", this._onClick);
    } else {
      this.canvas.removeEventListener("click", this._onClick);
    }
  }

  async _onClick(evt) {
    const rect = this.canvas.getBoundingClientRect();
    const px = evt.clientX - rect.left, py = evt.clientY - rect.top;
    const n = this.renderer.addMeasurePoint(px, py);
    if (n < 3) {
      this.textEl.textContent = `${n}/3 pontos marcados — clique em mais ${3 - n}`;
      return;
    }
    const B = this.getB();
    try {
      const result = await api.measure({ points: this.renderer.measurePoints, B_tesla: B });
      this.renderer.setMeasureCircle(result);
      if (result.radius_m == null) {
        this.textEl.textContent = "pontos quase colineares (traço reto) — raio muito grande, momento muito alto";
      } else {
        const sign = result.curvature_sign > 0 ? "horária (⟳)" : result.curvature_sign < 0 ? "anti-horária (⟲)" : "indefinida";
        this.textEl.innerHTML =
          `R = ${(result.radius_m * 100).toFixed(2)} cm · ` +
          `p = ${result.momentum_mev.toFixed(2)} MeV/c (${result.momentum_gev.toFixed(4)} GeV/c) · ` +
          `curvatura ${sign}`;
      }
      this.onResult(result);
    } catch (err) {
      this.textEl.textContent = "erro ao medir: " + err.message;
    }
    // permite reiniciar a medida com um novo clique
    setTimeout(() => { this.renderer.resetMeasure(); }, 3500);
  }
}
