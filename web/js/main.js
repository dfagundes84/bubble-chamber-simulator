import { api } from "./api.js";
import { ChamberRenderer, symbolLabel } from "./chamberRenderer.js";
import { MeasurementTool } from "./measurement.js";
import { ChartsPanel } from "./charts.js";
import { renderActivity } from "./activities.js";
import { renderParticleTable } from "./particleTable.js";

const SINGLE_TRACK_PARTICLES = ["p", "e-", "e+", "mu-", "mu+", "pi+", "pi-", "K+", "K-"];
const ELOSS_PARTICLES = ["e-", "e+", "mu-", "mu+", "pi+", "pi-", "p"];

const el = (id) => document.getElementById(id);

const state = {
  mode: "single",
  materials: [], particles: [], reactions: [],
  particleByKey: {},
};

const canvas = el("chamber-canvas");
const renderer = new ChamberRenderer(canvas);

function effectiveB() {
  return el("switch-row").querySelector('[data-switch="field"] input').checked
    ? parseFloat(el("bfield").value)
    : 0;
}

function readySwitches() {
  const q = (name) => el("switch-row").querySelector(`[data-switch="${name}"] input`).checked;
  return { power: q("power"), pressure: q("pressure"), temperature: q("temperature"), field: q("field") };
}

function updateSwitchAvailability() {
  const s = readySwitches();
  const deps = ["pressure", "temperature", "field"];
  for (const name of deps) {
    const wrap = el("switch-row").querySelector(`[data-switch="${name}"]`);
    wrap.style.opacity = s.power ? "1" : "0.35";
    wrap.querySelector("input").disabled = !s.power;
  }
  const canFire = s.power && s.pressure && s.temperature;
  el("fire-btn").disabled = !canFire;
  el("chamber-caption").textContent = canFire
    ? captionForMode(state.mode)
    : "Ligue Energia, Pressão e Superaquecimento para poder disparar o feixe.";
}

function captionForMode(mode) {
  switch (mode) {
    case "single": return "Traço único: ajuste momento e ângulo, então dispare o feixe.";
    case "energyloss": return "Baixo momento: observe o raio de curvatura encolher a cada volta.";
    case "pair": return "Produção de pares: ajuste Eγ e veja se o par é produzido.";
    case "cascade": return "Cascata completa: colisão inicial seguida da árvore de decaimentos.";
    default: return "";
  }
}

// ---------------------------------------------------------------- populate
async function populateSelectors() {
  const [particles, materials, reactions] = await Promise.all([
    api.particles(), api.materials(), api.reactions(),
  ]);
  state.particles = particles;
  state.materials = materials;
  state.reactions = reactions;
  state.particleByKey = Object.fromEntries(particles.map((p) => [p.symbol, p]));

  fillSelect(el("single-particle"), SINGLE_TRACK_PARTICLES.map((s) => [s, labelFor(s)]), "p");
  fillSelect(el("eloss-particle"), ELOSS_PARTICLES.map((s) => [s, labelFor(s)]), "e-");
  fillSelect(el("material-select"), materials.map((m) => [m.key, m.name_pt]), "h2_liquid");
  fillSelect(el("cascade-reaction"),
    [["random", "Aleatória (como no Gagnon 2011)"], ...reactions.map((r) => [r.id, r.label])],
    "random");
}

function labelFor(symbol) {
  const p = state.particleByKey[symbol];
  return p ? `${symbolLabel(symbol)} — ${p.name_pt}` : symbol;
}

function fillSelect(selectEl, pairs, defaultValue) {
  selectEl.innerHTML = "";
  for (const [value, label] of pairs) {
    const opt = document.createElement("option");
    opt.value = value; opt.textContent = label;
    selectEl.appendChild(opt);
  }
  if (defaultValue) selectEl.value = defaultValue;
}

// ---------------------------------------------------------------- HUD
function updateHud() {
  el("hud-B").textContent = `B = ${effectiveB().toFixed(2)} T`;
  const mat = state.materials.find((m) => m.key === el("material-select").value);
  el("hud-material").textContent = mat ? mat.name_pt : "—";
  let momentumText = "";
  if (state.mode === "single") momentumText = `p = ${parseFloat(el("single-momentum").value).toFixed(0)} MeV/c`;
  else if (state.mode === "energyloss") momentumText = `p = ${parseFloat(el("eloss-momentum").value).toFixed(0)} MeV/c`;
  else if (state.mode === "pair") momentumText = `Eγ = ${parseFloat(el("pair-energy").value).toFixed(1)} MeV`;
  else momentumText = `p = ${parseFloat(el("cascade-momentum").value).toFixed(1)} GeV/c`;
  el("hud-momentum").textContent = momentumText;
}

