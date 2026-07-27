# Vídeo 01 — O que aprendi sobre desenvolvimento de software fazendo uma Batalha Naval

**Formato:** um vídeo só, ~15–18 min. Panorama, não aprofundamento.
**Idioma:** pt-BR.
**Regra do roteiro:** cada bloco entrega **uma** lição. Se der vontade de aprofundar, corta e
vira vídeo próprio (lista no fim).

---

## Estrutura em uma linha

`print do tabuleiro` → `input no terminal` → `testar isso dói` → `domínio separado` →
`as estratégias da IA` → `benchmark prova qual é melhor` → `trocar terminal por web é barato`

---

## Bloco 0 — Gancho (0:00 – 0:45)

**Tela:** tabela do benchmark rodando, números aparecendo.

<!-- cena: terminal id=abertura-bench fonte=tapes/bench.tape -->
> Eu fiz o computador jogar Batalha Naval trinta e duas mil vezes.

<!-- short: inicio id=95-para-44 titulo="De 95 tiros para 44" -->
> A primeira versão da IA afundava a frota inteira em **noventa e cinco tiros**. O tabuleiro
> tem cem casas. Ou seja: ela era basicamente tão boa quanto atirar em tudo.
>
> A última versão faz em **quarenta e quatro**.
>
> E o que eu aprendi chegando de noventa e cinco até quarenta e quatro não foi sobre Batalha
> Naval. Foi sobre desenvolvimento de software. Separação de domínio, teste, benchmark, e por
> que trocar o terminal por um site foi a parte mais fácil do projeto inteiro.
<!-- short: fim id=95-para-44 -->

> Bora do começo — e o começo é bem burro.

**Corte seco pro Bloco 1.**

---

## Bloco 1 — O começo burro: só desenhar o tabuleiro (0:45 – 3:00)

**Lição: comece pela coisa mais idiota que você consegue ver funcionando.**

**Tela:** `main.go` vazio, digitar ao vivo (ou timelapse) um grid 10x10 de pontos.

<!-- cena: tela id=grid-ao-vivo nota="timelapse digitando o main.go de dois minutos" -->
> Eu não comecei com arquitetura. Comecei com isso aqui: um `main.go` que imprime dez
> linhas de ponto.

```go
for row := range BoardSize {
    for col := range BoardSize {
        fmt.Print(". ")
    }
    fmt.Println()
}
```

> Rodei. Apareceu um quadrado de pontinhos no terminal. **Isso é um tabuleiro.**
>
> Parece bobo, mas esse é o ponto: eu tinha uma coisa na tela em dois minutos. Não tinha
> pasta `internal`, não tinha interface, não tinha teste. Tinha um quadrado.
>
> Aí eu quis colocar navio nele. E aí começou o software de verdade.

**Mostrar rápido:** o `Cell` como `uint8` com `.`, `S`, `X`, `M` e o `Render(revealShips bool)` —
o mesmo desenho, agora com a regra "esconde o navio do inimigo" dentro de um `bool`.

<!-- cena: codigo id=render-bool arquivo=battleships/internal/game/board.go linhas=43-60 -->
> Um `bool` de parâmetro e o mesmo código desenha o seu tabuleiro com os navios à mostra e o
> do inimigo debaixo da neblina.

---

## Bloco 2 — O terminal pedindo jogada (3:00 – 5:00)

**Lição: input do usuário é 90% tratar o que ele digitou errado.**

**Tela:** rodar `go run ./cmd/play`, posicionar a frota, atirar. Deixar aparecer erro de
propósito: digitar `Z9`, digitar `A0 x`, atirar duas vezes na mesma casa.

<!-- cena: terminal id=play-demo fonte=tapes/play.tape -->
> Loop clássico: pergunta, lê, valida, repete.

```go
p, err := game.ParsePosition(line)
if err != nil { fmt.Println(err); continue }
if theirs.At(p).Shot() { fmt.Println("já atirou aqui"); continue }
```

<!-- cena: codigo id=parse-position arquivo=battleships/internal/game/position.go linhas=23-40 -->
> Repara numa coisa: quase todo o meu `main.go` é **conversa com humano**. Perguntar,
> reclamar, formatar, desenhar dois tabuleiros lado a lado.
>
> A regra do jogo mesmo — "esse tiro acertou? esse navio afundou?" — é uma linha:
> `theirs.Fire(p)`.
>
> Guarda essa proporção. Ela volta no bloco quatro.

