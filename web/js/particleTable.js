import { symbolLabel } from "./chamberRenderer.js";

function fmtLifetime(s) {
  if (s == null) return "estável";
  if (s >= 1) return `${s.toFixed(3)} s`;
  return `${s.toExponential(3)} s`;
}

export function renderParticleTable(particles, tbody, searchInput) {
  function draw(filter) {
    const f = (filter || "").toLowerCase();
    tbody.innerHTML = "";
    for (const p of particles) {
      const hay = `${p.symbol} ${p.name_pt}`.toLowerCase();
      if (f && !hay.includes(f)) continue;
      const tr = document.createElement("tr");
      const decays = p.decays.length
        ? p.decays.map((d) => `${(d.branching_ratio * 100).toFixed(1)}% ${d.label || d.daughters.join("+")}`).join("<br>")
        : "—";
      tr.innerHTML = `
        <td>${symbolLabel(p.symbol)} <span style="color:var(--text-faint)">(${p.name_pt})</span></td>
        <td>${p.mass_mev.toFixed(3)}</td>
        <td>${p.charge > 0 ? "+1" : p.charge < 0 ? "−1" : "0"}</td>
        <td>${p.baryon_number}</td>
        <td>${p.strangeness}</td>
        <td>${fmtLifetime(p.mean_lifetime_s)}</td>
        <td>${decays}</td>`;
      tbody.appendChild(tr);
    }
  }
  draw("");
  searchInput.addEventListener("input", () => draw(searchInput.value));
}