async function updatePairThreshold() {
  const materialKey = el("material-select").value;
  const t = await api.pairThresholdFor(materialKey);
  el("threshold-value").textContent = `${t.threshold_mev.toFixed(4)} MeV`;
}

// ---------------------------------------------------------------- mode switching
function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
  document.querySelectorAll(".mode-controls").forEach((div) => div.classList.add("hidden"));
  const map = { single: "controls-single", energyloss: "controls-energyloss", pair: "controls-pair", cascade: "controls-cascade" };
  el(map[mode]).classList.remove("hidden");
  renderActivity(mode, el("activity-text"));
  updateHud();
  updateSwitchAvailability();
  if (mode === "pair") updatePairThreshold();
}

// ---------------------------------------------------------------- firing
async function fireBeam() {
  const B = effectiveB();
  const materialKey = el("material-select").value;
  el("fire-btn").disabled = true;
  try {
    let data;
    if (state.mode === "single") {
      data = await api.eventSingle({
        particle_symbol: el("single-particle").value,
        momentum_mev: parseFloat(el("single-momentum").value),
        angle_deg: parseFloat(el("single-angle").value),
        B_tesla: B, material_key: materialKey,
      });
    } else if (state.mode === "energyloss") {
      data = await api.eventSingle({
        particle_symbol: el("eloss-particle").value,
        momentum_mev: parseFloat(el("eloss-momentum").value),
        angle_deg: 0, B_tesla: B, material_key: materialKey,
      });
    } else if (state.mode === "pair") {
      data = await api.eventPair({
        photon_energy_mev: parseFloat(el("pair-energy").value),
        B_tesla: B, material_key: materialKey,
      });
    } else {
      data = await api.eventCascade({
        reaction_id: el("cascade-reaction").value,
        beam_momentum_gev: parseFloat(el("cascade-momentum").value),
        B_tesla: B, material_key: materialKey,
      });
    }
    renderer.setEvent(data);
    renderEventInfo(data);
  } catch (err) {
    el("event-info").textContent = "Erro ao gerar evento: " + err.message;
  } finally {
    updateSwitchAvailability();
  }
}

function renderEventInfo(data) {
  const box = el("event-info");
  box.innerHTML = "";

  if (state.mode === "pair") {
    const rows = [
      ["Eγ", `${data.photon_energy_mev.toFixed(3)} MeV`],
      ["Limiar (Eq. 27)", `${data.threshold_mev.toFixed(4)} MeV`],
      ["Abaixo do limiar?", data.below_threshold ? "sim — par não produzido" : "não"],
    ];
    if (!data.below_threshold) {
      rows.push(["Massa invariante do par", `${data.pair_invariant_mass_mev.toFixed(3)} MeV/c²`]);
    }
    for (const [k, v] of rows) box.appendChild(rowEl(k, v));
  } else if (data.reaction_label) {
    box.appendChild(rowEl("Reação", data.reaction_label));
  }

  const list = document.createElement("div");
  list.style.marginTop = "8px";
  for (const t of data.tracks) {
    if (!t.visible && t.particle !== "gamma") continue;
    const row = document.createElement("div");
    row.className = "track-item";
    const dot = document.createElement("span");
    dot.className = "dot";
    dot.style.background = t.charge > 0 ? "var(--pos)" : t.charge < 0 ? "var(--neg)" : "var(--neutral)";
    row.appendChild(dot);
    const text = document.createElement("span");
    const pInfo = t.particle === "gamma"
      ? `E=${t.p_start_mev.toFixed(2)} MeV (${t.stop_reason === "converted" ? "converteu" : t.stop_reason === "below_threshold" ? "abaixo do limiar" : "saiu sem converter"})`
      : `${t.p_start_mev.toFixed(1)}→${t.p_end_mev.toFixed(1)} MeV/c${t.is_spiral ? " · espiral" : ""}`;
    text.textContent = `${symbolLabel(t.particle)} · ${pInfo}`;
    row.appendChild(text);
    list.appendChild(row);
  }
  box.appendChild(list);
}

function rowEl(k, v) {
  const row = document.createElement("div");
  row.className = "row";
  row.innerHTML = `<span>${k}</span><span>${v}</span>`;
  return row;
}

