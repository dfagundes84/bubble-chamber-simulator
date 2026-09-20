# Roadmap — DHEPS (Didactic High Energy Physics Simulator)

> **Status: apenas planejamento.** Nada neste documento foi implementado ainda — o
> projeto continua se chamando BCS, o repositório não foi renomeado, e nenhuma pasta
> nova (`ccs/`, `pa_fte/`, `pa_cmc/`) existe. Este documento registra as decisões de
> arquitetura já discutidas e aprovadas para quando essas fases forem priorizadas.

## Visão

O BCS (Bubble Chamber Simulator) atual se tornará o primeiro de quatro "ambientes"
sob um guarda-chuva chamado **DHEPS**, cada um cobrindo uma família diferente de
detectores/experimentos historicamente importantes para a física de partículas:

| Sigla | Nome | O que representa |
|---|---|---|
| **BCS** | Bubble Chamber Simulator | Câmara de bolhas (já existe) — feixe de acelerador contra alvo fixo dentro da própria câmara, fotografado como traços curvos num campo B. |
| **CCS** | Cloud Chamber Simulator | Câmara de nuvens — historicamente usada para raios cósmicos avulsos (não feixe de acelerador contínuo); mesmo princípio visual do BCS. |
| **PA-FTE** | Particle Accelerator — Fixed Target Experiment | Acelerador de alvo fixo — cinemática de limiar/produção, não fotografia de câmara. |
| **PA-CMC** | Particle Accelerator — Center-of-Momentum Collisions | Colisor (dois feixes, colisão simétrica no referencial do centro de momento) — cinemática de limiar/produção, não fotografia de câmara. |

## Decisões de arquitetura já confirmadas

1. **CCS reaproveita 100% o motor do BCS.** Fisicamente, câmaras de nuvens e de
   bolhas produzem o mesmo tipo de imagem — traços curvos num campo magnético — e só
   diferem no mecanismo de revelação (condensação de vapor supersaturado vs. ebulição
   de líquido superaquecido), que não afeta a cinemática de curvatura nem, em
   primeira ordem, a perda de energia por ionização já modelada em
   `bcs/bethe_bloch.py`. Portanto CCS não ganha um pacote de física próprio: reaproveita
   diretamente `bcs/track_builder.py`, `bcs/event.py` e `web/js/chamberRenderer.js`,
   mudando apenas:
   - material/meio padrão e tema visual (câmara de nuvens tende a ser clara,
     não verde-escura como a de líquido);
   - o catálogo de cenários: raios cósmicos avulsos (um único traço incidente, sem
     "feixe" contínuo) em vez de reações de acelerador.

2. **PA-FTE e PA-CMC não usam o paradigma de "foto de câmara".** Aceleradores reais
   não são fotografados como uma câmara de bolhas/nuvens — usam detectores
   eletrônicos (calorímetros, câmaras de fio, etc.). Representá-los como traços num
   canvas seria fisicamente desonesto. Em vez disso, esses dois ambientes usam um
   **painel de cinemática/limiar**: sliders de energia de feixe (ou das duas energias
   de feixe, no caso de PA-CMC), indicador de limiar produzido/não-produzido, gráfico
   de energia vs. limiar (no mesmo espírito do que já existe em `bcs/pair_production.py`
   e do gráfico de limiar já exposto em `/api/pair_threshold_curve`), e um diagrama
   esquemático simples do evento (não uma fotografia). Isso reaproveita diretamente
   `bcs/kinematics.py` (`kallen_momentum`, `two_body_split`, invariante de Mandelstam
   `s`), sem precisar de nenhuma física nova além do que já existe.

3. **Nome do repositório:** mantido como está por enquanto (`bubble-chamber-simulator`
   no GitHub). Renomear fica para quando houver pelo menos mais um ambiente pronto,
   para não trocar o link do repositório mais de uma vez.

## Candidatos a cenários históricos (por ambiente)

| Descoberta | Ano/experimento real | Ambiente proposto | Observação |
|---|---|---|---|
| Ω⁻ (estranheza −3) | Barnes *et al.*, BNL 1964, câmara de bolhas de 80" | **BCS** | ✅ Implementado (reação `k_omega_discovery`). |
| Pósitron | Anderson, 1932, câmara de nuvens + raio cósmico + chapa de chumbo | **CCS** | Precisa de uma funcionalidade nova no motor: uma placa absorvedora no meio da câmara (mudança abrupta de material ao longo do traço, para mostrar a perda de energia ao atravessar o chumbo — é assim que Anderson soube a direção de voo da partícula). Ainda não implementado. |
| Káons ("partículas V") | Rochester & Butler, 1947, câmara de nuvens | **CCS** (ou **BCS**, já parcialmente coberto pelas reações com K⁰/Λ existentes) | O BCS já mostra a assinatura de "V" característica (K⁰→π⁺π⁻, Λ→pπ⁻) nas reações existentes; um cenário CCS dedicado poderia enfatizar o contexto histórico de raio cósmico em vez de feixe de acelerador. |
| Antipróton | Segrè & Chamberlain, 1955, Bevatron (não foi fotografia de câmara) | **PA-FTE** | O limiar de `p + p → p + p + p + p̄` é um problema de cinemática de limiar quase idêntico em espírito ao já implementado para produção de pares — reaproveita diretamente `kallen_momentum`/Mandelstam `s`. |
| Píon carregado | Powell, 1947, emulsão nuclear (nem câmara de bolhas nem de nuvens) | **PA-FTE** (produção, não descoberta original) | A descoberta original não usou câmara nem acelerador — foi emulsão fotográfica exposta a raios cósmicos em altitude. Historicamente desalinhado com qualquer um dos 4 ambientes propostos; melhor tratado como um cenário de *produção* de píons num acelerador de alvo fixo (como de fato ocorreu depois, em 1948, em Berkeley) do que como uma "descoberta" fiel. |

## Próximos passos (não iniciados)

Nenhum código de CCS, PA-FTE ou PA-CMC existe ainda. Quando uma dessas fases for
priorizada, um novo ciclo de planejamento (plan mode) deve detalhar, por fase:

- **CCS**: novo `chamber` "tema" (paleta de cores clara, material padrão "ar"), a
  funcionalidade de placa absorvedora em `bcs/track_builder.py`/`bcs/event.py`, e o
  cenário da descoberta do pósitron.
- **PA-FTE**: o painel de cinemática de limiar (novo componente de UI, reaproveitando
  `kinematics.py`), começando pelo antipróton.
- **PA-CMC**: o mesmo painel, mas para colisões simétricas de dois feixes — precisa
  de uma pequena extensão em `kinematics.py` para montar o quadrimomento total a
  partir de dois feixes não-colineares (hoje `generate_cascade_event` assume sempre
  um alvo em repouso).
- **Rebranding**: só depois de pelo menos um desses ambientes estar funcional —
  renomear pasta/repositório/README para refletir o guarda-chuva DHEPS, com um
  seletor de ambiente na tela inicial da interface web.
