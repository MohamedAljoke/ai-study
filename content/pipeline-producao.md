# Pipeline de produção de vídeo — "Architect in Progress"

Documento do fluxo que quero padronizar: **roteiro aprovado → áudio → cenas ancoradas no
áudio → montagem → thumbnail**.

Isso é um software por si só. Por enquanto é ferramenta interna pra me ajudar a produzir; em
algum momento pode virar conteúdo (ou produto). Não é prioridade sobre o site — ver
`VISION.md`.

> **Este documento é o desenho.** A implementação vive em [`studio/`](../studio/README.md), e o
> plano de construção dividido em sprints está em [`studio/docs/`](../studio/docs/README.md).

---

## O fluxo

```
1. ROTEIRO      script.md aprovado, com marcadores de cena embutidos
                     ↓
2. ÁUDIO        eu leio em voz alta → narration.wav
                     ↓
3. ALINHAMENTO  script + áudio → timestamp de cada palavra
                     ↓
4. TIMELINE     marcadores + timestamps → timeline.json (cena X entra em 04:12.3)
                     ↓
5. ASSETS       gerar cada cena (terminal, código, replay, tela, card)
                     ↓
6. MONTAGEM     timeline.json + assets + áudio → video.mp4
                     ↓
7. THUMB        template HTML + cores da marca → thumb.png 1280x720
                     ↓
8. DERIVADOS    ├─ shorts: cortes verticais 9:16, já marcados no roteiro
                └─ blog: artigo escrito, mesmo assunto, texto de leitura
                     ↓
9. PUBLICAÇÃO   capítulos, descrição, tags
```

**Um roteiro aprovado gera quatro coisas:** o vídeo longo, N shorts, um post de blog e a
thumb. Os shorts saem do *mesmo* áudio e das *mesmas* cenas — custo marginal quase zero. O
blog **não** sai do áudio; sai do mesmo material de origem, escrito do zero pra ser lido.

**A ideia central:** eu nunca marco tempo na mão. Eu marco **posição no texto**; o alinhamento
converte posição em tempo. Se eu regravar o áudio mais devagar, todos os tempos se
recalculam sozinhos e a montagem continua sincronizada.

---

## Divisão de trabalho — o que é meu, o que é da máquina

Este é o objetivo do projeto inteiro. **Automatizar o máximo possível**, e o que sobrar pra
mim tem que ser só a parte que exige julgamento ou minha voz.

### Sempre meu (não automatizar, nem tentar)

1. **Revisar e aprovar o roteiro.** A IA rascunha, eu decido. É onde o vídeo é bom ou ruim.
2. **Ler em voz alta.** É o canal.
3. **Gravar as cenas que não dá pra scriptar** — navegador, editor, minha cara. O objetivo é
   que isso seja a **minoria** das cenas.

### Sempre da máquina

Alinhamento, cálculo de tempos, cenas de terminal, cenas de código, animações de algoritmo,
replays, cards, montagem, legendas, thumb, corte de shorts, capítulos, descrição, tags.

### O alvo

> Depois de aprovar o roteiro e gravar o áudio, **um comando** produz o `video.mp4`, os
> shorts, as legendas, a thumb e os metadados — prontos pra publicar. Eu só assisto e
> aprovo.

Nem tudo chega lá de primeira. Mas toda decisão do pipeline se resolve por essa pergunta:
*isso me obriga a fazer trabalho manual repetido?* Se obriga, está errado.

### Escopo agora

**Foco: gerar o vídeo e o conteúdo de YouTube.** Fora de escopo por enquanto: publicar
sozinho (upload na API do YouTube) e automatizar o blog. Eu subo na mão; o pipeline só
precisa **entregar os arquivos prontos**. Automatizar upload é fácil e vem depois — o valor
está antes dele.

---

## Etapa 1 — Roteiro com marcadores

O roteiro continua sendo um `.md` legível (ver `studio/videos/01-batalha-naval/script.md`). Os
marcadores são comentários HTML — não aparecem na renderização, não atrapalham a leitura.

