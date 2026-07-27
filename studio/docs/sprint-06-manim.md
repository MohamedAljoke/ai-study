# Sprint 6 — Animações de algoritmo (Manim)

**Objetivo:** explicar visualmente o que o código faz, com animação gerada a partir dos
**dados reais** do jogo.

É o conteúdo mais forte do vídeo 01 e o que mais diferencia o canal. Também é o mais caro —
por isso o [spike vem cedo](README.md#exceção-o-spike-de-manim-vem-cedo), durante o sprint 1,
mesmo que o sprint formal seja este.

**Manim Community** (`manim`), não o `manimgl` pessoal do Grant Sanderson.

## Casos no vídeo 01

- **`density`** — o tabuleiro virando mapa de calor de probabilidade, os números aparecendo
  casa a casa, o tiro indo na casa mais quente.
- **`parity`** — o xadrez sobrepondo o grid, um navio de 2 casas deslizando por cima e
  **sempre** cobrindo uma casa preta. É a prova visual, e ela vale mais que a explicação
  falada.
- **`hunt`** — a fila de vizinhos crescendo e sendo consumida.

## O truque: animar dados reais, não desenho

A parte que faz diferença e que eu não quero perder de vista.

O jeito preguiçoso é desenhar uma animação *ilustrando* o algoritmo. O jeito certo é a
animação **consumir a saída do código de verdade**:

```
Go: roda uma partida, exporta o score de cada casa por turno  →  density.json
                                   ↓
Manim: lê o JSON e anima exatamente aquilo
```

O mapa de calor na tela passa a ser **o mapa que o `density.go` calculou** — não uma
aproximação que eu fiz pra ficar bonita. Mudei o `hitWeight` no Go, a animação muda junto.

E tem um bônus temático: o vídeo fala sobre separar domínio de apresentação, e **a animação é
mais uma casca lendo o mesmo motor**. Dá pra falar isso em voz alta no vídeo.

## Como automatizar sem virar armadilha

Gerar código Manim do zero com LLM a cada cena **não funciona**. Sai animação que não
renderiza, ou que renderiza feia, e eu perco mais tempo depurando Python do que teria perdido
animando na mão.

O padrão que funciona:

1. **Biblioteca pequena de cenas parametrizadas, escrita à mão e reusável:** `GridBoard`,
   `HeatMap(dados)`, `ShipOverlay`, `ShotSequence(replay)`. Escrevo uma vez, uso em todo
   vídeo.
2. **O marcador do roteiro só escolhe e configura:**
   ```markdown
   <!-- cena: manim id=density-mapa classe=HeatMap dados=build/01/density.json turnos=1-12 -->
   ```
3. **A IA compõe, não inventa.** Cena nova, o LLM monta a partir das classes existentes —
   contexto pequeno, resultado previsível. Cena realmente nova eu escrevo, e ela **entra na
   biblioteca**.

O investimento é na biblioteca, não em prompt. Ela cresce a cada vídeo e o custo por animação
cai.

## Tarefas

1. **Export no lado Go** (a única mudança de código fora do `studio`): um modo que roda uma
   partida e serializa `d.score` por turno num `density.json`. Barato — o campo já existe em
   `internal/targeting/density.go`. Também serve pro post de blog.
2. **`manim.cfg` do canal:** fundo `#122440`, elementos `#FFFFFF`, destaque `#FFB020`. Nunca
   sair do padrão por descuido.
3. **`GridBoard`** — o tabuleiro 10x10 com coordenadas. Base de tudo.
4. **`HeatMap(dados)`** — lê o JSON e anima turno a turno.
5. **`ShipOverlay`** / **`ShotSequence(replay)`** — a prova do `parity` e o replay de partida.
6. **Gerador de cena `manim`** integrado ao `studio assets`, cacheado por hash da entrada.
7. **Render vertical 1080x1920** pros shorts — a animação do `parity` é o melhor short do
   lote e merece layout próprio, não crop.

## Prático

- Render é **lento**, minutos por cena. `-ql` enquanto edito, `-qh` só no final.
- Cache é obrigatório aqui, não otimização: JSON e parâmetros iguais, não re-renderiza.
- `-t` gera transparente, se eu quiser compor por cima de outra coisa.

## Critério de pronto

A cena do `parity` renderiza pelo `studio assets` e entra no vídeo montado sem passo manual.

Uma cena boa fecha o sprint. Duas é bônus.

## O risco

**Quanto tempo uma cena Manim custa de verdade?** É o maior risco de estimativa do plano
inteiro. Por isso o spike começa no sprint 1 com uma cena só — a do `parity`, a mais simples e
o melhor short.

Se custar caro demais, o plano B é honesto: menos animação por vídeo, usadas só onde o visual
carrega a explicação. Melhor descobrir isso antes de escrever um roteiro que depende de seis
animações.
