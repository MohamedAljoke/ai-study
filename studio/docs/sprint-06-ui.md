# Sprint 6 — A interface local

**Objetivo:** o fluxo inteiro numa página só — escrever o roteiro, largar o áudio, largar os
assets cena por cena — sem eu abrir o terminal.

```
studio ui        → http://127.0.0.1:8730
```

O sprint 6 era o do Manim. Ele saiu do plano quando o studio virou orquestrador, e o número
ficou vago. Este sprint ocupou o lugar por um motivo melhor: depois do sprint 5 o pipeline
estava completo e **o trabalho ficou repetitivo do jeito errado**. Produzir os 18 assets do
vídeo 01 é ler o `pedidos.md`, copiar um arquivo pra `assets/<id>.<ext>`, rodar
`make pedidos` pra confirmar, e repetir. Dezoito vezes.

## O que a página faz

Três seções, na ordem em que eu trabalho — e um **`+ novo`** no cabeçalho, porque senão a
página só sabe continuar vídeo que já existe, e conteúdo novo obrigava a voltar pro terminal.
Ele pede o `NN-slug`, cria `videos/NN-slug/` com o `script.md` do template e já abre no
roteiro, que é o próximo passo dele. Com `videos/` vazio, é a única coisa na tela.

1. **roteiro** — editor do `script.md` com a prévia ao lado: o texto que eu vou ler, a
   contagem de palavras, a duração estimada, as cenas e os shorts detectados. Salvar
   reinterpreta na hora, e roteiro inválido aparece como `script.md:42: id 'x' já usado na
   linha 30` — o mesmo formato do terminal (§12).
2. **áudio** — largo o `narration.wav` em cima da página. Mostra quando estou rodando com
   dublê, que é voz sintética e não vai pro ar.
3. **cenas** — um card por cena, na ordem do vídeo, com **duração exata, os params do
   marcador e o trecho da narração que toca durante ela**. Arrasto o arquivo em cima do card
   e ele vira `assets/<id>.<ext>`.

Cada etapa tem botão, e o log escorre ao vivo numa gaveta no rodapé — `alinhar` leva minutos,
e página parada sem sinal de vida é indistinguível de página travada.

## O que a página **não** faz

- **Não grava áudio.** A voz é minha, lida do `build/narration.md`, com o microfone que eu
  já uso. Navegador gravando voz seria a pior versão disso.
- **Não produz mídia.** Continua valendo o §3: todo asset é feito fora, principalmente em
  Manim. A página encomenda e recebe.
- **Não tem regra de pipeline.** Nenhuma.

Esse último item é o critério de projeto do sprint inteiro.

## A casca não decide nada

`studio/ui/` é casca, na mesma categoria de `comandos/`. Toda pergunta que a página faz já
tem dono:

| Pergunta | Quem responde |
|---|---|
| esse nome de vídeo vale? | `comandos/novo.criar` → `projeto.validar_nome` |
| em que passo o vídeo está | `comandos/status.etapas` |
| qual é o próximo passo | `comandos/status.proximo` |
| quem fornece cada cena | `comandos/pedidos.levantar` |
| o roteiro é válido? | `leitura.ler` |
| onde cada arquivo mora | `projeto.Projeto` |

Se a página souber responder qualquer uma dessas sozinha, ela vai discordar do terminal — e
divergência silenciosa entre a folha e o que o vídeo mostra é exatamente o modo de falha que
o `pedidos.py` foi escrito pra impedir. O teste que fecha o sprint é esse: `studio status 01`
e a barra de etapas dizem a mesma coisa, porque leem a mesma função.

Por isso `ui/estado.py` é puro e é onde mora o teste. `ui/servidor.py` só serializa.

## Rodar etapa é subprocesso

`ui/tarefas.py` roda `python -m studio.cli <comando> <NN>` e lê o stdout linha a linha. Não é
chamada direta da função do comando, e isso é decisão, não preguiça: mantém o torch e o
ffmpeg fora do processo do servidor, faz uma etapa travada não derrubar a página, e o log
vira literalmente o que eu veria no terminal.

Uma etapa por vez — duas montagens simultâneas brigariam pelo mesmo `build/segmentos/`.

A flag também não vem do cliente: `_argumentos` só aceita opção **declarada no `PIPELINE`**
do `cli.py`. Deixar a página escolher argumento de subprocesso seria transformar um botão em
shell.

## O que a página escreve no disco

Quatro coisas, e as quatro com guarda:

- **`videos/NN-slug/`** — o nome passa pelo `validar_nome`, e criar por cima de vídeo que
  existe é recusado. A página não pode virar o jeito mais fácil de apagar roteiro por cima.

- **`script.md`** — a página manda de volta a assinatura do arquivo que carregou. Se ele
  mudou no disco no meio (eu abri no editor), o servidor recusa em vez de sobrescrever. É o
  mesmo princípio do `--forcar` do `timeline` (§5): conserto meu não some em silêncio.
- **`assets/<id>.<ext>`** — o `id` tem que existir na timeline; a extensão vem do arquivo
  enviado e passa por lista branca. A versão anterior é apagada antes, senão dois arquivos
  com o mesmo id fazem o `asset_de` recusar a cena inteira.
- **`narration.wav`** — só `.wav`, que é o que o alinhador lê.

O servidor escuta em `127.0.0.1` e ponto. É ferramenta minha, na minha máquina: não tem login
e não deve ter.

## Instalação

O FastAPI é extra opcional (§9): o `studio` inteiro funciona sem ele, e `studio --help`
responde na hora porque o import é tardio.

```
uv sync --extra ui        # ou make setup, que traz os três extras
```

## Critério de pronto

Do `script.md` ao `video.rascunho.mp4` sem abrir o terminal. ✅

## O que ficou fora

- **Editar a timeline na página.** Mexer em tempo à mão contradiz o §1. O `timeline.json`
  continua editável no editor de texto, que é onde essa válvula de escape deve doer um pouco.
- **Marcar cena clicando no texto.** Tentador, e provavelmente a próxima coisa — mas o
  marcador no `script.md` é a fonte da verdade, e um editor visual que gera markdown é um
  segundo parser pra manter.
- **Ver a página de outra máquina.** Se um dia eu quiser revisar o rascunho no celular, isso
  é upload pra algum lugar, não abrir o servidor pra rede.
