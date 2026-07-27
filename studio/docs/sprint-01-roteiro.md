# Sprint 1 — Roteiro e marcadores

> **Feito.** `studio narracao 01` roda no roteiro real. O formato de marcador definido aqui é
> o contrato dos sprints 2–8.

**Objetivo:** o roteiro vira uma fonte de dados, sem deixar de ser um markdown legível.

Este é o sprint que define o **formato** do qual todo o resto depende. Errar aqui custa caro
depois, porque os roteiros já escritos teriam que ser migrados.

## O que já existe

> **Feito.** O roteiro vive em `videos/01-batalha-naval/script.md`, marcado com 18 cenas e os
> 4 shorts. `studio narracao 01` roda nele.

Antes: `content/video-01-batalha-naval.md` — roteiro completo do vídeo 01, em pt-BR, com
narração em blocos `>` e "o que mostrar na tela" em texto normal. Os 4 shorts estavam
**listados** no fim do arquivo, mas **não marcados** no corpo.

## Entregável

```
$ studio narracao 01
narration.txt — 1.069 palavras, ~7min07 a 150 wpm
18 cenas: 5 codigo, 4 terminal, 3 tela, 3 manim, 2 card, 1 replay
4 shorts: 95-para-44 (~30s), teste-stdout (~53s), uma-linha (~27s), terminal-para-web (~45s)

avisos:
  21x código na narração — eu leio diferente do que está escrito
  11x dígito na narração — eu leio "noventa e cinco", o alinhador vê "95"
  7x fonte de cena que ainda não existe — o sprint 4 cria
  cena 'web-demo' é tipo=tela — precisa de gravação minha
```

Sai um `build/narration.txt` que é **exatamente** o que eu leio em voz alta — e exatamente o
que o alinhador vai receber no sprint 2. Os dois serem o mesmo arquivo é o que faz o
alinhamento ser confiável.

Junto saem `build/narration.md` (mesma narração com título de bloco e marcador visível, pra eu
ler na tela sem me perder) e `build/marcadores.json` (o que o sprint 3 cruza com os tempos).
**As palavras faladas são idênticas nos dois** — se divergirem, o alinhamento mente.

## O formato

Marcadores são comentários HTML: não renderizam, não atrapalham a leitura do roteiro.

```markdown
<!-- cena: terminal id=play-demo fonte=tapes/play.tape -->
> Loop clássico: pergunta, lê, valida, repete.

<!-- cena: codigo id=parse-position arquivo=internal/game/position.go linhas=12-28 -->
> Repara numa coisa: quase todo o meu main.go é conversa com humano.

<!-- cena: manim id=density-mapa classe=HeatMap dados=build/01/density.json turnos=1-12 -->
> Pra cada casa, conto de quantas maneiras os navios caberiam ali.

<!-- short: inicio id=uma-linha titulo="Uma linha, 15 tiros a menos" -->
> O menor navio ocupa duas casas...
<!-- short: fim id=uma-linha -->
```

Regras:

- Um marcador vale **a partir da primeira palavra do parágrafo seguinte**, até o próximo
  marcador de cena.
- `short` é independente de `cena` e **pode se sobrepor** — um short atravessa duas cenas ou
  pega metade de uma. São dois eixos separados sobre o mesmo texto.
- Só linhas `>` entram na narração. Títulos, tabelas e notas de produção são pra mim.
- `id` único no vídeo, kebab-case, vira nome de arquivo.

## Tarefas

1. **Parser do roteiro** → uma estrutura com: blocos de narração (texto + posição de palavra
   inicial/final), cenas, shorts.
2. **Extração da narração.** Linhas `>` → texto limpo, sem markdown, com pontuação
   preservada (o alinhador usa pontuação). Números por extenso é decisão de escrita, não do
   parser — mas o comando avisa quando encontra dígito, porque eu leio "noventa e cinco" e o
   alinhador vê "95".