---

## Bloco 3 — Aí eu fui testar, e doeu (5:00 – 7:30)

**Lição: se pra testar você precisa capturar stdout, o problema não é o teste. É o design.**

**Tela:** escrever um teste que captura stdout. Mostrar a gambiarra na cara:

```go
old := os.Stdout
r, w, _ := os.Pipe()
os.Stdout = w
// ... roda o jogo ...
w.Close()
os.Stdout = old
saida, _ := io.ReadAll(r)

if !strings.Contains(string(saida), "acertou") { ... }
```

<!-- cena: tela id=teste-stdout-dor nota="escrever o teste que captura stdout, em commit separado" -->
<!-- short: inicio id=teste-stdout titulo="Seu teste está testando o texto" -->
> Isso **funciona**. Dá pra testar assim. Eu testei assim.
>
> Mas olha o tamanho do desconforto: eu troquei a saída padrão do processo, li de um pipe, e
> aí fiquei procurando *substring* no texto pra saber se o jogo funcionou. Meu teste depende
> da palavra "acertou". Se eu traduzir a mensagem, o teste quebra — e o jogo continua certo.
>
> **Um teste que quebra quando o texto muda não está testando a regra. Está testando o
> texto.**
>
> E o motivo é simples: a regra do jogo e a impressão na tela estavam no mesmo lugar. Pra
> chegar na regra eu tinha que passar pela tela.
>
> Se eu separasse as duas, o teste vira isso:

```go
res, err := b.Fire(game.Position{Row: 0, Col: 0})
// res.Hit == true, res.Sunk.Type.Name == "Destroyer"
```

<!-- cena: codigo id=fire-direto arquivo=battleships/internal/game/board.go linhas=114-135 -->
> Sem pipe, sem stdout, sem substring. **A dor do teste foi o que me mostrou onde cortar o
> código.**
<!-- short: fim id=teste-stdout -->

---

## Bloco 4 — O domínio: o jogo é o motor, o resto é casca (7:30 – 10:00)

**Lição: o núcleo não pode saber que o terminal existe.**

**Tela:** `tree` das pastas, depois abrir `internal/game/board.go`.

```
battleships/
  cmd/play/      ← terminal: bufio, os.Stdin, fmt.Print
  internal/
    game/        ← as regras: Board, Ship, Position, Fire, AllSunk
    placement/   ← como as frotas são posicionadas
    targeting/   ← como a IA escolhe o tiro
```

<!-- cena: terminal id=tree-internal fonte=tapes/tree.tape -->
> Faz um `grep` por `os.Stdin` dentro de `internal/`. **Zero.** Por `bufio`. Zero.
>
> O pacote `game` não sabe que existe terminal. Não sabe que existe usuário. Ele sabe
> responder três perguntas: *dá pra colocar esse navio aqui?*, *esse tiro acertou o quê?*,
> *acabou?*

```go
func (b *Board) Fire(p Position) (Result, error)
func (b *Board) AllSunk() bool
```

<!-- cena: codigo id=dominio-assinaturas arquivo=battleships/internal/game/board.go linhas=150-160 -->
> Isso é o que as pessoas chamam de **domínio**. E a definição prática, sem livro, é: é a
> parte do código que continua igual se amanhã eu jogar o terminal fora.
>
> Eu não fiz isso porque li que era certo. Eu fiz porque o teste do bloco anterior estava
> horrível.

**Ponto honesto pra falar em voz alta:**

> E olha, tem uma coisa de terminal que sobrou dentro do `game`: o método `Render`, que
> devolve o desenho em texto. Eu podia dizer que é impuro e tirar. Mas ele é opcional — o
> resto do motor não depende dele. **Separação não é pureza, é saber o que você joga fora
> sem quebrar nada.**

---

## Bloco 5 — O coração: as estratégias da IA (10:00 – 14:00)

**Lição: algoritmo não é enfeite. É a diferença entre 95 e 44.**

**Tela:** os replays visuais dos tiros, uma estratégia de cada vez. Este é o bloco mais longo
e o mais visual do vídeo.

Tudo isso vive atrás de **uma interface de dois métodos**:

```go
type Strategy interface {
    Next() game.Position                  // onde eu atiro agora
    Observe(p game.Position, r game.Result) // o que aconteceu com o último tiro
}
```

