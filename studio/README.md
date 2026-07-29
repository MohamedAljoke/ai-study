# studio

Ferramenta interna de produção de vídeo do canal. Transforma um **roteiro aprovado + um áudio
gravado por mim** em **vídeo, shorts, legendas, thumb e metadados prontos pra publicar**.

O desenho do fluxo está em [`content/pipeline-producao.md`](../content/pipeline-producao.md).
Este diretório é a implementação.

## O que é meu, o que é da máquina

Eu faço três coisas: **aprovo o roteiro**, **leio em voz alta** e **produzo as cenas** — Manim,
gravação de tela, imagem. O `studio` faz as três mecânicas: converte posição no texto em tempo,
me diz o que produzir e com que duração, e junta tudo com a narração.

**O studio não gera mídia.** Ele orquestra. Por quê, em
[docs/README.md](docs/README.md#o-studio-é-orquestrador-não-gerador).

## Estado

**Sprints 0 a 6 prontos — o pipeline vai do `script.md` ao `video.mp4`, com interface.** O
vídeo 01 tem 18 cenas, 07:02, e monta inteiro com qualquer subconjunto dos assets pronto:
cena que ainda não existe congela o último quadro da anterior, e o que falta aparece em
`build/pedidos.md`, não no silêncio ([convenção §3](docs/convencoes.md)). Plano em
[`docs/`](docs/README.md).

```
make setup             # ambiente Python (o ffmpeg vem do sistema)

make ui                # ← a página: roteiro, áudio e assets num lugar só

make status V=01
make narracao V=01     # → narration.txt, o texto que eu leio
make duble V=01        # voz falsa, só pra testar o pipeline
make alinhar V=01      # → words.json + legendas
make timeline V=01     # → timeline.json + shorts.json
make pedidos V=01      # → build/pedidos.md, o que eu tenho que produzir
                       # [eu produzo e largo em assets/<id>.<ext>]
make montar V=01       # → build/video.mp4
make rascunho V=01     # o mesmo em 540p, pra revisar em ciclo curto

make tudo V=01         # tudo isso em ordem
```

O `make ui` faz o mesmo que os alvos abaixo, numa página escura: editar e validar o roteiro,
largar o `narration.wav`, e largar o arquivo de cada cena num card que já mostra a duração
exata e o trecho que eu falo nela. O terminal continua valendo pra tudo — a página é casca
([sprint 6](docs/sprint-06-ui.md)).

Próximo: as animações do vídeo 01 em Manim — trabalho fora do studio — e o sprint 7 (shorts).

## Os comandos (alvo)

```
studio novo 01           # cria a pasta do vídeo a partir do template
studio narracao 01       # script.md → narration.txt (o texto que eu leio)
                         # [eu gravo narration.wav]
studio duble 01          # voz sintética temporária, quando eu ainda não gravei
studio alinhar 01        # + wav → words.json + legendas
studio timeline 01       # marcadores + words.json → timeline.json + shorts.json
studio pedidos 01        # → pedidos.md: o que produzir, com duração e fala
                         # [eu produzo e largo em assets/<id>.<ext>]
studio ui                # a mesma coisa numa página, com drag & drop
studio montar 01         # → video.mp4 + .srt
studio shorts 01         # → shorts/*.mp4 verticais com legenda queimada
studio thumb 01          # → thumb.png (+ variantes)
studio meta 01           # → título, descrição, capítulos, tags

studio tudo 01           # ← o alvo real
```

## Stack

Python. WhisperX (alinhamento), ffmpeg (montagem), piper (a voz de teste), FastAPI (a
interface local), Playwright (thumb, sprint 8). Manim é ferramenta minha, fora do pipeline. O
Go entra só do lado do jogo, exportando dados que as animações consomem.

As dependências pesadas são extras opcionais (`alinhamento`, `duble`, `ui`) — o `studio` em si
não depende de nada, e cada sprint só puxa o que precisa. A página é HTML, CSS e JavaScript
escritos à mão: sem framework, sem build, sem `node_modules`.

## Estrutura

```
studio/
  docs/                  ← plano, dividido em sprints
  studio/                ← o pacote Python
  videos/
    01-batalha-naval/
      script.md          ← roteiro aprovado, com marcadores (versionado)
      narration.wav      ← gravado por mim (versionado)
      assets/<id>.<ext>  ← a mídia de cada cena, produzida por mim (versionado)
      thumb.vars.json    ← versionado
      build/             ← TUDO descartável, gitignored
        narration.txt        ← o que eu leio, e o que o alinhador recebe
        narration.md         ← a mesma narração com títulos, pra eu ler na tela
        marcadores.json      ← cenas e shorts por índice de palavra
        narration.duble.wav  ← voz sintética, quando eu ainda não gravei
        words.json           ← o segundo de cada palavra
        timeline.json        ← cena X entra em 04:12.3   ← o artefato central
        pedidos.md           ← o que produzir: id, duração, fala   ← a encomenda
        substitutos/         ← o quadro congelado de quem ainda não existe
        segmentos/           ← cada cena já normalizada, pra emendar
        video.mp4            ← o alvo
  templates/
```

**Regra:** tudo em `build/` é descartável. Se apagar, um comando reconstrói.
