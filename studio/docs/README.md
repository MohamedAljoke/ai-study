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
| 2 | [Áudio e alinhamento](sprint-02-alinhamento.md) | `studio alinhar 01` → tempo de cada palavra + legendas | 1 | ← |
| 3 | [Timeline](sprint-03-timeline.md) | `studio timeline 01` → cena X entra em 04:12.3 | 2 | |
| 4 | [Assets determinísticos](sprint-04-assets.md) | `studio assets 01` → terminal, código e cards gerados | 3 | |
| 5 | [Montagem](sprint-05-montagem.md) | `studio montar 01` → **video.mp4** | 4 | |
| 6 | [Manim](sprint-06-manim.md) | animações de algoritmo a partir de dados reais | 4 | |
| 7 | [Shorts](sprint-07-shorts.md) | `studio shorts 01` → verticais com legenda queimada | 5 | |
| 8 | [Thumb e metadados](sprint-08-thumb-meta.md) | `studio thumb/meta 01` → thumb.png, título, capítulos | 0 | |

O sprint 2 precisa do `narration.wav`, que é gravação minha — mas `studio duble` gera uma voz
sintética temporária com o mesmo texto, então o **código** dos sprints 2 a 5 anda sem esperar
por mim. O vídeo publicável não.

**O sprint 5 é o marco.** Até ele, o `studio` ajuda a editar. A partir dele, o `studio`
monta o vídeo.

## Dependências reais

```
0 ──> 1 ──> 2 ──> 3 ──> 4 ──> 5 ──> 7
                        └──> 6
0 ──────────────────────────> 8
```

Os sprints 6 e 8 são independentes do caminho principal e podem ser feitos em qualquer
momento de folga. O 8 (thumb) é o mais barato de todos.

## Exceção: o spike de Manim vem cedo

O sprint 6 é formalmente depois do 5, mas **uma cena de Manim deve ser tentada já durante o
sprint 2**, fora de ordem — o sprint 2 tem tempo morto esperando eu gravar. Motivo: as animações do `density` e do `parity` são o conteúdo mais
forte do vídeo 01 e as mais lentas de produzir, e eu ainda não sei quanto tempo uma cena custa
de verdade. Esse é o maior risco de estimativa do plano inteiro.

O spike é uma cena só — a do `parity`, que é a mais simples e vira o melhor short. Se custar
caro demais, eu descubro antes de escrever um roteiro que depende de seis animações.

## Fora de escopo (por enquanto)

- **Upload automático pro YouTube.** Eu subo na mão. O pipeline entrega os arquivos.
- **Blog.** Primeiro post escrito à mão, sem ferramenta. Depende do site existir.
- **TTS no vídeo publicado.** O canal é primeira pessoa; eu leio. Voz sintética existe só como
  [dublê](sprint-02-alinhamento.md) de teste, em `build/`, e nunca chega no que sai no ar.

## Convenções

Regras que valem pra todos os sprints estão em [convencoes.md](convencoes.md). Vale ler antes
do sprint 0.
