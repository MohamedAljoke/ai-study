# Sprint 7 — Shorts

**Objetivo:** os trechos marcados no roteiro viram vídeos verticais prontos.

Mecanicamente é quase de graça: o alinhamento já sabe onde cada palavra está, o `shorts.json`
já existe desde o sprint 3. O trabalho real é o **reenquadramento**.

## O princípio

**Short não é vídeo longo cortado no susto. É um trecho que já foi escrito pra se sustentar
sozinho.** Por isso os marcadores vão no roteiro **antes de gravar**: quando eu escrevo o
bloco do `parity`, eu já escrevo sabendo que aqueles 40 segundos são um short.

Isso muda como eu escrevo — o trecho marcado precisa abrir sem depender do que veio antes e
fechar sem prometer o que vem depois. É restrição de **escrita**, não de edição. Nenhum
software conserta isso depois.

## Entregável

```
$ studio shorts 01
4 shorts, 1080x1920

  uma-linha          44.4s  "Uma linha, 15 tiros a menos"
  tabuleiro-xadrez   38.1s  "Por que meu bot pula casas"
  teste-stdout       52.0s  "O teste que me ensinou arquitetura"
  95-para-44         29.7s  "De 95 tiros para 44"

→ build/shorts/*.mp4
```

## O que muda do longo pro short

| | Longo | Short |
|---|---|---|
| Formato | 1920x1080 | **1080x1920** (9:16) |
| Duração | 15–18 min | 20–60s, alvo **~45s** |
| Legenda | opcional (`.srt`) | **queimada**, obrigatório |
| Gancho | 45s de contexto | **primeiros 2 segundos** ou perdeu |
| Fecho | "comenta aí" | nome do canal, sem CTA longo |

## Tarefas

1. **Recorte de áudio e legenda** pelos tempos do `shorts.json`. Trivial — o dado já existe.
2. **Legenda queimada**, palavra a palavra ou frase a frase, tipografia pesada, fundo navy
   translúcido. É o item que mais afeta retenção em short.
3. **Layout vertical.** Duas saídas, e a segunda é claramente melhor:
   - crop central + barras navy em cima e embaixo — rápido, funciona, feio;
   - **template vertical próprio:** faixa de título no topo, o asset no meio já renderizado em
     proporção vertical, legenda embaixo.

   Como VHS, freeze e Manim são scriptados, gerar o mesmo asset em tamanho diferente é só
   mudar um parâmetro. **É a vantagem de ter asset determinístico** — e é o motivo de este
   sprint vir depois do 4 e do 6.
4. **Cartela final** com o nome do canal, ~1s.
5. **Título e legenda de publicação** por short, via LLM a partir do trecho.

## Critério de pronto

Os 4 shorts do vídeo 01 saem publicáveis sem eu abrir editor.

## A regra que vale mais que o software

**Se eu não consegui marcar pelo menos 3 shorts no roteiro, o roteiro provavelmente não tem 3
ideias claras** — sinal de que o vídeo está morno. O comando deve me avisar disso já no sprint
3, quando ainda dá tempo de reescrever.

Ritmo alvo: um short por semana entre os longos.

## Fora de escopo

Upload e agendamento. Eu subo na mão.
