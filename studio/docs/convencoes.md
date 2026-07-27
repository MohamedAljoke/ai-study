# Convenções do `studio`

Regras que valem pra todos os sprints. Se um sprint contradiz isso, o sprint está errado.

## 1. Nada de tempo escrito à mão

Eu **nunca** digito `04:12.3` em lugar nenhum. Eu marco **posição no texto**; o alinhamento
converte posição em tempo. Se eu regravar o áudio mais devagar, todos os tempos se recalculam
sozinhos.

Corolário: qualquer feature que me peça pra ajustar tempo manualmente está resolvendo o
problema errado.

## 2. Todo comando é idempotente e cacheado

Rodar `studio montar 01` duas vezes seguidas não deve refazer nada na segunda. Cache por
**hash das entradas** (arquivo de origem + parâmetros + versão da ferramenta). Isso não é
otimização prematura: um vídeo de sete minutos são dezoito segmentos pra codificar, e eu vou
rodar o pipeline dezenas de vezes por vídeo — trocar um asset tem que custar um segmento.

"Versão da ferramenta" é o **hash do código que gera** (`cache.versao_de(*modulos)`), não um
número que eu lembro de subir. Trocar um asset e receber o segmento velho de volta é o pior
modo de falha do pipeline: silencioso, e faz eu debugar a etapa errada.

## 3. Falta de asset não quebra o render

O studio **não gera mídia**. Toda cena é um arquivo que eu produzo fora — Manim, gravação de
tela, imagem — e largo em `videos/NN-slug/assets/<id>.<ext>`. A extensão é escolha minha; a
busca é por `id`.

Cena que ainda não existe **congela o último quadro da cena anterior** e o vídeo segue. Isso
esconde o buraco de propósito: dá pra assistir o vídeo inteiro, com o ritmo certo, antes de
metade das animações existir. Quando não há nada antes pra congelar — as cenas do começo,
enquanto eu não produzi nada — entra uma cartela navy com o `id`.

Como o vídeo esconde, **o buraco tem que aparecer em outro lugar, sempre**: `build/pedidos.md`
lista cena a cena o que falta e quanto tempo cada uma dura, o `montar` imprime cada cena
congelada com o id de quem ela herdou, e o `status` nunca fica `ok` com asset faltando.

Erro fatal só em coisa que impede o vídeo de existir: roteiro inválido.

Vale pro áudio também: sem a minha gravação, `studio duble` põe uma voz sintética no lugar e o
pipeline anda. O que **não** pode é isso passar despercebido — quem escolhe o áudio é
`Projeto.audio()`, minha voz sempre ganha da sintética, e todo comando que cair no dublê diz
isso na tela.

## 4. `build/` é descartável

Se eu apagar `videos/01-batalha-naval/build/` inteiro, um comando reconstrói tudo. O que entra
no git é: `script.md`, `narration.wav`, `assets/*`, `thumb.vars.json`, templates.

Nunca ler de `build/` uma informação que não dê pra regenerar.

## 5. Artefato entre etapas é JSON legível

Cada etapa lê arquivo e escreve arquivo. Sem estado em memória atravessando comandos, sem
banco. Isso me dá três coisas de graça: rodar etapas isoladas, inspecionar o que deu errado, e
**editar na mão quando a máquina errar** (o alinhador vai errar em `stdout` e `WebSocket` —
o `timeline.json` é só um arquivo).

Pra essa edição valer alguma coisa, ela não pode ser apagada em silêncio: o `.hash` guarda
também o hash da **saída**, e um comando que fosse sobrescrever um arquivo mexido à mão para e
pede `--forcar`. Sem isso a válvula de escape é decorativa.

## 6. IA só em texto

LLM rascunha roteiro, sugere marcadores, escreve título/descrição/tags, compõe cena Manim a
partir da biblioteca existente. LLM **não** gera imagem de thumb (texto sai ruim), não narra,
não edita vídeo.

Toda chamada de LLM é offline e em batch. Nada em tempo real.

## 7. Determinismo antes de esperteza

Entre "gerar com IA" e "gerar com template", template ganha. Entre "detectar automaticamente"
e "declarar no roteiro", declarar ganha. O pipeline tem que produzir o mesmo vídeo hoje e
daqui a seis meses.

## 8. Uma etapa do pipeline por módulo

Geração de voz não mora junto com geração de texto. Medição de áudio não mora junto com
alinhamento. Cada módulo tem **um** assunto, e o nome do arquivo diz qual:

