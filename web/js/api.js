const BASE = "/api";

async function postJSON(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${path} -> HTTP ${res.status}: ${detail}`);
  }
  return res.json();
}

async function getJSON(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} -> HTTP ${res.status}`);
  return res.json();
}

export const api = {
  particles: () => getJSON("/particles"),
  materials: () => getJSON("/materials"),
  reactions: () => getJSON("/reactions"),
  eventCascade: (body) => postJSON("/event/cascade", body),
  eventSingle: (body) => postJSON("/event/single", body),
  eventPair: (body) => postJSON("/event/pair", body),
  dedxCurve: (body) => postJSON("/dedx_curve", body),
  pairThresholdCurve: (body) => postJSON("/pair_threshold_curve", body),
  pairThresholdFor: (materialKey) => getJSON(`/pair_threshold/${materialKey}`),
  measure: (body) => postJSON("/measure", body),
};
