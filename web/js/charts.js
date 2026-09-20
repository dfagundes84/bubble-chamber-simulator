import { api } from "./api.js?v=2";

const MATERIAL_COLORS = ["#43e6b5", "#ff9457", "#57b8ff", "#ffd76a", "#ff6bd6", "#9d7bff", "#7fd858", "#ff6b6b"];

function cssVar(name) {
  return getComputedStyle(document.body).getPropertyValue(name).trim() || "#e9edf2";
}

function baseGridColor() { return "rgba(154,167,184,0.18)"; }
function baseTextColor() { return cssVar("--text-dim"); }

export class ChartsPanel {
  constructor({ dedxCanvas, thresholdCanvas, materialChecksEl, materials }) {
    this.dedxCanvas = dedxCanvas;
    this.thresholdCanvas = thresholdCanvas;
    this.materials = materials;
    this.selectedMaterials = new Set(["h2_liquid", "lead"]);
    this.dedxChart = null;
    this.thresholdChart = null;
    this._buildMaterialChips(materialChecksEl);
  }

  _buildMaterialChips(container) {
    container.innerHTML = "";
    this.materials.forEach((m, i) => {
      const chip = document.createElement("button");
      chip.className = "chip" + (this.selectedMaterials.has(m.key) ? " active" : "");
      chip.textContent = m.name_pt;
      chip.dataset.key = m.key;
      chip.addEventListener("click", () => {
        if (this.selectedMaterials.has(m.key)) this.selectedMaterials.delete(m.key);
        else this.selectedMaterials.add(m.key);
        chip.classList.toggle("active");
        this.refreshDedx();
      });
      container.appendChild(chip);
    });
  }

  async refreshDedx() {
    const keys = [...this.selectedMaterials];
    if (keys.length === 0) return;
    const data = await api.dedxCurve({ material_keys: keys, n_points: 220 });
    const datasets = keys.map((key, i) => {
      const curve = data[key];
      const mat = this.materials.find((m) => m.key === key);
      return {
        label: mat ? mat.name_pt : key,
        data: curve.beta_gamma.map((bg, idx) => ({ x: bg, y: curve.dedx_mev_cm2_g[idx] })),
        borderColor: MATERIAL_COLORS[i % MATERIAL_COLORS.length],
        backgroundColor: "transparent",
        borderWidth: 2, pointRadius: 0, tension: 0.15,
      };
    });

    if (this.dedxChart) this.dedxChart.destroy();
    this.dedxChart = new Chart(this.dedxCanvas.getContext("2d"), {
      type: "line",
      data: { datasets },
      options: {
        responsive: true, animation: false,
        scales: {
          x: {
            type: "logarithmic", title: { display: true, text: "βγ = p/Mc", color: baseTextColor() },
            grid: { color: baseGridColor() }, ticks: { color: baseTextColor() },
          },
          y: {
            type: "logarithmic",
            title: { display: true, text: "⟨-dE/dx⟩ (MeV cm² g⁻¹)", color: baseTextColor() },
            grid: { color: baseGridColor() }, ticks: { color: baseTextColor() },
          },
        },
        plugins: {
          legend: { labels: { color: baseTextColor(), font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: βγ=${ctx.parsed.x.toFixed(2)}, ⟨-dE/dx⟩=${ctx.parsed.y.toFixed(3)}`,
            },
          },
        },
      },
    });
  }

  async refreshThreshold() {
    const data = await api.pairThresholdCurve({ n_points: 200 });
    if (this.thresholdChart) this.thresholdChart.destroy();
    this.thresholdChart = new Chart(this.thresholdCanvas.getContext("2d"), {
      type: "line",
      data: {
        datasets: [
          {
            label: "(Eγ)mín (Eq. 27, com recuo do núcleo)",
            data: data.nucleus_mass_mev.map((m, i) => ({ x: m, y: data.threshold_mev[i] })),
            borderColor: "#43e6b5", backgroundColor: "transparent", borderWidth: 2.2, pointRadius: 0,
          },
          {
            label: "limite sem recuo, 2mₑc² = 1,022 MeV (Eq. 28)",
            data: data.nucleus_mass_mev.map((m) => ({ x: m, y: data.no_recoil_limit_mev })),
            borderColor: "#ffd76a", borderDash: [6, 4], backgroundColor: "transparent",
            borderWidth: 1.6, pointRadius: 0,
          },
        ],
      },
      options: {
        responsive: true, animation: false,
        scales: {
          x: { type: "logarithmic", title: { display: true, text: "M_N (MeV/c²)", color: baseTextColor() },
               grid: { color: baseGridColor() }, ticks: { color: baseTextColor() } },
          y: { title: { display: true, text: "(Eγ)mín (MeV)", color: baseTextColor() },
               grid: { color: baseGridColor() }, ticks: { color: baseTextColor() } },
        },
        plugins: { legend: { labels: { color: baseTextColor(), font: { size: 11 } } } },
      },
    });
  }
}