```markdown
<!-- cena: terminal id=play-demo fonte=tapes/play.tape -->
> Loop clássico: pergunta, lê, valida, repete.

<!-- cena: codigo id=parse-position arquivo=internal/game/position.go linhas=12-28 -->
> Repara numa coisa: quase todo o meu `main.go` é conversa com humano.

<!-- cena: replay id=density-vs-hunt estrategias=hunt,density -->
> Pra cada casa, conto de quantas maneiras os navios caberiam ali.
```

**Marcador de short** — delimita um trecho que se sustenta sozinho, com abre e fecha:

```markdown
<!-- short: inicio id=uma-linha titulo="Uma linha, 15 tiros a menos" -->
> O menor navio ocupa duas casas. Então qualquer navio cobre pelo menos uma casa preta...
> ...uma linha de código e uma ideia.
<!-- short: fim id=uma-linha -->
```

Regras:

- O marcador vale **a partir da primeira palavra do parágrafo seguinte**, até o próximo
  marcador.
- Marcadores de `short` são **independentes** dos de `cena` e podem se sobrepor a eles —
  um short pode atravessar duas cenas ou pegar metade de uma.
- `id` é único no vídeo e vira o nome do arquivo do asset.
- Texto em `>` é o que eu leio. O resto do `.md` (títulos, notas de produção, tabelas) é para
  mim e **não entra** no áudio nem no alinhamento.

Antes de gravar, um passo `extrair-narracao` produz `narration.txt` — só as linhas `>`,
limpas de markdown. Esse é o texto que eu leio **e** o texto que o alinhador recebe. Os dois
sendo o mesmo arquivo é o que faz o alinhamento ser confiável.

---

## Etapa 2 — Áudio

Eu leio. Sem TTS no que vai ao ar: o canal é primeira pessoa, sobre coisa que eu fiz, e voz
sintética mata isso. (TTS só faria sentido para versão em inglês do mesmo roteiro — fica pra
depois.)

Existe uma exceção que não é exceção: `studio duble` sintetiza uma voz temporária a partir do
mesmo `narration.txt`, só pra eu conseguir escrever e testar o resto do pipeline antes de
gravar. Ela vive em `build/`, é descartável, e a minha gravação sempre ganha dela.

| Coisa | Recomendação |
|---|---|
| Gravar | Qualquer DAW ou o próprio OBS em faixa separada. Audacity resolve. |
| Limpar | **Auphonic** (nivelamento + ruído + loudness, ~1 clique) ou `ffmpeg` + `arnndn` se quiser local e de graça |
| Alvo | **-16 LUFS**, mono, 48kHz WAV — padrão de voz pra YouTube |

Erro de leitura: repito a frase e sigo. No corte, deleto a tomada ruim **antes** do
alinhamento — o alinhador espera que áudio e texto batam.

---

## Etapa 3 — Alinhamento (a peça técnica que segura tudo)

Isso é **forced alignment**, não transcrição. Eu já sei o texto; quero saber *quando* cada
palavra foi dita. Isso é bem mais preciso do que transcrever e torcer.

| Ferramenta | Nota |
|---|---|
| **WhisperX** | **Recomendado.** Timestamp por palavra, modelo pt, roda local na GPU/CPU, saída JSON limpa. Aceita `initial_prompt` mas o valor está no alinhamento em si. |
| aeneas | Feito exatamente pra sincronizar texto+áudio (nasceu de audiobook). Mais leve, menos manutenção ativa. |
| stable-ts | Wrapper de Whisper com timestamps melhores. Alternativa simples. |
| Montreal Forced Aligner | Mais acadêmico/preciso, mais chato de instalar. Exagero aqui. |

Saída esperada:

```json
{"word": "parity", "start": 623.41, "end": 623.88}
```

