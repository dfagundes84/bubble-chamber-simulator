// Renderização da câmara: converte a geometria de traços (em metros, vinda
// da API) em um desenho estilo fotografia de câmara de bolhas, com traços
// que "crescem" (simulando a nucleação de bolhas) e brilho (glow) por carga.

const COLORS = {
  neg: "#57b8ff",
  pos: "#ff9457",
  neutral: "#8fa0ad",
  classic: "#eaffef",
};

function lerp(a, b, t) { return a + (b - a) * t; }

export class ChamberRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.event = null;
    this.options = {
      showNeutrals: false, showLabels: true, showBackground: true,
      showNoise: true, colorByCharge: true,
    };
    this.chamber = { half_width_m: 1.0, half_height_m: 0.55 };
    this.animStart = null;
    this.animDurationMs = 1100;
    this.animating = false;
    this.hoverTrackId = null;
    this.measurePoints = [];
    this.measureCircle = null;
    this.noiseDots = [];
    this._resizeObserver = new ResizeObserver(() => this.resize());
    this._resizeObserver.observe(canvas.parentElement);
    this.resize();
    this._genNoise();
    this._raf = this._raf.bind(this);
    requestAnimationFrame(this._raf);
  }

  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.canvas.width = Math.max(1, Math.round(rect.width * dpr));
    this.canvas.height = Math.max(1, Math.round(rect.height * dpr));
    this.canvas.style.width = rect.width + "px";
    this.canvas.style.height = rect.height + "px";
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.cssWidth = rect.width;
    this.cssHeight = rect.height;
    this._genNoise();
  }

  _genNoise() {
    const n = 140;
    this.noiseDots = Array.from({ length: n }, () => ({
      x: Math.random(), y: Math.random(), r: Math.random() * 1.1 + 0.2,
      a: Math.random() * 0.10 + 0.02,
    }));
  }

  setOptions(opts) { Object.assign(this.options, opts); }

  setEvent(eventData) {
    this.event = eventData;
    this.chamber = eventData.chamber || this.chamber;
    this.animStart = performance.now();
    this.animating = true;
    this.measurePoints = [];
    this.measureCircle = null;
  }

  clear() {
    this.event = null;
    this.measurePoints = [];
    this.measureCircle = null;
  }

  // --- transformação física (m) <-> tela (px, origem no canto sup. esq.) ---
  _margin() { return 26; }

  physToScreen(x, y) {
    const m = this._margin();
    const w = this.cssWidth - 2 * m, h = this.cssHeight - 2 * m;
    const sx = m + ((x + this.chamber.half_width_m) / (2 * this.chamber.half_width_m)) * w;
    const sy = m + (1 - (y + this.chamber.half_height_m) / (2 * this.chamber.half_height_m)) * h;
    return [sx, sy];
  }

  screenToPhys(px, py) {
    const m = this._margin();
    const w = this.cssWidth - 2 * m, h = this.cssHeight - 2 * m;
    const x = ((px - m) / w) * (2 * this.chamber.half_width_m) - this.chamber.half_width_m;
    const y = (1 - (py - m) / h) * (2 * this.chamber.half_height_m) - this.chamber.half_height_m;
    return [x, y];
  }

  trackColor(track) {
    if (!this.options.colorByCharge) return COLORS.classic;
    if (track.charge > 0) return COLORS.pos;
    if (track.charge < 0) return COLORS.neg;
    return COLORS.neutral;
  }

  hitTest(px, py) {
    if (!this.event) return null;
    let best = null, bestDist = 14;
    for (const t of this.event.tracks) {
      if (!t.visible && !this.options.showNeutrals) continue;
      for (const [x, y] of t.points) {
        const [sx, sy] = this.physToScreen(x, y);
        const d = Math.hypot(sx - px, sy - py);
        if (d < bestDist) { bestDist = d; best = t; }
      }
    }
    return best;
  }

  addMeasurePoint(px, py) {
    if (this.measurePoints.length >= 3) this.measurePoints = [];
    this.measurePoints.push(this.screenToPhys(px, py));
    return this.measurePoints.length;
  }

  resetMeasure() { this.measurePoints = []; this.measureCircle = null; }
  setMeasureCircle(circle) { this.measureCircle = circle; }

  _raf(t) {
    this.render(t);
    requestAnimationFrame(this._raf);
  }

  render(now) {
    const ctx = this.ctx;
    const w = this.cssWidth, h = this.cssHeight;
    ctx.clearRect(0, 0, w, h);

    this._drawBackground(ctx, w, h);
    this._drawFiducials(ctx, w, h);

    let progress = 1;
    if (this.animating && this.animStart != null) {
      progress = Math.min(1, (now - this.animStart) / this.animDurationMs);
      if (progress >= 1) this.animating = false;
    }

    if (this.event) {
      const tracks = [...this.event.tracks].sort((a, b) => a.generation - b.generation);
      for (const t of tracks) this._drawTrack(ctx, t, progress);
      if (this.options.showLabels) {
        for (const t of tracks) this._drawLabel(ctx, t, progress);
      }
      this._drawVertices(ctx, progress);
    }

    this._drawMeasurement(ctx);
    this._drawFrameVignette(ctx, w, h);
  }

  _drawBackground(ctx, w, h) {
    const g = ctx.createRadialGradient(w * 0.5, h * 0.42, Math.min(w, h) * 0.15, w * 0.5, h * 0.5, Math.max(w, h) * 0.75);
    g.addColorStop(0, "#0a2c1f");
    g.addColorStop(0.55, "#062017");
    g.addColorStop(1, "#020e09");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);

    if (this.options.showNoise) {
      for (const d of this.noiseDots) {
        ctx.beginPath();
        ctx.fillStyle = `rgba(210,255,235,${d.a})`;
        ctx.arc(d.x * w, d.y * h, d.r, 0, 6.283);
        ctx.fill();
      }
    }
  }

  _drawFiducials(ctx, w, h) {
    // marcas de referência tipo "x" nas bordas superior/inferior, como nas
    // fotografias reais da câmara (Figuras 4-6 do artigo)
    ctx.strokeStyle = "rgba(210,255,235,0.22)";
    ctx.lineWidth = 1.1;
    const rows = [12, h - 12];
    for (const y of rows) {
      for (let i = 0; i < 16; i++) {
        const x = 14 + i * ((w - 28) / 15);
        ctx.beginPath();
        ctx.moveTo(x - 4, y - 4); ctx.lineTo(x + 4, y + 4);
        ctx.moveTo(x - 4, y + 4); ctx.lineTo(x + 4, y - 4);
        ctx.stroke();
      }
    }
  }

  _drawFrameVignette(ctx, w, h) {
    const g = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.35, w / 2, h / 2, Math.max(w, h) * 0.72);
    g.addColorStop(0, "rgba(0,0,0,0)");
    g.addColorStop(1, "rgba(0,0,0,0.45)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  }

  _drawTrack(ctx, t, globalProgress) {
    if (!t.visible && !this.options.showNeutrals) return;
    const pts = t.points;
    if (pts.length < 2) return;

    const delay = Math.min(0.5, t.generation * 0.12);
    const local = Math.max(0, Math.min(1, (globalProgress - delay) / (1 - delay || 1)));
    if (local <= 0) return;
    const nShow = Math.max(2, Math.round(pts.length * local));
    const shown = pts.slice(0, nShow);

    const color = this.trackColor(t);
    const isHover = this.hoverTrackId === t.id;
    const neutral = t.charge === 0;

    ctx.save();
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    if (neutral) ctx.setLineDash([2, 6]); else ctx.setLineDash([]);

    // glow
    if (!neutral) {
      ctx.shadowColor = color;
      ctx.shadowBlur = isHover ? 16 : (t.is_spiral ? 11 : 7);
    }
    ctx.strokeStyle = neutral ? "rgba(160,180,190,0.55)" : color;
    ctx.globalAlpha = neutral ? 0.7 : 0.95;
    ctx.lineWidth = isHover ? 3.2 : (neutral ? 1.4 : 2.1);

    ctx.beginPath();
    let [sx, sy] = this.physToScreen(shown[0][0], shown[0][1]);
    ctx.moveTo(sx, sy);
    for (let i = 1; i < shown.length; i++) {
      [sx, sy] = this.physToScreen(shown[i][0], shown[i][1]);
      ctx.lineTo(sx, sy);
    }
    ctx.stroke();

    // núcleo brilhante fino por cima (efeito "bolha luminosa")
    if (!neutral) {
      ctx.shadowBlur = 0;
      ctx.globalAlpha = 0.9;
      ctx.lineWidth = 0.9;
      ctx.strokeStyle = "rgba(255,255,255,0.55)";
      ctx.stroke();
    }
    ctx.restore();
  }

  _drawLabel(ctx, t, globalProgress) {
    if (!t.visible && !this.options.showNeutrals) return;
    if (t.points.length < 2) return;
    const delay = Math.min(0.5, t.generation * 0.12);
    const local = Math.max(0, Math.min(1, (globalProgress - delay) / (1 - delay || 1)));
    if (local < 0.98) return;
    const mid = t.points[Math.floor(t.points.length * 0.55)];
    const [sx, sy] = this.physToScreen(mid[0], mid[1]);
    ctx.save();
    ctx.font = "600 11px var(--font-ui), sans-serif";
    ctx.fillStyle = "rgba(233,240,255,0.85)";
    ctx.shadowColor = "rgba(0,0,0,0.8)";
    ctx.shadowBlur = 4;
    ctx.fillText(symbolLabel(t.particle), sx + 6, sy - 6);
    ctx.restore();
  }

  _drawVertices(ctx, globalProgress) {
    if (!this.event || !this.event.vertices) return;
    for (const v of this.event.vertices) {
      const [sx, sy] = this.physToScreen(v.x, v.y);
      ctx.save();
      ctx.globalAlpha = 0.9;
      if (v.type === "collision") {
        ctx.fillStyle = "#ffd76a";
        ctx.shadowColor = "#ffd76a"; ctx.shadowBlur = 10;
        drawStar(ctx, sx, sy, 5, 6, 3);
      } else if (v.type === "conversion") {
        ctx.strokeStyle = "#ff6bd6"; ctx.shadowColor = "#ff6bd6"; ctx.shadowBlur = 8;
        ctx.lineWidth = 1.6;
        ctx.beginPath(); ctx.arc(sx, sy, 5, 0, 6.283); ctx.stroke();
      } else {
        ctx.fillStyle = "#bde8ff";
        ctx.shadowColor = "#bde8ff"; ctx.shadowBlur = 6;
        ctx.beginPath(); ctx.arc(sx, sy, 2.6, 0, 6.283); ctx.fill();
      }
      ctx.restore();
    }
  }

  _drawMeasurement(ctx) {
    for (const [x, y] of this.measurePoints) {
      const [sx, sy] = this.physToScreen(x, y);
      ctx.save();
      ctx.strokeStyle = "#ffcf6b"; ctx.fillStyle = "rgba(255,207,107,0.25)";
      ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.arc(sx, sy, 6, 0, 6.283); ctx.fill(); ctx.stroke();
      ctx.restore();
    }
    if (this.measureCircle && this.measureCircle.center) {
      const { x: cx, y: cy } = this.measureCircle.center;
      const R = this.measureCircle.radius_m;
      const [scx, scy] = this.physToScreen(cx, cy);
      const [ex] = this.physToScreen(cx + R, cy);
      const rpx = Math.abs(ex - scx);
      ctx.save();
      ctx.strokeStyle = "rgba(255,207,107,0.85)";
      ctx.setLineDash([5, 5]);
      ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.arc(scx, scy, rpx, 0, 6.283); ctx.stroke();
      ctx.beginPath(); ctx.arc(scx, scy, 3, 0, 6.283); ctx.fillStyle = "#ffcf6b"; ctx.fill();
      ctx.restore();
    }
  }
}

function drawStar(ctx, cx, cy, spikes, outerR, innerR) {
  let rot = (Math.PI / 2) * 3;
  const step = Math.PI / spikes;
  ctx.beginPath();
  ctx.moveTo(cx, cy - outerR);
  for (let i = 0; i < spikes; i++) {
    ctx.lineTo(cx + Math.cos(rot) * outerR, cy + Math.sin(rot) * outerR); rot += step;
    ctx.lineTo(cx + Math.cos(rot) * innerR, cy + Math.sin(rot) * innerR); rot += step;
  }
  ctx.closePath();
  ctx.fill();
}

const LABELS = {
  "gamma": "γ", "e-": "e⁻", "e+": "e⁺", "mu-": "μ⁻", "mu+": "μ⁺",
  "pi+": "π⁺", "pi-": "π⁻", "pi0": "π⁰", "K+": "K⁺", "K-": "K⁻", "K0S": "K⁰",
  "p": "p", "n": "n", "Lambda0": "Λ", "Sigma+": "Σ⁺", "Sigma-": "Σ⁻",
  "Sigma0": "Σ⁰", "Xi0": "Ξ⁰", "Xi-": "Ξ⁻",
};
export function symbolLabel(sym) { return LABELS[sym] || sym; }
