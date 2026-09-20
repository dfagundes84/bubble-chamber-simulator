# BCS — Simulador de Câmara de Bolhas

Um simulador moderno de câmara de bolhas, construído para expandir os estudos propostos em

> D. A. Fagundes, *Investigando a produção de pares e⁺e⁻ por meio da análise de imagens de uma câmara de bolhas*, Revista Brasileira de Ensino de Física (submetido).

e inspirado no simulador clássico (Pascal/Delphi) de

> M. Gagnon, *A bubble chamber simulator: a new tool for the physics classroom*, Phys. Educ. **46**, 443 (2011).

Ele reconstrói as ideias dos dois trabalhos com física relativística de verdade (não apenas animações), controles interativos e um visual moderno — pensado tanto para a Educação Básica quanto para disciplinas de Física Moderna/Contemporânea no Ensino Superior (como o MNPEF, contexto original do artigo).

![status](https://img.shields.io/badge/status-funcional-brightgreen)

## O que o simulador faz

| Aba do simulador | Física envolvida | Seção do artigo |
|---|---|---|
| **Traço único** | Movimento circular relativístico em campo magnético uniforme (`p⊥ = 0,3 B R`); em baixo momento, a perda de energia por ionização (Bethe-Bloch) faz o traço colapsar em espiral; opcionalmente, um espalhamento elástico único com um elétron ou próton do meio (raio-delta/recuo de núcleo) | Seções II.A e II.C |
| **Fóton na matéria** | Acima do limiar, produção de pares `γ + N → e⁺ + e⁻ + N`, `(Eγ)mín = 2mₑc²(1+mₑ/M_N)`; abaixo dele, espalhamento Compton `γ + e⁻ → γ' + e⁻'` | Seção II.B |
| **Cascata** | 9 reações π⁻/K⁻ + p — 8 inspiradas em Gagnon (2011) + a descoberta histórica do Ω⁻ (BNL 1964) —, com árvore de decaimentos gerada dinamicamente (conservação de carga, número bariônico e estranheza); traços de feixe que podem sofrer espalhamento elástico, e fótons secundários (ex.: de π⁰ → γγ) que podem converter ou Comptonizar | — |

Além disso: régua virtual de medição (ajuste de círculo por 3 cliques → raio → momento), tabela de partículas pesquisável, gráficos interativos (reprodução da Fig. 3 do artigo e da curva de limiar das Eqs. 27–28), e um "console" de chaves (energia/pressão/superaquecimento/campo) no espírito do simulador original de Gagnon.

O feixe de prótons real usado nas fotografias do CERN (24 GeV/c, ver referência do S'Cool LAB abaixo) raramente colide de frente — na maior parte das vezes ele apenas ioniza o líquido continuamente, e ocasionalmente espalha elasticamente com um elétron (raio-delta) ou um próton do meio, ou gera um fóton secundário que converte em par ou Comptoniza. O simulador reproduz essas quatro assinaturas (elétron, próton, "elétron de Compton" e pósitron) da Atividade 3 do roteiro do S'Cool LAB, tanto isoladamente (modo "Traço único"/"Fóton na matéria") quanto entremeadas nos traços de fundo do modo "Cascata".

A interface é deliberadamente enxuta: poucos controles, porém robustos, focados em trajetórias, processos e medidas. O roteiro didático de atividades (com sugestões de uso em sala, perguntas para discussão e avaliação) vive como documento independente em [`docs/roteiro_atividades.md`](docs/roteiro_atividades.md), para não competir por espaço com os controles do simulador.

## Arquitetura e escolha de linguagem

O projeto foi pensado em duas camadas propositalmente independentes:

- **`bcs/`** — núcleo de física em **Python puro** (sem nenhuma dependência de interface gráfica: `stdlib` apenas). Contém toda a cinemática relativística, a fórmula de Bethe-Bloch, a cinemática de produção de pares, a tabela de partículas e o gerador de eventos. É importável diretamente em um notebook Jupyter (veja `notebooks/`) para estender os estudos do artigo sem tocar em nenhuma linha de interface.
- **`server/` + `web/`** — a interface: um servidor **FastAPI** (Python) expõe o núcleo de física como uma API HTTP, e uma página web (**HTML/CSS/JavaScript puro**, sem framework) desenha a câmara em `<canvas>`, com animações e um painel de controle moderno.

Essa combinação (núcleo em Python + interface web) foi escolhida em vez de um app desktop (Qt/Tkinter) porque permite um visual muito mais rico e responsivo com bem menos código, roda em qualquer navegador (inclusive em tablets/Chromebooks de laboratório escolar) sem instalação de dependências gráficas nativas, e mantém o núcleo de física 100% reaproveitável em outros contextos (scripts, notebooks, testes automatizados). O Chart.js usado nos gráficos é servido localmente (`web/js/vendor/`), então o simulador funciona **offline** depois de instalado — importante para uso em sala de aula sem internet confiável.

```
bcs/            núcleo de física (puro Python, sem GUI)
  constants.py       constantes físicas e conversões de unidade (Tabela I do artigo)
  particles.py       tabela de partículas (massa, carga, B, S, vida média, decaimentos)
  materials.py        meios de detecção (H2 líquido, propano, He, C, Al, Fe, Sn, Pb)
  kinematics.py        quadrivetores, split relativístico de 2 corpos, MCU
  bethe_bloch.py       perda de energia por ionização (Eq. 29)
  pair_production.py    limiar e cinemática de γ + N -> e+ + e- + N (Eqs. 27-28)
  em_scattering.py       espalhamento elástico (raio-delta/recuo) e espalhamento Compton
  track_builder.py      integra trajetórias (curvatura + perda de energia -> espiral)
  reactions.py           catálogo de reações de colisão inicial (estilo Gagnon 2011 + Ω⁻)
  event.py                gerador de eventos: monta a árvore completa de decaimentos
  measurement.py          ajuste de círculo (régua virtual) e p = 0,3 B R

server/         API FastAPI (expõe bcs/ via HTTP)
web/            interface (HTML/CSS/JS vanilla + Chart.js local)
tests/          suíte de testes (pytest) do núcleo de física
notebooks/      exemplos de uso do núcleo em Jupyter, para expandir os estudos
docs/           roteiro didático de atividades (documento independente da interface)
run.py          ponto de entrada único (sobe o servidor e abre o navegador)
```

## Como instalar e rodar

Requer Python 3.10+.

```bash
cd "Bubble Chamber Simultor (BCS)"
python3 -m venv .venv && source .venv/bin/activate   # opcional mas recomendado
pip install -r requirements.txt
python run.py
```

O navegador abre automaticamente em `http://127.0.0.1:8000/`. Use `python run.py --port 8080` para outra porta, ou `--no-browser` para não abrir o navegador automaticamente.

> **Nota sobre `python3 -m venv`:** em algumas distribuições Linux (Debian/Ubuntu) o pacote `python3-venv` não vem instalado por padrão. Se o comando acima falhar com *"ensurepip is not available"*, rode primeiro `sudo apt install python3-venv` (uma única vez), ou instale as dependências diretamente com `pip install --user -r requirements.txt`.

### Testes

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Os testes verificam, entre outras coisas: a relação `p = 0,3 B R` (Eq. 17), a conservação de energia-momento em todo split relativístico de N corpos (2 ou mais — necessário para a reação de 3 corpos da descoberta do Ω⁻), a conservação de carga/número bariônico/estranheza em todas as reações de cascata (e nos decaimentos da tabela de partículas), o mínimo de ionização da curva de Bethe-Bloch (~4 MeV cm²/g para H₂ líquido, como na Fig. 3 do artigo), e a convergência do limiar de produção de pares ao valor sem recuo 2mₑc² (Eqs. 27–28).

### Notebook — expandindo os estudos do artigo

```bash
pip install -r requirements-dev.txt
jupyter notebook notebooks/expandindo_o_artigo.ipynb
```

O notebook reproduz a Figura 3 e a curva de limiar diretamente do pacote `bcs`, e propõe extensões concretas (distribuição de comprimento de decaimento, histogramas de momento a partir de amostras de eventos simulados, produção de múons e bárions estranhos a partir de decaimentos em cascata, metrologia da régua virtual) — ligadas explicitamente às sugestões de trabalhos futuros da Seção IV do artigo.

## Física implementada (resumo)

- **Cinemática relativística de 2 corpos** (colisões e decaimentos) via quadrivetores e a função de Källén, o mesmo formalismo de invariantes introduzido na Seção II.B.1 do artigo (equivalente às Eqs. 5–12 de Gagnon 2011, mas sem precisar resolver a equação quadrática em `p₁` explicitamente).
- **Movimento circular em campo magnético**: `p⊥ [GeV/c] ≈ 0,3 B[T] R[m]` (Eq. 17).
- **Perda de energia por ionização**: fórmula completa de Bethe-Bloch (Eq. 29), incluindo o termo de correção de densidade δ(βγ) via aproximação de Sternheimer-Peierls (a partir de `I`, `Z`, `A`, `ρ` do meio — sem depender de tabelas de parâmetros ajustados por elemento, o que é adequado para fins didáticos mas não tem precisão de metrologia).
- **Limiar de produção de pares** com correção de recuo do núcleo (Eqs. 27–28), incluindo a demonstração de por que um fóton isolado no vácuo não pode se converter (Seção II.B.2).
- **Espalhamento elástico (raio-delta/recuo de núcleo) e espalhamento Compton**: a energia transferida num espalhamento elástico feixe-alvo é amostrada da distribuição diferencial correta, dσ/dT ∝ 1/T² (Rutherford/Møller — o mesmo resultado por trás do termo T_max de Bethe-Bloch), invertida em forma fechada a partir do boost do referencial de centro de massa; a cinemática de Compton usa a fórmula fechada padrão. Ambos verificados por conservação exata de energia-momento (`bcs/em_scattering.py`).
- **Tabela de partículas real** (massas, vida média e canais de decaimento do PDG) com verificação automática, nos testes, de conservação de carga, número bariônico e estranheza.
- **Traços gerados por integração numérica** (curvatura + perda de energia acopladas passo a passo), não por animações pré-definidas — é por isso que, em baixo momento, o traço genuinamente colapsa em espiral, e por isso que desligar o campo produz uma reta perfeita.

## Limitações conhecidas (documentadas no próprio código)

- A cinemática é tratada em 2D (o plano da fotografia), como em Gagnon (2011) — eventos reais são 3D e precisam de duas vistas estereoscópicas para reconstrução completa (mencionado na Seção II.B.3 do artigo).
- O termo de correção de densidade de Bethe-Bloch usa a aproximação geral de Sternheimer-Peierls, não os parâmetros oficiais tabelados por elemento do PDG.
- A conversão de fótons (pair production) usa uma amostragem simplificada do comprimento de conversão (não o comprimento de radiação `X₀` do meio), e a escolha entre Compton e produção de pares usa uma probabilidade heurística em função da energia (não as seções de choque reais de Klein-Nishina/Bethe-Heitler).
- O ângulo de espalhamento Compton é amostrado uniformemente (não pela distribuição angular real de Klein-Nishina, que favorece ângulos pequenos em altas energias).
- Núcleos-alvo além do hidrogênio são aproximados por `M_N ≈ A × u` (ignorando o pequeno defeito de massa de ligação nuclear).

Essas simplificações são intencionais (mantêm o núcleo de física pequeno e didático) e estão documentadas como oportunidades de extensão nos comentários do código e no notebook.

## Créditos

- D. A. Fagundes, *Investigando a produção de pares e⁺e⁻ por meio da análise de imagens de uma câmara de bolhas*, RBEF (submetido) — fundamentação teórica e roteiro das três atividades.
- M. Gagnon, *A bubble chamber simulator: a new tool for the physics classroom*, Phys. Educ. **46**, 443 (2011) — inspiração original do simulador e de oito das nove reações de cascata.
- J. Woithe, R. Schmidt & F. Naumann, *Student worksheet: Bubble chamber pictures*, S'Cool LAB/CERN (2018) — fotografias históricas da Câmara de Bolhas de 2 m usadas como referência visual, e as quatro assinaturas de espalhamento (elétron, próton, "elétron de Compton", pósitron) reproduzidas nos modos "Traço único"/"Fóton na matéria"/"Cascata".
- Particle Data Group, *Phys. Rev. D* **110**, 030001 (2024) — massas, vidas médias e razões de ramificação das partículas.
- V. E. Barnes *et al.*, *Observation of a Hyperon with Strangeness Minus Three*, Phys. Rev. Lett. **12**, 204 (1964) — descoberta do Ω⁻, reproduzida na reação `k_omega_discovery`.