| Módulo | Assunto | O que **não** entra |
|---|---|---|
| `texto.py` | limpar e contar palavra | qualquer I/O |
| `roteiro.py` | o roteiro como dado (tipos) | ler arquivo, validar |
| `leitura.py` | `script.md` → `Roteiro` (sintaxe) | regra de marcador, áudio, tempo |
| `validacao.py` | checar marcador e avisar | ler o markdown |
| `cenas.py` | quais tipos de cena existem | o que fazer com cada uma |
| `audio.py` | **medir** um wav (ffprobe) | sintetizar, alinhar, corrigir |
| `alinhador.py` | texto + áudio → tempo | legenda, formato de saída |
| `legendas.py` | palavras com tempo → srt/vtt | alinhar |
| `artefatos.py` | JSON do `build/` ↔ dataclass | o que fazer com o dado |
| `timeline.py` | índice de palavra → segundo | I/O, aviso, impressão |
| `conferencia.py` | regra de sanidade → aviso | montar a timeline |
| `relogio.py` | segundo → `00:22.4` | formato de legenda (é outro) |
| `marca.py` | as cores do canal | como desenhar qualquer coisa |
| `processos.py` | rodar binário externo → `ErroDeUso` | qual binário chamar |
| `ffmpeg.py` | a linha de comando do ffmpeg | o que renderizar |
| `pedidos.py` | quem fornece cada cena | procurar no disco, formatar |
| `folha.py` | pedidos → o texto do `pedidos.md` | decidir o que falta |
| `substitutos.py` | o quadro de quem falta (congela/cartela) | escolher quem falta |
| `placeholder.py` | a cartela navy com o id | quando usá-la |
| `montagem.py` | pedidos + tempo → plano de render | rodar ffmpeg, imprimir |
| `cache.py` | hash de entrada → refazer ou não | saber o que gera o quê |
| `projeto.py` | caminhos e nomes | conteúdo de arquivo |
| `comandos/*.py` | orquestrar e falar com o terminal | regra de negócio |

**Regra de dependência: os módulos não conhecem os comandos, e não imprimem nada.** `print`
só existe em `comandos/`. Isso é o que deixa a lógica testável sem disco e sem capturar
stdout.

Etapa nova é **arquivo novo**, não um `if` num arquivo existente.

Tipo de cena novo, hoje, é **uma linha em `cenas.py`** e mais nada: o tipo é rótulo do
trabalho que eu tenho que fazer, não motor. O que já foi um registro de geradores (VHS,
freeze, Chrome) virou uma pasta `assets/` e uma folha de pedidos — a versão que sobreviveu
ao teste de "isso aqui está resolvendo o problema certo?".

## 9. Dependência pesada atrás de interface pequena

`alinhador.py` é o modelo a seguir: é o único lugar do projeto que sabe que o WhisperX existe,
e o resto do código só enxerga `alinhar()` e `Alinhada`. O piper só aparece em
`comandos/duble.py`, e o ffmpeg só em `ffmpeg.py`. Ferramenta nova segue o mesmo padrão.

Duas consequências obrigatórias:

- **Import tardio**, dentro da função que usa (`_importar()`). Nada de dependência pesada no
  topo do módulo: `studio --help` tem que responder na hora, e cada extra continua opcional.
- **Ferramenta ausente é `ErroDeUso` com o comando de instalação junto**, nunca um
  `ImportError` cru na cara.

## 10. Tamanho é sintoma

Módulo passando de ~200 linhas ou função passando de ~30 quase sempre quer dizer que tem duas
coisas ali dentro. Não é limite de contagem, é gatilho pra olhar.

Dívida conhecida: **sem transição na montagem.** O `docs/sprint-05` pede um cross-fade de
~0.2s e a v1 corta seco. O motivo é estrutural: cross-fade encadeia os segmentos e mata o
cache por cena, que é o que faz trocar um quadro congelado por mídia de verdade custar um
segmento em vez de sete minutos. Entra quando o vídeo já estiver assistível e a decisão for
estética, não estrutural.

Dívida conhecida: **três formatações de tempo** no projeto — `relogio.py`, os timestamps do
`legendas.py` e o `formatar_duracao` do `texto.py`. Não são a mesma função (o SRT tem vírgula
decimal e hora obrigatória), mas duas delas provavelmente são. Consolidar tem um custo
específico: a `FERRAMENTA` do `alinhar` hasheia `legendas` e `texto`, então mexer ali obriga um
realinhamento inteiro do WhisperX. O momento certo é junto da próxima gravação, que realinha
de qualquer jeito.

## 11. Teste é o contrato

**Não tem revisão humana neste projeto.** O teste é a única coisa que segura as regras acima,
então ele não é opcional:

- Toda lógica pura entra com teste junto — mesmo commit, não "depois".
- Bug encontrado vira **teste que falha** antes do conserto. Nunca conserta sem reproduzir.
- O nome do teste descreve o comportamento em português
  (`test_repeticao_no_audio_nao_desalinha_o_resto`), não o método que ele chama. Quem lê a
  lista de testes tem que entender o que o módulo promete.
- Testar o que dói: reconciliação de índice, buraco, ponta, entrada vazia, arquivo que sumiu.
  Não testar getter.
- `make test` e `make check` limpos antes de qualquer commit.