De posse disso, cada marcador do roteiro vira um tempo: acha a primeira palavra do parágrafo
seguinte ao marcador, pega seu `start`. Fim da cena = `start` do próximo marcador.

**Cuidado conhecido:** termos técnicos em inglês no meio do português (`stdout`, `benchmark`,
`WebSocket`) são onde o alinhador erra. Se o desvio incomodar, a saída tem um passo de
revisão manual — o `timeline.json` é editável à mão, é só um arquivo.

---

## Etapa 4 — Timeline

Artefato central. Tudo depois disso só consome ele.

```json
{
  "video": "01-batalha-naval",
  "audio": "build/01/narration.wav",
  "duracao": 1082.4,
  "cenas": [
    { "id": "play-demo", "tipo": "terminal", "inicio": 180.2, "fim": 300.7,
      "fonte": "tapes/play.tape", "asset": "build/01/assets/play-demo.mp4" },
    { "id": "parse-position", "tipo": "codigo", "inicio": 300.7, "fim": 318.0,
      "arquivo": "internal/game/position.go", "linhas": [12, 28] }
  ]
}
```

Se uma cena é mais curta que o trecho de narração, o vídeo segura o último frame. Se for mais
longa, corta ou dá slow-down — decisão por tipo de cena, configurável.

---

## Etapa 5 — Gerar os assets

O ponto forte de fazer isso com código: **as cenas são determinísticas e regeneráveis**. Mudou
o código do jogo? Roda o pipeline de novo e os vídeos de terminal se atualizam sem eu
regravar tela.

| Tipo de cena | Ferramenta | Por quê |
|---|---|---|
| `terminal` | **VHS** (charmbracelet) | Um `.tape` descreve o que digitar e o timing; sai MP4/GIF idêntico toda vez. Fim de regravar terminal. |
| `codigo` | **freeze** (charmbracelet) ou silicon | Snippet → PNG bonito, via CLI. Aponta arquivo + linhas, sem screenshot manual. |
| `replay` | ferramenta Go própria | `internal/replay` já grava snapshot tiro a tiro. Renderizar pra frames → `ffmpeg`. É o visual que segura o vídeo 01. |
| `manim` | **Manim Community** | Animação explicando o algoritmo — o mapa de probabilidade da `density`, a prova do `parity`. Ver seção própria abaixo. |
| `tela` | **OBS** | Navegador, editor, coisas que não dá pra scriptar. |
| `card` | HTML + Playwright | Tabelas, títulos de bloco, o "95 → 44". Mesmo template da thumb. |
| `diagrama` | Mermaid ou Excalidraw | Árvore de pastas, fluxo. |

**VHS e freeze são o maior ganho de tempo do pipeline inteiro.** Vale começar por eles.

---

## Etapa 5b — Animações de algoritmo (Manim)

Usar **Manim Community** (`manim`, a versão mantida pela comunidade — não o `manimgl` pessoal
do Grant Sanderson). É Python, é o que faz as animações do 3Blue1Brown, e resolve exatamente o
tipo de cena que eu mais preciso: **explicar visualmente o que o código está fazendo**.

Casos concretos no vídeo 01:

- `density`: mostrar o tabuleiro virando um mapa de calor de probabilidade, os números
  aparecendo casa a casa, e o tiro indo na casa mais quente.
- `parity`: o tabuleiro de xadrez sobrepondo o grid, um navio de 2 casas deslizando por cima
  e sempre cobrindo uma casa preta. É a prova visual, e ela vale mais que a explicação falada.
- `hunt`: a fila de vizinhos crescendo e sendo consumida.

### O truque: animar dados reais, não desenho

Esta é a parte que faz diferença e que eu não quero perder de vista.

O jeito preguiçoso é desenhar uma animação *ilustrando* o algoritmo. O jeito certo é a
animação **consumir a saída do código de verdade**:

```
Go: roda uma partida, exporta por turno o score de cada casa  →  density.json
                                    ↓
Manim: lê o JSON e anima exatamente aquilo
```

