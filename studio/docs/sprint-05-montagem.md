# Sprint 5 — Montagem

> **Feito.** `studio montar 01` → `build/video.mp4`, 18 cenas, 421,83s em 1920x1080@30, com a
> narração inteira e o `.srt` ao lado. O `--rascunho` sai em 540p em ~40s.
>
> Diferenças do plano abaixo. **Sem cross-fade** (tarefa 3): a transição encadeia os segmentos
> e mataria o cache por cena, que é o que faz trocar o quadro de uma cena que falta custar um
> segmento em vez de sete minutos — fica como dívida em `convencoes.md` §10. **Um MP4 por cena antes do
> concat**, em vez de um `filter_complex` só: custa disco e devolve cache por cena e a
> possibilidade de abrir o segmento que saiu errado.

**Objetivo:** `timeline.json` + `assets/` + áudio → `video.mp4`.

**Este é o marco do projeto.** Até aqui o `studio` me *ajuda* a editar. A partir daqui ele
*monta* o vídeo, e eu só assisto e aprovo.

## Entregável

```
$ studio montar 01
18 cenas, 07:21, 1920x1080 @30fps
  ⚠ web-demo   falta o asset — congela o quadro de bench-rodando
renderizando... 4:12

→ build/video.mp4  (412 MB)
→ build/video.srt
```

E o alvo real:

```
$ studio tudo 01
```

## A rota

**`ffmpeg` direto a partir do `timeline.json`.** O script gera a lista de filtros/concat e
renderiza. Sem interação, reprodutível, roda em CI. Enquanto o vídeo for "narração + tela
cheia + cards" — que é o caso hoje — isso basta.

A alternativa, pra quando doer: emitir **OpenTimelineIO** e abrir no **DaVinci Resolve**
(gratuito, API Python) com tudo já posicionado, ajustando só o que quiser. Mais trabalho de
montar, devolve controle fino sem perder a automação.

Regra: **ffmpeg até a montagem começar a doer.** Não construir o caminho B antes de sentir a
dor — pode ser que nunca chegue.

## Tarefas

1. **Compositor:** para cada cena, um segmento de vídeo com a duração exata da timeline.
   Imagem estática → vídeo da duração certa; vídeo curto demais → segura o último frame;
   longo demais → corta (ou slow-down, configurável por tipo).
2. **Trilha de áudio única:** a narração inteira, intacta. Nunca cortar o áudio pra encaixar
   vídeo — o áudio é a verdade, o vídeo se ajusta.
3. **Transições:** um cross-fade curto padrão (~0.2s). Nada mais. Transição chamativa
   envelhece rápido e distrai.
4. **Legenda** como `.srt` ao lado (não queimada — no longo é opcional, o YouTube usa).
5. **Render em duas qualidades:** rascunho rápido (720p, preset veloz) pra eu revisar em
   ciclo curto, e final (1080p) pra publicar. Vou assistir o rascunho muitas vezes.
6. **`studio tudo`** encadeando os alvos, parando com mensagem clara no primeiro que faltar.

## Critério de pronto

O vídeo 01 sai do `studio montar` **assistível de ponta a ponta**, com áudio sincronizado, e o
único trabalho restante é produzir os assets que ainda faltam — listados em `build/pedidos.md`.

Não precisa estar bonito. Precisa estar **certo**: cena certa, no tempo certo, com o áudio
inteiro.

## O risco deste sprint

O julgamento que ainda não dá pra fazer: **quão longe a montagem automática chega antes do
corte manual dar um vídeo visivelmente melhor?** Só descubro fazendo o 01.

Se a resposta for "o automático é bom o bastante", o projeto ganhou. Se for "dá pra ver que é
robô", a saída é o caminho B (OpenTimelineIO → Resolve): o pipeline entrega tudo posicionado e
eu faço o acabamento. **Nos dois casos o trabalho dos sprints 0–4 se aproveita inteiro** — é
por isso que dá pra correr esse risco.

## Fora de escopo

Shorts (sprint 7), thumb (sprint 8), upload. O comando entrega arquivo; eu subo na mão.