// ---------------------------------------------------------------- wiring
function wireControls() {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.dataset.mode));
  });

  el("switch-row").querySelectorAll("input").forEach((inp) => {
    inp.addEventListener("change", () => { updateSwitchAvailability(); updateHud(); });
  });

  el("fire-btn").addEventListener("click", fireBeam);
  el("clear-btn").addEventListener("click", () => {
    renderer.clear();
    el("event-info").textContent = "Nenhum evento gerado ainda.";
  });

  const rangeIds = [
    ["single-momentum", "single-momentum-value", (v) => `${Math.round(v)} MeV/c`],
    ["single-angle", "single-angle-value", (v) => `${Math.round(v)}°`],
    ["eloss-momentum", "eloss-momentum-value", (v) => `${Math.round(v)} MeV/c`],
    ["pair-energy", "pair-energy-value", (v) => `${v.toFixed(1)} MeV`],
    ["cascade-momentum", "cascade-momentum-value", (v) => `${v.toFixed(1)} GeV/c`],
    ["bfield", "bfield-value", (v) => `${v.toFixed(2)} T`],
  ];
  for (const [inputId, outId, fmt] of rangeIds) {
    const input = el(inputId);
    input.addEventListener("input", () => {
      el(outId).textContent = fmt(parseFloat(input.value));
      updateHud();
    });
  }

  el("material-select").addEventListener("change", () => {
    updateHud();
    if (state.mode === "pair") updatePairThreshold();
  });

  // opções de exibição
  const opts = {
    "opt-neutrals": "showNeutrals", "opt-labels": "showLabels",
    "opt-background": "showBackground", "opt-noise": "showNoise", "opt-colorcharge": "colorByCharge",
  };
  for (const [id, key] of Object.entries(opts)) {
    el(id).addEventListener("change", () => renderer.setOptions({ [key]: el(id).checked }));
    renderer.setOptions({ [key]: el(id).checked });
  }

  // medição
  const measureTool = new MeasurementTool({
    canvas, renderer, readoutEl: el("measure-readout"), textEl: el("measure-text"),
    getB: effectiveB,
  });
  el("measure-btn").addEventListener("click", () => {
    const active = !el("measure-btn").classList.contains("active");
    el("measure-btn").classList.toggle("active", active);
    measureTool.setActive(active);
  });

  // modais
  document.querySelectorAll("[data-open-modal]").forEach((btn) => {
    btn.addEventListener("click", () => openModal(btn.dataset.openModal));
  });
  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => { if (e.target === backdrop) closeModal(backdrop); });
    backdrop.querySelector("[data-close-modal]").addEventListener("click", () => closeModal(backdrop));
  });

  el("theme-toggle").addEventListener("click", () => {
    const cur = document.body.dataset.theme === "light" ? "dark" : "light";
    document.body.dataset.theme = cur;
    try { localStorage.setItem("bcs_theme", cur); } catch { /* ignore */ }
  });
  try {
    const saved = localStorage.getItem("bcs_theme");
    if (saved) document.body.dataset.theme = saved;
  } catch { /* ignore */ }
}

let chartsPanel = null;
function openModal(id) {
  el(id).classList.remove("hidden");
  if (id === "modal-particles") {
    renderParticleTable(state.particles, document.querySelector("#particle-table tbody"), el("particle-search"));
  }
  if (id === "modal-charts") {
    if (!chartsPanel) {
      chartsPanel = new ChartsPanel({
        dedxCanvas: el("chart-dedx"), thresholdCanvas: el("chart-threshold"),
        materialChecksEl: el("dedx-material-checks"), materials: state.materials,
      });
      chartsPanel.refreshDedx();
      document.querySelectorAll(".chart-tab").forEach((tab) => {
        tab.addEventListener("click", () => {
          document.querySelectorAll(".chart-tab").forEach((t) => t.classList.remove("active"));
          tab.classList.add("active");
          const which = tab.dataset.chart;
          el("chart-dedx-panel").classList.toggle("hidden", which !== "dedx");
          el("chart-threshold-panel").classList.toggle("hidden", which !== "threshold");
          if (which === "threshold" && !chartsPanel.thresholdChart) chartsPanel.refreshThreshold();
        });
      });
    }
  }
}
function closeModal(backdrop) { backdrop.classList.add("hidden"); }

// ---------------------------------------------------------------- boot
async function boot() {
  await populateSelectors();
  wireControls();
  setMode("single");
  updateHud();
  updateSwitchAvailability();
  // dispara um evento de demonstração ao carregar
  fireBeam();
}

boot().catch((err) => {
  console.error(err);
  el("chamber-caption").textContent = "Falha ao carregar o simulador: " + err.message;
});
