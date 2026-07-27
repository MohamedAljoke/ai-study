# Sprint 4 — Assets determinísticos

**Objetivo:** cada cena da timeline vira um arquivo de mídia, gerado por comando, sem eu
gravar tela.

Este é o sprint que mais economiza tempo por vídeo. E ele tem uma propriedade que gravação
manual nunca terá: **mudou o código do jogo, roda de novo e os vídeos se atualizam.** Nada de
regravar terminal porque o output mudou.

## Entregável

```
$ studio assets 01
play-demo        terminal  vhs      12.4s   gerado
parse-position   codigo    freeze    —      cache
density-mapa     manim     —         —      pulado (sprint 6)
abertura         card      html       —     gerado
web-demo         tela      manual    —      PLACEHOLDER

10/14 gerados, 3 em cache, 1 placeholder
```

## Tipos de cena

| Tipo | Ferramenta | Por quê |
|---|---|---|
| `terminal` | **VHS** (charmbracelet) | Um `.tape` descreve o que digitar e o timing; sai MP4 idêntico toda vez |
| `codigo` | **freeze** (charmbracelet) | Arquivo + intervalo de linhas → PNG bonito, via CLI |
| `card` | HTML + **Playwright** | Tabelas, títulos de bloco, o "95 → 44" |
| `replay` | ferramenta Go própria | `internal/replay` já grava snapshot tiro a tiro |
| `diagrama` | Mermaid | Árvore de pastas, fluxo |
| `manim` | Manim Community | [Sprint 6](sprint-06-manim.md) |
| `tela` | **OBS**, gravado por mim | Navegador, editor. Deve ser a minoria |

**VHS e freeze são o maior ganho isolado do pipeline.** Se este sprint entregasse só esses
dois, já valia.

## Tarefas

1. **Registro de geradores** — um por tipo, mesma assinatura, recebendo a cena da timeline e
   devolvendo o caminho do asset. Tipo novo é um arquivo novo, não uma mudança no motor.
   Os tipos e seus parâmetros já estão declarados em `studio/cenas.py` desde o sprint 1; aqui
   cada um ganha um gerador. Os caminhos marcados como `adiados` lá (`.tape`, `density.json`)
   são exatamente os que este sprint passa a produzir — quando existirem, os avisos do
   `studio narracao` somem sozinhos.
2. **Gerador `terminal`:** roda VHS no `.tape`, corta na duração da cena. O `.tape` é
   versionado; o MP4 é descartável.
3. **Gerador `codigo`:** `freeze` no arquivo + linhas, tema com as cores da marca. Aponta pro
   código **real** do repositório — se o arquivo mudou, o PNG muda, e é isso que eu quero.
4. **Gerador `card`:** template HTML + variáveis → Playwright → PNG 1920x1080. Mesmo CSS da
   thumb (sprint 8), pra identidade não divergir.
5. **Placeholder** pra cena `tela` sem gravação: fundo `#122440`, o `id` em branco, duração
   certa. [Convenções §3](convencoes.md) — falta de asset nunca quebra o render.
6. **Cache por hash** de (arquivo fonte + parâmetros + versão da ferramenta).
7. **Paralelismo.** É o comando mais lento do pipeline; as cenas são independentes.

## Critério de pronto

- Todas as cenas do vídeo 01 que **não** são `tela` nem `manim` geram asset sem eu tocar em
  nada.
- Mudar uma linha em `internal/game/position.go` e rodar de novo regenera **só** o
  `parse-position`.

## Uma coisa que vale fazer aqui

Os `.tape` do VHS podem ser **gerados a partir do jogo real**: rodar `cmd/play` com uma
sequência de tiros conhecida e emitir o `.tape` correspondente. Assim a demo de terminal não é
uma encenação — é uma partida de verdade, reproduzível.

Não é obrigatório pro sprint fechar, mas é barato e melhora o vídeo.

## Fora de escopo

Juntar os assets. Aqui cada cena vira um arquivo solto; a montagem é o sprint 5.