<!-- cena: codigo id=strategy-interface arquivo=battleships/internal/targeting/strategy.go linhas=9-12 -->
> "Chuta um lugar" e "toma o resultado". Todas as IAs implementam isso, e o jogo não sabe
> qual delas está jogando.

### 5.1 — `random` — o piso

<!-- cena: replay id=replay-random dados=build/replays/random.json estrategia=random -->
> Sorteia uma casa que ainda não atirou. `Observe` não faz nada — ela **ignora** a
> informação. Média: **noventa e cinco tiros**. Esse é o piso. Qualquer coisa melhor que isso é ganho.

### 5.2 — `hunt` — usar a informação que já está na mesa

<!-- cena: manim id=hunt-fila classe=ShotSequence dados=build/replays/hunt.json -->
> Acertou? Enfileira as quatro casas vizinhas e atira nelas antes de voltar a chutar.

```go
if r.Hit {
    for _, n := range neighbours(p) { h.queue = append(h.queue, n) }
}
```

> **De noventa e cinco para setenta.** Vinte e cinco tiros de ganho, com quatro linhas. Nenhuma matemática. Só parar
> de jogar fora um dado que eu já tinha.

### 5.3 — `parity` — usar a regra do jogo a seu favor

<!-- cena: manim id=parity-prova classe=ShipOverlay -->
<!-- short: inicio id=uma-linha titulo="Uma linha, 15 tiros a menos" -->
> O menor navio ocupa **duas** casas. Então qualquer navio, em qualquer posição, cobre pelo
> menos uma casa preta de um tabuleiro de xadrez. Ou seja: eu posso **ignorar metade do
> tabuleiro** na fase de busca.

```go
if (p.Row+p.Col)%2 == 0 { hunt = append(hunt, p) }
```

> **De setenta para cinquenta e cinco.** Essa é minha parte favorita do projeto, porque o ganho não veio de código
> melhor. Veio de **entender melhor o problema**. É uma linha de código e uma ideia.
<!-- short: fim id=uma-linha -->

### 5.4 — `density` — pensar em probabilidade

<!-- cena: manim id=density-mapa classe=HeatMap dados=build/density.json turnos=1-12 -->
> Pra cada casa, conto de quantas maneiras os navios que ainda estão vivos caberiam
> passando por ali. Atiro na casa de maior contagem. Acertos vizinhos pesam mais.
>
> **De cinquenta e cinco para quarenta e quatro.**

### O resumão na tela

| estratégia | média de tiros |
|---|---|
| random  | 95.5 |
| hunt    | 69.7 |
| parity  | 54.9 |
| density | 44.4 |

<!-- cena: card id=tabela-estrategias titulo="95 → 44" subtitulo="média de tiros por estratégia" -->
> E aqui vem a pergunta que fecha o bloco: **como é que eu sei que esses números são
> verdade?**

---

## Bloco 6 — Benchmark: parar de achar e começar a medir (14:00 – 16:00)

**Lição: "ficou mais rápido" sem número é opinião.**

**Tela:** `go test ./internal/bench/ -v` rodando e cuspindo a matriz.

<!-- cena: terminal id=bench-rodando fonte=tapes/bench.tape -->
> Cada estratégia joga **duas mil partidas** contra **quatro jeitos diferentes de posicionar a frota** —
> uniforme, colada nas bordas, no centro, espalhada. Dezesseis combinações, trinta e duas mil
> partidas, uns onze segundos.

```go
const seed = 42
rng := rand.New(rand.NewPCG(seed, uint64(gameIdx)))
```

> **Semente fixa.** Isso é o detalhe que faz o benchmark valer alguma coisa: rodou hoje,
> rodou daqui a seis meses, dá o mesmo número. Se eu mexer numa estratégia e a média mudar,
> foi **eu** que mudei — não foi sorte.
>
> E ele testa contra posicionamentos diferentes de propósito, senão eu estaria só otimizando
> a IA pra um jeito específico de esconder navio.
>
> Isso não é enfeite de projeto pessoal. É a diferença entre "acho que melhorou" e "melhorou
> vinte por cento".

---

## Bloco 7 — E o site? (16:00 – 17:30)

**Lição: a recompensa da separação chega tarde, mas chega de uma vez.**

**Tela:** o site rodando no navegador ao lado do terminal, mesma partida.

