# Sprint 3 — Timeline

**Objetivo:** juntar as duas metades — marcadores (posição no texto) + palavras (tempo) — e
produzir o artefato central do pipeline.

Sprint pequeno e puramente de dados. Nenhum vídeo é gerado aqui, e mesmo assim ele é o mais
importante depois do sprint 2: **tudo que vem depois só consome o `timeline.json`.**

## Entregável

```
$ studio timeline 01
18 cenas posicionadas, 4 shorts
duração total 07:21

  00:00.0  card      abertura
  00:22.4  terminal  play-demo          (tapes/play.tape)
  02:41.9  codigo    parse-position     (internal/game/position.go:12-28)
  06:10.2  manim     density-mapa       (HeatMap, turnos 1-12)
  11:03.7  tela      web-demo           ⚠ sem gravação
  ...

aviso: cena 'abertura' dura 22s — card estático longo demais
```

```json
{
  "video": "01-batalha-naval",
  "audio": "narration.wav",
  "duracao": 1082.4,
  "cenas": [
    { "id": "play-demo", "tipo": "terminal", "inicio": 180.2, "fim": 300.7,
      "fonte": "tapes/play.tape", "asset": "build/assets/play-demo.mp4" }
  ]
}
```

E um `shorts.json`:

```json
{ "id": "uma-linha", "titulo": "Uma linha, 15 tiros a menos",
  "inicio": 745.2, "fim": 789.6, "duracao": 44.4,
  "origem": "01-batalha-naval", "legenda": "queimada" }
```

## Tarefas

1. **Casar marcador com palavra.** Cada marcador guarda o índice da palavra onde começa
   (sprint 1); `words.json` dá o `start` daquele índice (sprint 2). Fim da cena = início da
   próxima. Última cena termina no fim do áudio.
2. **Resolver os shorts** do mesmo jeito, mas com abre e fecha explícitos — e sem exigir que
   coincidam com bordas de cena.
3. **Validar contra a realidade:** short fora de 20–60s, cena com duração negativa (marcador
   fora de ordem), buraco sem cena nenhuma, cena de 2 segundos.
4. **Impressão legível** da timeline no terminal, marcando o que ainda não tem asset. É a
   saída que eu vou olhar mais vezes.
5. **`timeline.json` editável à mão.** O alinhador vai errar em alguma palavra técnica; eu
   preciso poder ajustar um tempo direto no arquivo. Rodar `studio timeline` de novo
   sobrescreve — então o comando avisa se o arquivo foi editado depois de gerado.

Esse último ponto é a válvula de escape do pipeline inteiro. Sem ela, um erro do WhisperX me
obriga a regravar o áudio.

## Critério de pronto

- `studio timeline 01` no vídeo 01 real produz uma lista de tempos que bate com o áudio
  quando eu confiro 3 ou 4 pontos no player.
- Os 4 shorts caem todos dentro de 20–60s. Se não caírem, o problema é de **escrita** do
  roteiro, não do software — e é exatamente isso que o aviso tem que me dizer.

## Já dá pra usar assim

Mesmo sem montagem automática, o `timeline.json` sozinho **já elimina a parte mais chata da
edição manual**: eu abro o editor, importo o áudio, e sei exatamente em que segundo colocar
cada coisa em vez de ficar procurando.

Se por qualquer motivo o projeto parar aqui, os sprints 0–3 já pagaram o custo.

## Fora de escopo

Gerar qualquer asset. A timeline aponta pra caminhos de arquivo que provavelmente ainda não
existem — e tudo bem.