Sem teste, `cenas.py` e `cli.py` — os dois que ainda não têm.

O que não pode ficar sem teste é a escolha de quem fornece cada cena (`pedidos.py`) e o
cálculo de tempo da montagem, que é onde um erro passa despercebido até eu assistir os sete
minutos.

## 12. Uma etapa se debuga sozinha

O teste de qualquer desenho novo: **quando algo sair errado na etapa X, dá pra mexer só nela?**
As quatro coisas abaixo têm que valer pra toda etapa.

**Roda sozinha.** `make narracao V=01` refaz só o roteiro, sem realinhar nada. Nenhuma etapa
depende de rodar a anterior na mesma sessão — depende do **arquivo** que a anterior deixou.

**Entrada e saída são arquivos que eu consigo abrir** (§5). Debugar é comparar
`script.md` com `build/marcadores.json`, não colocar `print` no meio do código.

**O erro aponta o lugar exato.** Erro de roteiro cita arquivo e linha do `script.md`, no
formato `script.md:70: id 'play-demo' já usado na linha 42` — eu pulo direto pra lá. Erro que
diz só "id duplicado" está incompleto.

**A lógica roda sem projeto nenhum.** `roteiro.interpretar()` recebe uma **string**, não um
`Projeto` — dá pra reproduzir um bug no REPL com três linhas e o trecho do markdown que
quebrou. Toda etapa nova segue isso: a função pura recebe dado, o comando é quem sabe de
caminho e de disco.

### Onde mexer

| Quando o problema é… | Roda | Olha | Mexe em | Teste |
|---|---|---|---|---|
| marcador não reconhecido, parágrafo no lugar errado | `make narracao V=01` | `build/narration.txt`, `build/marcadores.json` | `leitura.py` | `test_roteiro.py`, `test_leitura.py` |
| cena recusada, aviso de fonte que falta | `make narracao V=01` | a mensagem `script.md:NN:` | `validacao.py` | `test_validacao.py` |
| markdown ou pontuação lida errado | `make narracao V=01` | `build/narration.txt` | `texto.py` | `test_texto.py` |
| voz sintética, ritmo do dublê | `make duble V=01` | `build/narration.duble.wav` | `comandos/duble.py` | — |
| wav recusado, aviso de LUFS | `make alinhar V=01` | o cabeçalho impresso | `audio.py` | `test_audio.py` |
| palavra no tempo errado | `make alinhar V=01` | `build/words.json` | `alinhador.py` | `test_alinhador.py` |
| legenda cortada feio | `make alinhar V=01` | `build/narration.srt` | `legendas.py` | `test_legendas.py` |
| cena entra no segundo errado | `make timeline V=01` | `build/timeline.json` | `timeline.py` | `test_timeline.py` |
| aviso de short/cena que não faz sentido | `make timeline V=01` | os avisos impressos | `conferencia.py` | `test_conferencia.py` |
| JSON do `build/` recusado | `make timeline V=01` | a mensagem do erro | `artefatos.py` | `test_artefatos.py` |
| duração ou fala errada na encomenda de uma cena | `make pedidos V=01` | `build/pedidos.md` | `folha.py` | `test_folha.py` |
| asset que eu larguei não foi reconhecido | `make pedidos V=01` | a coluna `pronto/falta` | `pedidos.py`, `projeto.asset_de` | `test_pedidos.py` |
| cena congelou o quadro da cena errada | `make pedidos V=01` | `build/pedidos.md` | `pedidos.py` | `test_pedidos.py` |
| quadro congelado saiu preto ou torto | `make montar V=01` | `build/substitutos/<id>.png` | `substitutos.py`, `ffmpeg.py` | `test_ffmpeg.py` |
| cena certa no tempo errado no vídeo | `make montar V=01` | `build/segmentos/<perfil>/<id>.mp4` | `montagem.py` | `test_montagem.py` |
| vídeo dessincronizado do áudio no fim | `make montar V=01` | `ffprobe build/video.mp4` | `montagem.py` | `test_montagem.py` |
| enquadramento, codec, cor de fundo da borda | `make montar V=01` | um segmento solto | `ffmpeg.py` | `test_ffmpeg.py` |
| refez o que não devia (ou não refez) | qualquer um, duas vezes | os `.hash` no `build/` | `cache.py` | `test_cache.py` |

Etapa nova entra nesta tabela **no mesmo commit** em que nasce.

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
- Caminho em marcador: `arquivo=` é relativo à **raiz do repositório**, porque aponta pro
  código de verdade do `projects/battleships/`. É o único caminho que o studio confere —
  `dados=` e `nota=` são recado meu, e saem na folha de pedidos como estão.
- O asset de uma cena **não é declarado**: é `assets/<id>.<ext>`, achado pelo id.
- Comandos em português (`narracao`, `montar`, `alinhar`) — é ferramenta minha, o canal é
  pt-BR, e não tem custo de tradução.
