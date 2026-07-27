# Sprint 2 — Áudio e alinhamento

**Objetivo:** saber **quando** cada palavra foi dita.

É a peça técnica que segura o pipeline inteiro. Sem ela, eu volto a marcar tempo na mão e o
projeto perde a razão de existir.

## O que já existe

`build/narration.txt` (1.069 palavras) e `build/marcadores.json` com o índice de palavra de
cada cena e short.

O wav mora na raiz da pasta do vídeo, não em `build/` ([convenções §4](convencoes.md)): é o
artefato caro e insubstituível do vídeo inteiro, não pode viver num diretório que eu apago sem
pensar.

## O dublê

`studio duble 01` gera `build/narration.duble.wav`: voz sintética (piper, `pt_BR-faber-medium`)
lendo o `narration.txt`, freada pro ritmo alvo. **Mesmas palavras, mesma ordem** — que é tudo
que o alinhador precisa. Serve pra escrever e testar os sprints 2 a 5 antes de eu gravar.

Três regras que impedem o dublê de virar vídeo publicado por acidente:

- mora em `build/`, com nome próprio, e nunca sobrescreve `narration.wav`;
- `Projeto.audio()` é o único jeito de descobrir qual áudio usar, e **a minha voz sempre
  ganha** — gravar é o bastante pra trocar, sem apagar nada nem mudar comando;
- todo comando que cair no dublê avisa, e o `status` carimba `⚠ rodando com dublê`.

O que o dublê **não** substitui: ritmo, ênfase e pausa de gente. Um corte que funciona na voz
sintética pode não funcionar na minha. Ele valida o código, não a edição.

## O ponto importante

Isso é **forced alignment**, não transcrição. Eu **já sei o texto** (`narration.txt` do sprint
1); quero descobrir o timestamp de cada palavra. Alinhar texto conhecido é bem mais preciso do
que transcrever e torcer pra bater.

## Entregável

```
$ studio alinhar 01
áudio: 07:21 (441.3s), -16.2 LUFS, mono 48k  ok
alinhando 1.069 palavras... (whisperx, pt, cpu)
1.069/1.069 alinhadas, confiança média 0.94
12 palavras com confiança < 0.5:
  "stdout" (03:12), "WebSocket" (06:41), "benchmark" (05:03) ...

→ build/words.json
→ build/narration.srt
→ build/narration.vtt
```

```json
{"word": "parity", "start": 623.41, "end": 623.88, "score": 0.97}
```

As legendas saem **de graça** aqui — é o mesmo dado. Isso já é útil sozinho, antes de qualquer
montagem automática existir.

## Tarefas

1. **Checagem do áudio** antes de alinhar: existe, duração plausível pro texto, mono/48k,
   loudness perto de **-16 LUFS**. Avisa e sugere o comando de correção; não corrige sozinho.
2. **Alinhador: WhisperX**, modelo pt, saída palavra a palavra. Isolar atrás de uma interface
   pequena — WhisperX é a escolha, mas é a dependência mais pesada e mais provável de trocar
   (aeneas e stable-ts são as alternativas).
3. **`words.json`** com `word`, `start`, `end`, `score` e **índice da palavra** — é o índice
   que casa com os marcadores do sprint 1. Sem ele, o sprint 3 não tem como ligar as pontas.
   A contagem tem que sair de `texto.palavras`, o mesmo tokenizador que gerou os marcadores;
   se cada etapa contar do seu jeito, os índices não batem e o pipeline mente sem quebrar.
4. **Legendas** `.srt` e `.vtt`, agrupando palavras em linhas legíveis (~40 caracteres, quebra
   na pontuação).
5. **Relatório de baixa confiança.** Termo técnico em inglês no meio do português (`stdout`,
   `benchmark`, `WebSocket`) é onde o alinhador erra. Listar os piores com timestamp pra eu
   conferir no player.
6. **Cache.** Alinhar leva minutos. Não realinhar se `narration.txt` e o `.wav` não mudaram —
   `cache.precisa_refazer`, com a versão da ferramenta vinda de `cache.versao_de`.

## Critério de pronto

- Abrir o `.srt` gerado num player junto com o áudio e as legendas baterem, de ponta a ponta,
  sem drift acumulado.
- Um erro de leitura meu (frase repetida) não pode desalinhar o resto do vídeo — ou o
  alinhador se recupera, ou o comando aponta onde texto e áudio divergiram.

Esse segundo ponto é o risco real do sprint. Alinhador que desalinha depois de um erro no
minuto 3 inutiliza os 15 minutos seguintes.

## Sobre gravar

Fora do software, mas define a qualidade da entrada:

| Coisa | Escolha |
|---|---|
| Gravar | Audacity, ou OBS em faixa separada |
| Limpar | **Auphonic** (~1 clique) ou `ffmpeg` + `arnndn` local |
| Alvo | **-16 LUFS**, mono, 48kHz WAV |

Errei uma frase: repito e sigo. **Deleto a tomada ruim antes de alinhar** — o alinhador
espera que áudio e texto batam.

## Fora de escopo

- TTS na narração publicada. O canal é primeira pessoa; voz sintética mata isso. O dublê acima
  é ferramenta de desenvolvimento e morre em `build/`. (TTS de verdade só faria sentido pra
  versão em inglês, que não está decidida.)
- Correção automática de áudio. O comando avisa, eu corrijo.
- Cenas, tempos de cena, montagem. Aqui só existe palavra e segundo.
