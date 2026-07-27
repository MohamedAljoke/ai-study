# studio

Ferramenta interna de produção de vídeo do canal. Transforma um **roteiro aprovado + um áudio
gravado por mim** em **vídeo, shorts, legendas, thumb e metadados prontos pra publicar**.

O desenho do fluxo está em [`content/pipeline-producao.md`](../content/pipeline-producao.md).
Este diretório é a implementação.

## O que é meu, o que é da máquina

Eu faço três coisas: **aprovo o roteiro**, **leio em voz alta** e **gravo as cenas que não dá
pra scriptar**. Todo o resto é do `studio`.

## Estado

**Sprints 0 e 1 prontos:** `studio novo`, `studio status` e `studio narracao` funcionam. O
roteiro do vídeo 01 está marcado e gera narração. Existe também `studio duble`, uma voz
sintética temporária que destrava o código enquanto eu não gravo. Os outros comandos existem
no `--help` e respondem "não implementado — sprint N". Plano em [`docs/`](docs/README.md).

```
make setup
make status V=01
make narracao V=01
make duble V=01        # voz falsa, só pra testar o pipeline
```

Próximo: sprint 2, alinhamento.

## Os comandos (alvo)

```
studio novo 01           # cria a pasta do vídeo a partir do template
studio narracao 01       # script.md → narration.txt (o texto que eu leio)
                         # [eu gravo narration.wav]
studio duble 01          # voz sintética temporária, quando eu ainda não gravei
studio alinhar 01        # + wav → words.json + legendas
studio timeline 01       # marcadores + words.json → timeline.json + shorts.json
studio assets 01         # gera as cenas: vhs, freeze, manim, replay, cards
studio montar 01         # → video.mp4 + .srt
studio shorts 01         # → shorts/*.mp4 verticais com legenda queimada
studio thumb 01          # → thumb.png (+ variantes)
studio meta 01           # → título, descrição, capítulos, tags

studio tudo 01           # ← o alvo real
```

## Stack

Python. WhisperX (alinhamento), Manim Community (animação), Playwright (thumb/cards), VHS e
freeze (terminal/código), ffmpeg (montagem), piper (a voz de teste). O Go entra só do lado do
jogo, exportando dados que o pipeline consome.

As dependências pesadas são extras opcionais (`alinhamento`, `assets`, `manim`, `duble`) — o
`studio` em si não depende de nada, e cada sprint só puxa o que precisa.

## Estrutura

```
studio/
  docs/                  ← plano, dividido em sprints
  studio/                ← o pacote Python
  videos/
    01-batalha-naval/
      script.md          ← roteiro aprovado, com marcadores (versionado)
      narration.wav      ← gravado por mim (versionado)
      tapes/*.tape       ← fontes VHS (versionado)
      thumb.vars.json    ← versionado
      build/             ← TUDO descartável, gitignored
        narration.txt        ← o que eu leio, e o que o alinhador recebe
        narration.md         ← a mesma narração com títulos, pra eu ler na tela
        marcadores.json      ← cenas e shorts por índice de palavra
        narration.duble.wav  ← voz sintética, quando eu ainda não gravei
  templates/
```

**Regra:** tudo em `build/` é descartável. Se apagar, um comando reconstrói.