Assim o mapa de calor na tela é **o mapa que o `density.go` calculou**, não uma aproximação
que eu fiz pra ficar bonito. Se eu mudar o `hitWeight` no Go, a animação muda junto.

Isso exige um passo pequeno no lado Go: um modo de export que serializa `d.score` a cada
turno. Barato, e vira também o material do post de blog.

E tem um bônus temático: o vídeo fala sobre separar domínio de apresentação, e a animação é
mais uma casca lendo o mesmo motor. Dá pra falar isso em voz alta no vídeo.

### Como automatizar sem virar armadilha

Gerar código Manim do zero com LLM a cada cena **não funciona bem** — sai animação que não
renderiza, ou que renderiza feia, e eu perco mais tempo depurando Python do que teria perdido
animando. O padrão que funciona:

1. **Uma pequena biblioteca de cenas parametrizadas, escrita à mão e reusável:**
   `GridBoard`, `HeatMap(dados)`, `ShipOverlay`, `ShotSequence(replay)`. Escrevo uma vez,
   uso em todo vídeo.
2. **O marcador do roteiro só escolhe e configura:**
   ```markdown
   <!-- cena: manim id=density-mapa classe=HeatMap dados=build/01/density.json turnos=1-12 -->
   ```
3. **A IA compõe, não inventa.** Quando precisar de cena nova, o LLM monta a partir das
   classes existentes — contexto pequeno, resultado previsível. Cena realmente nova eu
   escrevo e ela entra na biblioteca.

Ou seja: o investimento é na biblioteca, não em prompt. Ela cresce a cada vídeo e o custo por
animação cai.

### Prático

- Render é **lento** (minutos por cena). Usar `-ql` (baixa qualidade) enquanto edito e `-qh`
  só no render final. Cachear por hash da entrada: se o JSON e os parâmetros não mudaram, não
  re-renderiza.
- Cores da marca no Manim: fundo `#122440`, elementos `#FFFFFF`, destaque `#FFB020`. Definir
  um `manim.cfg` do canal pra nunca sair do padrão.
- Manim sai transparente (`-t`) se eu quiser compor com outra coisa por cima.
- Renderizar em 1080x1920 também, pros shorts — a animação do `parity` é o melhor short do
  lote e merece layout vertical próprio, não crop.

---

## Etapa 6 — Montagem

Duas rotas. Recomendo começar pela primeira e mudar se apertar.

**A) `ffmpeg` direto a partir do `timeline.json`** — script gera a lista de filtros/concat e
renderiza. Sem interação, roda em CI, reprodutível. Bom enquanto o vídeo for "narração +
tela cheia + cards". É o caso hoje.

**B) Gerar projeto de NLE em vez de vídeo final** — o script emite **OpenTimelineIO** →
exporta pra DaVinci Resolve (gratuito, tem API Python). Aí eu abro com tudo já posicionado e
só ajusto o que quiser. Mais trabalhoso de montar, mas devolve controle fino sem perder a
automação.

Regra prática: **A** até a montagem começar a doer, aí **B**.

Legendas saem de graça — o alinhamento da etapa 3 já é um `.srt`/`.vtt`.

---

## Etapa 7 — Thumbnail

**Não usar geração de imagem por IA.** Thumb é 80% texto grande, e modelo de imagem escreve
texto mal. Template HTML + screenshot é determinístico, versionável e bate a marca sempre.

Stack: um `thumb.html` com CSS + variáveis por vídeo → **Playwright** tira screenshot em
1280x720 → PNG.

### Cores da marca (extraídas do banner do canal)

| Uso | Hex |
|---|---|
| Fundo / navy | `#122440` |
| Texto / logo | `#FFFFFF` |
| Fundo alternativo (mais claro, pra profundidade) | `#1B3157` |
| **Acento** (sugestão — o banner não tem) | `#FFB020` âmbar |

