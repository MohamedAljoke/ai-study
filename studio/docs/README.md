# Plano de construção — sprints

Divisão do `studio` em sprints. Cada sprint entrega **alguma coisa que eu consigo usar
sozinha**, mesmo que o resto ainda não exista. Nenhum sprint depende de um sprint futuro pra
ter valor.

## Princípio da ordem

Não construir o pipeline inteiro antes de fazer o vídeo 01. **Fazer o vídeo 01 e automatizar
o que doeu.** Cada sprint sai de uma dor real do vídeo anterior, não de um plano no papel.

## Sprints

| # | Sprint | Entrega | Depende de | |
|---|---|---|---|---|
| 0 | [Fundação](sprint-00-fundacao.md) | `studio` roda, `studio novo 01` cria a pasta do vídeo | — | ✅ |
| 1 | [Roteiro e marcadores](sprint-01-roteiro.md) | `studio narracao 01` → o texto que eu leio | 0 | ✅ |
| 2 | [Áudio e alinhamento](sprint-02-alinhamento.md) | `studio alinhar 01` → tempo de cada palavra + legendas | 1 | ✅ |
| 3 | [Timeline](sprint-03-timeline.md) | `studio timeline 01` → cena X entra em 04:12.3 | 2 | ✅ |
| 4 | [Folha de pedidos](sprint-04-pedidos.md) | `studio pedidos 01` → o que produzir, com duração | 3 | ✅ |
| 5 | [Montagem](sprint-05-montagem.md) | `studio montar 01` → **video.mp4** | 4 | ✅ |
| 6 | [Interface](sprint-06-ui.md) | `studio ui` → roteiro, áudio e assets numa página | 5 | ✅ |
| 7 | [Shorts](sprint-07-shorts.md) | `studio shorts 01` → verticais com legenda queimada | 5 | ← |
| 8 | [Thumb e metadados](sprint-08-thumb-meta.md) | `studio thumb/meta 01` → thumb.png, título, capítulos | 0 | |

O sprint 2 precisa do `narration.wav`, que é gravação minha — mas `studio duble` gera uma voz
sintética temporária com o mesmo texto, então o **código** dos sprints 2 a 5 anda sem esperar
por mim. O vídeo publicável não.

**O sprint 5 é o marco.** Até ele, o `studio` ajuda a editar. A partir dele, o `studio`
monta o vídeo.

## O studio é orquestrador, não gerador

Decisão tomada depois do sprint 5, olhando o vídeo que saiu: **o studio não produz mídia.**
A primeira versão gerava as cenas sozinha — VHS pro terminal, freeze pro código, Chrome pras
cartelas — e o resultado não era assistível. Ficava a cara de "gerado", não a cara do canal.

O que sobrou pro studio são as três coisas mecânicas, que ele faz bem:

1. **tempo** — posição no texto vira segundo (sprints 1 a 3);
2. **a encomenda** — `pedidos.md` diz id, duração exata e o que se fala em cada cena;
3. **a junção** — os arquivos que eu produzi + a narração viram `video.mp4`.

A parte visual é minha, feita fora, principalmente em **Manim**. Isso não tornou o pipeline
mais frouxo: a duração de cada cena continua vindo do áudio, e mirar nela é o que faz o
arquivo que eu produzo entrar sem retrabalho.

O sprint 6 era o do Manim, e **saiu do plano do studio** por isso — não é código daqui. O que
valia dele continua valendo como método de trabalho, e está anotado embaixo. O número foi
reaproveitado pela [interface](sprint-06-ui.md), que nasceu da dor seguinte: com o pipeline
pronto, o que sobrou foi repetir dezoito vezes o mesmo copiar-arquivo-e-conferir.

## Dependências reais

```
0 ──> 1 ──> 2 ──> 3 ──> 4 ──> 5 ──> 7
                              └──> 6
0 ──────────────────────────> 8
```

O sprint 8 é independente do caminho principal e é o mais barato de todos. O 6 também sai do
5 e não bloqueia ninguém: a interface é casca sobre o pipeline pronto, e tudo continua
funcionando pelo terminal sem ela.

## Como eu faço as animações (fora do studio)

Não é tarefa de sprint, é como eu trabalho — e é o que evita cair na armadilha de sempre.

**Animar dados reais, não desenho.** O jeito preguiçoso é ilustrar o algoritmo; o certo é a
animação **consumir a saída do código de verdade** — o `density.go` exporta o score de cada
casa por turno, o Manim lê aquilo e anima. Mudei o `hitWeight` no Go, a animação muda junto.
Tem bônus temático: o vídeo fala sobre separar domínio de apresentação, e a animação é mais
uma casca lendo o mesmo motor.

**Biblioteca pequena, escrita à mão:** `GridBoard`, `HeatMap(dados)`, `ShipOverlay`,
`ShotSequence(replay)`. Gerar cena Manim do zero com LLM não funciona — sai animação que não
renderiza, ou que renderiza feia. LLM **compõe** a partir das classes que existem; cena
realmente nova eu escrevo, e ela entra na biblioteca. O investimento é na biblioteca, não em
prompt: ela cresce a cada vídeo e o custo por animação cai.

**Fundo `#122440`, elementos `#FFFFFF`, destaque `#FFB020`** — as cores do canal, no
`manim.cfg`, pra não sair do padrão por descuido.

O risco continua o mesmo de sempre: **quanto tempo uma cena Manim custa de verdade?** A do
`parity` é a mais simples e vira o melhor short — é por ela que eu começo. Se custar caro
demais, o plano B é honesto: menos animação por vídeo, só onde o visual carrega a explicação.

## Fora de escopo (por enquanto)

- **Upload automático pro YouTube.** Eu subo na mão. O pipeline entrega os arquivos.
- **Blog.** Primeiro post escrito à mão, sem ferramenta. Depende do site existir.
- **TTS no vídeo publicado.** O canal é primeira pessoa; eu leio. Voz sintética existe só como
  [dublê](sprint-02-alinhamento.md) de teste, em `build/`, e nunca chega no que sai no ar.

## Convenções

Regras que valem pra todos os sprints estão em [convencoes.md](convencoes.md). Vale ler antes
do sprint 0.
