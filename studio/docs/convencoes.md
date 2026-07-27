# Convenções do `studio`

Regras que valem pra todos os sprints. Se um sprint contradiz isso, o sprint está errado.

## 1. Nada de tempo escrito à mão

Eu **nunca** digito `04:12.3` em lugar nenhum. Eu marco **posição no texto**; o alinhamento
converte posição em tempo. Se eu regravar o áudio mais devagar, todos os tempos se recalculam
sozinhos.

Corolário: qualquer feature que me peça pra ajustar tempo manualmente está resolvendo o
problema errado.

## 2. Todo comando é idempotente e cacheado

Rodar `studio assets 01` duas vezes seguidas não deve refazer nada na segunda. Cache por
**hash das entradas** (arquivo de origem + parâmetros + versão da ferramenta). Isso não é
otimização prematura: o Manim leva minutos por cena e eu vou rodar o pipeline dezenas de
vezes por vídeo.

"Versão da ferramenta" é o **hash do código que gera** (`cache.versao_de(*modulos)`), não um
número que eu lembro de subir. Consertar um gerador e receber o arquivo velho de volta é o
pior modo de falha do pipeline: silencioso, e faz eu debugar a etapa errada.

## 3. Falta de asset não quebra o render

Se uma cena ainda não existe — gravação minha que não fiz, Manim que não renderizou — o
pipeline gera um **placeholder navy com o `id` escrito em cima** e segue. Eu assisto o vídeo
inteiro e sei exatamente o que falta.

Erro fatal só em coisa que impede o vídeo de existir: roteiro inválido.

Vale pro áudio também: sem a minha gravação, `studio duble` põe uma voz sintética no lugar e o
pipeline anda. O que **não** pode é isso passar despercebido — quem escolhe o áudio é
`Projeto.audio()`, minha voz sempre ganha da sintética, e todo comando que cair no dublê diz
isso na tela. Placeholder serve pra eu ver o que falta, nunca pra esconder.

## 4. `build/` é descartável

Se eu apagar `videos/01-batalha-naval/build/` inteiro, um comando reconstrói tudo. O que entra
no git é: `script.md`, `narration.wav`, `tapes/*.tape`, `thumb.vars.json`, templates.

Nunca ler de `build/` uma informação que não dê pra regenerar.

## 5. Artefato entre etapas é JSON legível

Cada etapa lê arquivo e escreve arquivo. Sem estado em memória atravessando comandos, sem
banco. Isso me dá três coisas de graça: rodar etapas isoladas, inspecionar o que deu errado, e
**editar na mão quando a máquina errar** (o alinhador vai errar em `stdout` e `WebSocket` —
o `timeline.json` é só um arquivo).

## 6. IA só em texto

LLM rascunha roteiro, sugere marcadores, escreve título/descrição/tags, compõe cena Manim a
partir da biblioteca existente. LLM **não** gera imagem de thumb (texto sai ruim), não narra,
não edita vídeo.

Toda chamada de LLM é offline e em batch. Nada em tempo real.

## 7. Determinismo antes de esperteza

Entre "gerar com IA" e "gerar com template", template ganha. Entre "detectar automaticamente"
e "declarar no roteiro", declarar ganha. O pipeline tem que produzir o mesmo vídeo hoje e
daqui a seis meses.

## Cores da marca

| Uso | Hex |
|---|---|
| Fundo / navy | `#122440` |
| Texto / logo | `#FFFFFF` |
| Fundo alternativo | `#1B3157` |
| Acento (só no número/palavra-chave) | `#FFB020` |

O acento aparece em **um** elemento por peça. Nunca dois.

## Nomes

- Vídeo: `NN-slug` → `01-batalha-naval`. O `NN` é o argumento dos comandos.
- `id` de cena e de short: kebab-case, único dentro do vídeo, vira nome de arquivo.
- Caminho em marcador: `fonte=` e `dados=` são relativos à **pasta do vídeo**; `arquivo=` é
  relativo à **raiz do repositório**, porque aponta pro código de verdade do `battleships/`.
- Comandos em português (`narracao`, `montar`, `alinhar`) — é ferramenta minha, o canal é
  pt-BR, e não tem custo de tradução.