O banner é navy + branco, só. Isso é elegante mas **fraco em thumbnail** — precisa de um
ponto de tensão. Sugestão: um acento âmbar usado **só no número/palavra-chave** (`95 → 44`,
`1 LINHA`), nunca em mais de um elemento. Mantém a identidade e dá o contraste que a
miniatura precisa.

Elementos fixos do template: logo (triângulo de 3 círculos) num canto, faixa navy, título em
2–4 palavras, sans-serif pesada (Inter/Archivo Black/Anton), e opcionalmente um recorte da
tela do código.

Gerar **3 variantes** de copy por vídeo e escolher. É o tipo de coisa que a IA faz bem: dar o
roteiro e pedir 10 títulos de thumb de no máximo 4 palavras.

---

## Etapa 8a — Shorts

**Princípio: short não é vídeo longo cortado no susto. É um trecho que já foi escrito pra se
sustentar sozinho.** Por isso os marcadores vão no roteiro **antes de gravar** — quando eu
escrevo o bloco do `parity`, eu já escrevo sabendo que aqueles 40 segundos são um short.

Isso muda como eu escrevo: o trecho marcado precisa abrir sem depender do que veio antes e
fechar sem prometer o que vem depois. É uma restrição de **escrita**, não de edição.

Mecanicamente é de graça: o alinhamento já sabe onde cada palavra está, então `inicio`/`fim`
viram tempo igual às cenas. O mesmo áudio, as mesmas cenas, recortados.

### O que muda do longo pro short

| | Longo | Short |
|---|---|---|
| Formato | 1920x1080 | **1080x1920** (9:16) |
| Duração | 15–18 min | 20–60s, alvo **~45s** |
| Legenda | opcional (`.srt`) | **queimada no vídeo**, obrigatório |
| Gancho | 45s de contexto | **primeiros 2 segundos** ou perdeu |
| Fecho | "comenta aí" | nome do canal, sem CTA longo |

O reenquadramento é o único trabalho real: cena de terminal em 16:9 não cabe em 9:16. Duas
saídas, e prefiro a segunda:

1. Crop central + barras navy `#122440` em cima e embaixo — rápido, funciona, feio.
2. **Layout vertical próprio:** faixa de título no topo, o asset no meio já renderizado em
   proporção vertical, legenda embaixo. Como VHS e freeze são scriptados, é só gerar o mesmo
   `.tape` num tamanho diferente. **É a vantagem de ter asset determinístico.**

### Saída

```json
{ "id": "uma-linha", "titulo": "Uma linha, 15 tiros a menos",
  "inicio": 745.2, "fim": 789.6, "duracao": 44.4,
  "origem": "01-batalha-naval", "legenda": "queimada" }
```

Um short por semana entre os longos. **Regra: se eu não consegui marcar pelo menos 3 shorts
no roteiro, o roteiro provavelmente não tem 3 ideias claras** — sinal de que o vídeo está
morno.

---

## Etapa 8b — Blog

**O blog não é a transcrição do vídeo.** Transcrição lida é ruim: repetição, "olha só", frases
que só funcionam faladas. O que os dois compartilham é o **material de origem** — o projeto,
os números, o código — não o texto.

Por que existe: ranqueia no Google (vídeo não), é o formato certo pra quem quer copiar código,
e é onde eu posso aprofundar sem estourar a duração do vídeo.

### O que o texto faz melhor que o vídeo

Vale escrever o post explorando exatamente isso, senão é vídeo pior:

- **Código que dá pra copiar** e ler no seu ritmo, com o arquivo/linha de referência.
- **Profundidade opcional** — no vídeo eu prometi "cada tema vira vídeo próprio"; no post eu
  posso abrir a prova do `parity` num bloco recolhível sem perder quem não quer.
- **Tabelas de dados** — a matriz completa do benchmark (16 combinações) cabe. No vídeo eu
  mostrei 4 linhas.
- **Links** — repositório, ferramentas, artigos.
- **Consulta** — a pessoa volta pra achar uma coisa específica. Ninguém volta num vídeo pra
  isso.

