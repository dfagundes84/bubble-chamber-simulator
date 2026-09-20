// Textos do roteiro guiado, ancorados nas três atividades discutidas no
// artigo à RBEF (Seção III) e ampliados para o "modo cascata" inspirado em
// Gagnon (2011).

const CONTENT = {
  single: {
    title: "Atividade 1 — Movimento circular e curvatura",
    body: `
      <p>Uma partícula carregada em campo magnético uniforme percorre um círculo com
      raio <em>R = p⊥ / (|q| B)</em> — Eq. (16) do artigo. Como a força magnética não
      realiza trabalho, o módulo do momento não muda: o traço é um círculo perfeito
      (na ausência de perda de energia).</p>
      <ul>
        <li>Aumente <strong>B</strong> e observe o raio encolher.</li>
        <li>Aumente o <strong>momento</strong> e observe o raio crescer — traços quase
        retilíneos correspondem a momento muito alto (como o feixe de prótons de
        24 GeV/c do PS do CERN).</li>
        <li>Desligue a chave <strong>Campo B</strong>: sem campo, não há força magnética
        e a trajetória é reta.</li>
      </ul>
      <div class="q">
        <strong>Para pensar:</strong> use a régua virtual (📐 Medir traço) para estimar R
        e compare o momento medido com o valor real mostrado em "Evento atual".
      </div>`,
  },
  energyloss: {
    title: "Atividade 2 — Perda de energia por ionização",
    body: `
      <p>A fórmula de Bethe-Bloch (Eq. 29) descreve a perda média de energia por
      ionização. Como p = |q|BR, uma partícula que perde momento ao atravessar o
      líquido tem seu raio de curvatura encolhendo continuamente — o traço, que
      começa circular, degenera numa <strong>espiral</strong> até colapsar.</p>
      <ul>
        <li>Escolha um <strong>elétron</strong> ou <strong>pósitron</strong> com poucos
        MeV/c: a espiral é bem visível porque a massa pequena faz β mudar rapidamente.</li>
        <li>Compare com um <strong>próton</strong> de mesmo momento: por ser ~1800× mais
        massivo, sua curvatura muda muito mais devagar (veja o gráfico de ⟨-dE/dx⟩ vs
        βγ, Fig. 3 do artigo, no menu "Gráficos").</li>
      </ul>
      <div class="q">
        <strong>Para pensar:</strong> por que o "mínimo de ionização" ocorre perto de
        βγ ≈ 3–4, e por que a curva volta a subir lentamente em altas energias
        (efeito relativístico, sem saturar como o "platô de Fermi")?
      </div>`,
  },
  pair: {
    title: "Atividade 3 — Limiar de produção de pares",
    body: `
      <p>Um fóton real isolado não pode se converter em e⁺e⁻ no vácuo — isso violaria
      a conservação de energia-momento (massa invariante nula vs. massa mínima
      2mₑc² do par). É o núcleo que absorve o recuo necessário. O limiar de energia é
      (Eq. 27): <br><code>(Eγ)mín = 2mₑc² (1 + mₑ/M_N)</code>.</p>
      <ul>
        <li>Reduza a <strong>energia do fóton</strong> abaixo do limiar mostrado: o
        evento não ocorre — o fóton atravessa a câmara sem deixar traço.</li>
        <li>Compare o limiar para diferentes núcleos-alvo (menu "Meio da câmara")
        no gráfico de limiar (menu "Gráficos"): quanto mais pesado o núcleo, mais
        próximo do limite ideal 2mₑc² = 1,022 MeV.</li>
      </ul>
      <div class="q">
        <strong>Para pensar:</strong> compare a curvatura do traço do elétron com a do
        pósitron. Ambos vêm de um vértice sem traço incidente — por quê?
      </div>`,
  },
  cascade: {
    title: "Modo cascata — reações e decaimentos (estilo Gagnon 2011)",
    body: `
      <p>Escolha uma reação π⁻/K⁻ + p e observe a cascata completa de decaimentos,
      gerada dinamicamente a partir da tabela de partículas (massa, carga, número
      bariônico, estranheza e vida média de cada partícula).</p>
      <ul>
        <li><strong>Cotovelos ("kinks")</strong>: mudança abrupta de curvatura — a
        partícula carregada decaiu, e ao menos um produto neutro (invisível) levou
        parte do momento.</li>
        <li><strong>"Vês"</strong>: um V formado por duas partículas de cargas opostas
        que nascem no mesmo ponto — assinatura do decaimento de uma partícula neutra
        (ex.: Λ → p + π⁻, K⁰ → π⁺ + π⁻) ou da conversão de um fóton (γ → e⁺e⁻).</li>
        <li>Ative "Traços neutros" para ver (tracejado) o caminho de fótons e
        nêutrons entre os vértices — eles não ionizam o líquido e por isso não
        aparecem nas fotografias reais.</li>
      </ul>
      <div class="q">
        <strong>Para pensar:</strong> em cada vértice, verifique se a soma das cargas
        antes e depois se conserva — e tente reconstruir a reação apenas a partir da
        topologia dos traços, como um físico faria com uma fotografia real.
      </div>`,
  },
};

const STORAGE_KEY = "bcs_activity_notes_v1";

function loadNotes() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); }
  catch { return {}; }
}
function saveNotes(notes) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(notes)); } catch { /* ignore */ }
}

export function renderActivity(mode, container) {
  const content = CONTENT[mode] || CONTENT.single;
  const notes = loadNotes();
  container.innerHTML = `
    <h3>${content.title}</h3>
    ${content.body}
    <div class="q">
      <strong>Minhas anotações</strong>
      <textarea placeholder="Registre observações, valores medidos, dúvidas…">${notes[mode] || ""}</textarea>
    </div>`;
  const ta = container.querySelector("textarea");
  ta.addEventListener("input", () => {
    const n = loadNotes();
    n[mode] = ta.value;
    saveNotes(n);
  });
}