3. **Índice de palavras.** Cada marcador guarda o **índice da palavra** onde começa. É essa
   posição que o sprint 3 converte em tempo. Palavra é a unidade, não caractere nem linha.
4. **Validação** com mensagem útil e número de linha: `id` duplicado, `short` sem fecho,
   `cena` com tipo desconhecido, `id` fora de kebab-case, parâmetro obrigatório faltando,
   `arquivo=` inexistente, `linhas=` fora do arquivo.
5. **Estimativa de duração** por contagem de palavras. Serve pra saber se o vídeo estourou
   antes de gravar 18 minutos.
6. **Migrar o vídeo 01:** mover o roteiro e **marcar as cenas e os 4 shorts** no corpo.

## Critério de pronto

- `studio narracao 01` roda no roteiro real do vídeo 01 e produz um `narration.txt` que eu
  consigo ler em voz alta de cabo a rabo sem editar nada.
- Roteiro quebrado dá erro com linha e explicação, não stack trace.

O teste de verdade é o primeiro: se eu preciso corrigir o `narration.txt` na mão antes de
gravar, o parser está errado — e o alinhamento do sprint 2 vai quebrar, porque texto e áudio
não vão bater.

## O que o roteiro real mudou no plano

Três coisas que só apareceram quando o parser rodou em 367 linhas de verdade:

**Limpeza é por parágrafo, não por linha.** `**A dor do teste ... onde cortar o\n> código.**`
deixava `código.**` na narração, porque negrito atravessa quebra de linha. `texto.py` separa
`sem_citacao` (por linha, tira o `>`) de `limpar_bloco` (no parágrafo inteiro, tira ênfase,
link e crase).

**A versão da ferramenta sai do código dela.** Consertado o bug acima, o comando não regerou
nada: o `script.md` não tinha mudado e o hash bateu. `cache.versao_de(*modulos)` passa a
hashear o fonte de quem gera, então mudar o parser invalida o cache sozinho.

**Fonte que ainda não existe é aviso, não erro.** O plano pedia erro em `fonte=` inexistente,
mas os `.tape` e o `density.json` só nascem no sprint 4 — a regra tornaria o roteiro
impossível de marcar antes da hora. Cada tipo de cena declara seus caminhos como `fontes`
(tem que existir hoje → erro) ou `adiados` (nasce depois → aviso). Referência a código que já
existe (`arquivo=`) continua erro duro.

E o número que o comando passou a repetir toda vez: **7min07 de fala contra os 15–18
planejados**. Isso é sinal de escrita, não de software — mas agora eu vejo antes de gravar, e
não depois de montar.

## Onde a IA entra

- Rascunhar e revisar o roteiro (o maior ganho de LLM no projeto inteiro — mas eu decido).
- **Sugerir os marcadores** a partir de um roteiro já pronto: passa o `.md`, devolve onde
  cada cena entra e qual tipo.
- Sugerir onde marcar os shorts. Eu decido — o critério "isso se sustenta sozinho?" é meu.

Nada disso é obrigatório pro pipeline funcionar. É `studio sugerir-cenas 01` imprimindo um
diff que eu aplico ou não.

**Adiado.** Como eu marquei o vídeo 01 à mão, o comando perdeu a urgência. Ele volta quando
existir vídeo 02 — aí o custo de marcar aparece de novo e com dois roteiros marcados eu tenho
exemplo pra dar de referência ao modelo.

## Em paralelo: o spike de Manim

Fora da ordem, começar **uma** cena Manim (`parity`). Não deu tempo aqui; passa pro sprint 2,
que tem espera embutida enquanto eu gravo. Não é pra
entregar nada — é pra medir quanto uma cena custa. Ver [sprint 6](sprint-06-manim.md) e a
justificativa no [índice](README.md).

## Fora de escopo

Tempo. Nada neste sprint sabe que segundos existem — só posição de palavra.