### Estrutura

Deriva do roteiro mas **reescrita**, não colada:

```
título (SEO, diferente do título do vídeo)
gancho curto — o número 95 → 44
o vídeo embedado, no topo, pra quem prefere assistir
seções ~= os blocos do roteiro, mas com liberdade pra fundir e reordenar
blocos de código completos, com caminho do arquivo
a tabela cheia do benchmark
"o que eu cortei do vídeo" ← aqui entra o aprofundamento
links: repo, ferramentas
```

Um detalhe que vale a pena: **as mesmas cenas viram figuras**. Os PNGs do `freeze` e os
GIFs do VHS já estão gerados na etapa 5 — o post reusa direto, sem produzir imagem nova.

### Onde publicar

| Opção | Nota |
|---|---|
| **Site próprio, `/blog`** | **Recomendado.** Mesmo domínio do site de jogos — o tráfego se soma, e ads já vão estar configurados lá (fase 2 do `VISION.md`). Markdown + gerador estático. |
| dev.to / Medium | Distribuição de graça, mas o tráfego é deles. Serve como *cross-post* com canonical apontando pro meu. |

Recomendação: **publica no meu, faz cross-post com `rel=canonical`.**

### Ritmo

O post sai **junto ou depois** do vídeo, nunca antes — o vídeo é o produto principal e o post
linka pra ele. Um post por vídeo longo. Se um tema cortado ficar grande demais, vira post
próprio sem vídeo (barato de fazer, e alimenta a lista de vídeos futuros).

---

## Onde a IA entra (tenho chaves Claude/OpenAI)

Uso de LLM nas etapas de **texto**, não de mídia:

| Tarefa | Vale a pena? |
|---|---|
| Rascunhar/revisar o roteiro em pt-BR | **Sim** — é o maior ganho |
| Sugerir marcadores de cena a partir do roteiro pronto | **Sim** — passa o `.md`, devolve onde cada cena entra |
| Compor cena Manim a partir da biblioteca existente | **Sim** — compor, não gerar do zero |
| Sugerir onde marcar os shorts no roteiro | **Sim** — mas eu decido; o critério "se sustenta sozinho?" é meu |
| Título/legenda de cada short | **Sim** |
| **Rascunhar o post de blog** a partir do roteiro | **Sim, com cuidado** — ver abaixo |
| Título, descrição, tags, capítulos | **Sim** — barato e chato de fazer na mão |
| Variantes de copy de thumbnail | **Sim** |
| Traduzir roteiro pra inglês | Sim, quando fizer sentido |
| Gerar a imagem da thumb | **Não** — texto sai ruim, usar HTML |
| Narração TTS no vídeo | **Não** — mata a primeira pessoa. Só como dublê descartável de teste |
| Editar/cortar vídeo | Não — determinístico resolve melhor |

Chamadas de texto podem ir em batch, é barato. Nada disso precisa ser em tempo real.

**Sobre o blog gerado por IA:** o risco é sair transcrição disfarçada — texto que repete o
roteiro com outras palavras e não usa nada do que o formato escrito tem de bom. O prompt tem
que dar o **material** (código, números do benchmark, o repositório) e o **roteiro como
referência de assunto**, pedindo explicitamente um artigo que aprofunde onde o vídeo cortou.
E eu reescrevo a abertura e o fecho na mão, sempre — é onde a voz aparece.

---

## Estrutura de pastas proposta

```
studio/
  videos/
    01-batalha-naval/
      script.md          ← roteiro aprovado, com marcadores
      narration.txt      ← gerado: só as falas
      narration.wav      ← gravado por mim
      timeline.json      ← gerado: cenas + tempos
      shorts.json        ← gerado: cortes + títulos
      tapes/*.tape       ← fontes VHS
      thumb.vars.json    ← título, número em destaque
      post.md            ← o blog, escrito (não gerado do áudio)
      build/             ← assets + mp4 + shorts/ + srt + thumb.png (gitignored)
  templates/
    thumb.html
    card.html
    short.html         ← layout vertical 9:16
  cmd/                   ← as ferramentas do pipeline
```