<!-- cena: tela id=web-demo nota="site e terminal lado a lado, mesma partida — depende do site existir" -->
<!-- short: inicio id=terminal-para-web titulo="Troquei o terminal por um site e não mudei o jogo" -->
> Quando eu fui levar isso pro navegador, a pergunta era: quanto do jogo eu vou ter que
> reescrever?
>
> Resposta: **nada de `internal/`.** Nem uma linha das regras, nem uma linha das
> estratégias.
>
> O que eu joguei fora foi o `main.go` do terminal — o `bufio.Scanner`, os `fmt.Print`, o
> desenho em ASCII. E o que eu escrevi no lugar foi uma casca nova que chama exatamente as
> mesmas funções.
>
> O `Fire` é o mesmo `Fire`.
>
> **Essa é a fatura chegando.** Toda aquela chatice do bloco três e do bloco quatro — separar,
> tirar o `fmt` de dentro da regra — ela não me deu nada na hora. Ela me deu isso aqui,
> semanas depois.
<!-- short: fim id=terminal-para-web -->

**Teaser do próximo:**

> E tem uma coisa que o navegador abre e o terminal não abria: **jogar contra outra pessoa**.
> Isso é WebSocket, é estado no servidor, é o que acontece quando o cara fecha a aba no meio
> da partida. É vídeo próprio.

---

## Bloco 8 — Fechamento (17:30 – 18:00)

<!-- cena: card id=fechamento titulo="Cinco coisas" subtitulo="o que eu levo desse projeto" -->
> Cinco coisas que eu levo desse projeto:
>
> 1. Comece com o quadrado de pontinhos.
> 2. Teste difícil de escrever é sintoma de design, não de preguiça.
> 3. O domínio é o que sobra quando você tira a tela.
> 4. Entender o problema rende mais que otimizar o código. (`parity`: uma linha, quinze
>    tiros.)
> 5. Meça. Com semente fixa.
>
> Código todo no link aí embaixo. Se quiser que eu aprofunde algum desses, comenta qual — eu
> já tenho a lista.

---

## Cortes / vídeos que saem daqui

Coisas que **não** entram neste vídeo, justamente porque cada uma sustenta um sozinha:

- Como funciona a `density` de verdade (o mapa de probabilidade, os pesos)
- Por que `parity` funciona — a prova, não só a intuição
- Testar em Go sem capturar stdout: table tests, interfaces, `io.Writer`
- Benchmark reprodutível: seed, `rand/v2`, `PCG`, por que `math/rand` global é armadilha
- O sistema de replay (`internal/replay`) — gravar a partida pra depurar a IA
- WebSocket + multiplayer + o cara que fecha a aba
- Deploy e ads no site

---

## Shorts que dá pra tirar deste roteiro

1. **"Uma linha de código, 15 tiros a menos"** — só o `parity`. É o melhor short do lote.
2. **"Seu teste está testando o texto, não o código"** — o pipe de stdout do bloco 3.
3. **"95 → 44"** — timelapse das quatro IAs jogando lado a lado, sem narração, só os números.
4. **"Eu troquei o terminal por um site e não mudei uma linha do jogo"** — o `tree` + o `grep`
   por `os.Stdin` dando zero.

---

## Notas de produção

**Números:** a tabela do bloco 6 é saída real de `go test ./internal/bench/ -v` (2000 partidas
por combinação, seed 42). **Regravar a tabela se mexer em qualquer estratégia** — os números
do roteiro têm que bater com os da tela.

**O que ainda não existe no repositório e precisa ser feito antes de gravar:**

- O teste que captura stdout (bloco 3) — hoje não está no projeto. Escrever de propósito, pra
  filmar a dor, e deixar num branch/commit separado.
- A versão web (bloco 7) — ainda não existe. **Este bloco não pode ser gravado antes do site
  rodar.** Ver `VISION.md`, fase 1.
- O `main.go` mínimo do bloco 1 — reconstruir a versão de dois minutos pra filmar, o projeto
  atual já passou desse ponto.

**Visual:** os replays das estratégias (bloco 5) são o que segura o vídeo. Vale investir o
tempo de produção ali e ser econômico nos blocos de texto. O `internal/replay` já grava
snapshot tiro a tiro — dá pra virar animação.

**Tom:** primeira pessoa, sem "nós, desenvolvedores". Sem prometer profundidade que o vídeo
não tem — assumir de cara que é panorama e que cada tema tem vídeo próprio.
