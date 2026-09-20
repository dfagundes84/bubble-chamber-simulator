# Roteiro de atividades — Simulador de Câmara de Bolhas (BCS)

Este roteiro é um documento independente do simulador, pensado para ser usado por professores e estudantes ao lado do aplicativo (`python run.py`). Ele reproduz, de forma expandida, as três atividades discutidas no artigo:

> D. A. Fagundes, *Investigando a produção de pares e⁺e⁻ por meio da análise de imagens de uma câmara de bolhas*, Revista Brasileira de Ensino de Física (submetido).

Para a fundamentação teórica completa (equações, dedução do limiar de produção de pares, Bethe-Bloch), consulte o artigo — este roteiro assume que ele já foi lido e foca no *uso do simulador*.

---

## Atividade 1 — Movimento circular e curvatura

**Aba do simulador:** *Traço único*

Uma partícula carregada em campo magnético uniforme percorre um círculo de raio `R = p⊥ / (|q| B)` (Eq. 16 do artigo). Como a força magnética não realiza trabalho, o módulo do momento não muda: o traço é um círculo perfeito na ausência de perda de energia.

**Roteiro sugerido:**

1. Com a partícula padrão (próton) e momento ≈ 1 GeV/c, aumente o campo **B** e observe o raio encolher.
2. Aumente o **momento** e observe o raio crescer — traços quase retilíneos correspondem a momento muito alto (como o feixe de prótons de 24 GeV/c do PS do CERN usado nas fotografias do artigo).
3. Desligue a chave **Campo B**: sem campo, não há força magnética e a trajetória é reta.
4. Use a ferramenta **Medir traço** (clique em 3 pontos sobre a curva) para estimar `R` e compare o momento medido com o valor real mostrado em "Evento atual".

**Para discutir:** por que o sentido da curvatura se inverte ao trocar o sinal da carga da partícula (compare próton e antipróton, ou e⁻ e e⁺)?

---

## Atividade 2 — Perda de energia por ionização

**Aba do simulador:** *Traço único* (mesma aba da Atividade 1 — reduza o momento)

A fórmula de Bethe-Bloch (Eq. 29 do artigo) descreve a perda média de energia por ionização. Como `p = |q|BR`, uma partícula que perde momento ao atravessar o líquido tem seu raio de curvatura encolhendo continuamente — o traço, que começa circular, degenera numa **espiral** até colapsar.

**Roteiro sugerido:**

1. Escolha um **elétron** ou **pósitron** e arraste o controle de momento para a extremidade inferior (poucos MeV/c): a espiral é bem visível porque a massa pequena faz β mudar rapidamente.
2. Compare com um **próton** de mesmo momento: por ser ≈ 1800× mais massivo, sua curvatura muda muito mais devagar.
3. Abra o gráfico de ⟨-dE/dx⟩ vs βγ (menu **Gráficos**, reprodução da Fig. 3 do artigo) e localize, para o material escolhido, a região de momento que você está explorando.

**Para discutir:** por que o "mínimo de ionização" ocorre perto de βγ ≈ 3–4, e por que a curva volta a subir lentamente em altas energias (efeito relativístico, sem saturar como o chamado "platô de Fermi")?

---

## Atividade 3 — Limiar de produção de pares

**Aba do simulador:** *Produção de pares*

Um fóton real isolado não pode se converter em e⁺e⁻ no vácuo — isso violaria a conservação de energia-momento (a massa invariante de um fóton real é nula, mas a massa mínima do par e⁺e⁻ é `2mₑc²`). É o núcleo que absorve o recuo necessário. O limiar de energia é (Eq. 27):

```
(Eγ)mín = 2mₑc² (1 + mₑ/M_N)
```

**Roteiro sugerido:**

1. Com o material padrão (hidrogênio líquido), reduza a **energia do fóton** abaixo do limiar mostrado no painel: o evento não ocorre — o fóton atravessa a câmara sem deixar traço.
2. Aumente a energia até pouco acima do limiar e dispare repetidamente: observe a assinatura de "V" formada pelo par, nascendo de um ponto sem traço incidente.
3. Troque o **meio da câmara** (menu de materiais) e compare o limiar para diferentes núcleos-alvo no gráfico de limiar (menu **Gráficos**): quanto mais pesado o núcleo, mais próximo do limite ideal `2mₑc² = 1,022 MeV`.

**Para discutir:** compare a curvatura do traço do elétron com a do pósitron. Ambos vêm de um vértice sem traço incidente visível — por quê?

---

## Atividade 4 — Cascata de reações (estilo Gagnon, 2011)

**Aba do simulador:** *Cascata*

Escolha uma reação π⁻/K⁻ + p e observe a cascata completa de decaimentos, gerada dinamicamente a partir da tabela de partículas (massa, carga, número bariônico, estranheza e vida média de cada partícula).

**Elementos a identificar numa fotografia (real ou simulada):**

- **Cotovelos ("kinks")** — mudança abrupta de curvatura: a partícula carregada decaiu, e ao menos um produto neutro (invisível) levou parte do momento.
- **"Vês"** — um V formado por duas partículas de cargas opostas que nascem no mesmo ponto: assinatura do decaimento de uma partícula neutra (ex.: Λ → p + π⁻, K⁰ → π⁺ + π⁻) ou da conversão de um fóton (γ → e⁺e⁻).
- **Traços neutros** (ative a opção "Traços neutros" para ver, tracejado, o caminho de fótons e nêutrons entre os vértices — eles não ionizam o líquido e por isso não aparecem nas fotografias reais).

**Roteiro sugerido:**

1. Gere uma reação e, sem olhar a legenda em "Evento atual", tente identificar visualmente: qual traço é o feixe? Onde ocorreu a colisão inicial? Há algum cotovelo ou "V"?
2. Em cada vértice, verifique se a soma das cargas antes e depois se conserva.
3. Tente reconstruir a reação apenas a partir da topologia dos traços, como um físico faria com uma fotografia real — depois confira com a legenda.

**Destaque histórico — a descoberta do Ω⁻:** selecione a reação `K⁻ + p → Ω⁻ + K⁺ + K⁰`, que reproduz a reação de produção usada por Barnes *et al.* na câmara de bolhas de 80 polegadas de Brookhaven em 1964 — a confirmação experimental que faltava para o modelo de quarks de Gell-Mann/Ne'eman (o "caminho óctuplo"), pois o Ω⁻ tinha estranheza −3 e massa previstas de antemão. Dispare a reação algumas vezes e observe a variedade de cadeias de decaimento (Ω⁻ → Λ + K⁻, cerca de 68% das vezes, ou Ω⁻ → Ξ⁰ + π⁻/Ξ⁻ + π⁰ no restante) — a identificação de 1964 dependeu exatamente de reconhecer essa cadeia específica numa única fotografia.

---

## Sugestões de avaliação

- Peça aos estudantes que registrem, para cada atividade, os valores medidos (raio, momento) e comparem com os valores "reais" mostrados pelo simulador — uma introdução concreta à propagação de incertezas de medida.
- Combine este roteiro com a leitura de fotografias reais da Câmara de Bolhas do CERN, disponibilizadas pelo S'Cool LAB (ver referências do artigo), pedindo que os mesmos critérios de identificação sejam aplicados às imagens autênticas.