Regra: **tudo em `build/` é descartável.** Se apagar, um comando reconstrói. O que entra no
git é o roteiro, os `.tape`, os templates e o áudio.

---

## Os comandos que eu quero ter

O pipeline é um alvo por etapa, cada um idempotente e cacheado. Rodar de novo só refaz o que
mudou.

```
studio narracao 01     # script.md → narration.txt (o que eu vou ler)
                       # [eu gravo narration.wav]
studio alinhar 01      # + wav → words.json, legendas
studio timeline 01     # marcadores + words.json → timeline.json, shorts.json
studio assets 01       # gera TUDO: vhs, freeze, manim, replay, cards
studio montar 01       # → video.mp4 + .srt
studio shorts 01       # → shorts/*.mp4 verticais, legenda queimada
studio thumb 01        # → thumb.png (+ variantes)
studio meta 01         # → título, descrição, capítulos, tags

studio tudo 01         # ← o alvo real: tudo acima em sequência
```

`studio assets` é o que mais economiza tempo e o que mais demora a rodar (Manim). Vale
paralelizar e cachear por hash de entrada desde o começo.

**Falta de asset não pode quebrar o render.** Se uma cena de gravação manual ainda não existe,
o pipeline coloca um placeholder navy com o `id` escrito e segue — eu vejo o vídeo inteiro e
sei exatamente o que falta gravar.

---

## Em que ordem construir

Não construir o pipeline inteiro antes de fazer o vídeo 01. Fazer o 01 majoritariamente na
mão e automatizar o que doeu.

1. **Manual + VHS/freeze.** Vídeo 01 editado à mão, mas as cenas de terminal e código já
   geradas por script. Ganho imediato, custo quase zero.
2. **Alinhamento.** WhisperX no áudio do 01, gerar `timeline.json`, usar só pra saber onde
   colocar as coisas. Já economiza a parte mais chata da edição.
3. **Montagem automática** via ffmpeg, quando os passos 1 e 2 estiverem confiáveis.
4. **Thumb template.** Pode ser feito a qualquer momento, é independente.
5. **Renderizador de replay** do Batalha Naval — é específico do vídeo 01, mas é o asset de
   maior impacto visual.
6. **Corte de shorts.** Depois do alinhamento funcionar, é quase de graça — os tempos já
   existem. O trabalho é o template vertical + legenda queimada.
7. **Blog.** Independente do pipeline de vídeo, depende do site existir (`/blog`). Fora de
   escopo agora — primeiro post escrito à mão, sem ferramenta nenhuma.

O **Manim entra junto com o passo 1**, fora de ordem, por um motivo: a animação do `density` e
a do `parity` são o conteúdo mais forte do vídeo 01 e as mais demoradas de fazer. Começar cedo
com uma cena só (`parity`, que é a mais simples e o melhor short) e ver quanto tempo custa de
verdade antes de depender dela.

Os shorts do vídeo 01 já estão listados no fim de `studio/videos/01-batalha-naval/script.md` — falta
marcá-los no corpo do roteiro com `<!-- short: inicio ... -->` antes de gravar.

Só considerar isso "um software" (e possível conteúdo/produto) depois do vídeo 03. Antes
disso são scripts.

---

## Decisões que ainda não tomei

- ~~Linguagem do pipeline~~ — **resolvido: Python.** WhisperX, Playwright e Manim são todos
  Python; não faz sentido lutar contra isso. O Go fica só no que é do jogo: exportar replay e
  o `density.json` pro Manim consumir.
- Quão longe a montagem automática chega antes de o corte manual dar vídeo visivelmente
  melhor. Só descubro fazendo o 01.
- Quanto tempo uma cena Manim custa de verdade. É o maior risco de estimativa do plano.
- Se o canal terá versão em inglês dos mesmos roteiros.
