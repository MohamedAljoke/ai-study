# Sprint 4 — A folha de pedidos

**Objetivo:** a timeline vira a lista do que eu tenho que produzir, com **duração exata** e o
**texto que eu falo** em cada cena.

É o sprint que substituiu o "assets determinísticos" original. A primeira versão gerava as
cenas sozinha — VHS pro terminal, freeze pro código, Chrome pras cartelas. Funcionava, e o
vídeo ficou com cara de gerado. A conclusão está no [README](README.md#o-studio-é-orquestrador-não-gerador):
o studio não produz mídia; ele encomenda e junta.

## O que o comando faz

```
studio pedidos 01
```

1. lê `build/timeline.json` (cena, tipo, params, tempo, intervalo de palavras);
2. procura o arquivo de cada cena em `assets/<id>.<ext>` — **por id, extensão livre**;
3. recorta o trecho da narração que se fala durante a cena;
4. escreve `build/pedidos.md` e imprime o resumo.

Sem cache: é varredura de diretório, custa milissegundos. Roda quantas vezes eu quiser
enquanto produzo.

## O formato

Uma seção por cena, na ordem do vídeo:

```markdown
## `parity-prova` — manim · 04:00.8 → 04:27.7 · **26.8s**

falta — largue em `assets/parity-prova.<ext>`
por enquanto o vídeo congela o último quadro de `replay-random`

`classe=ShipOverlay`

> …e é aqui que a paridade aparece: um navio de duas casas, deslize ele pra onde quiser,
> sempre cobre uma casa preta.
```

As duas informações que fazem a folha valer alguma coisa andam **juntas**: duração sem a fala
faz eu animar no escuro; fala sem duração faz eu animar 30s pra um buraco de 12.

Cena pronta aparece como `✓ pronto` com o arquivo achado. A folha é a checklist inteira, não
só o que falta — é assim que ela serve de painel de progresso.

## Onde os assets moram

`videos/NN-slug/assets/<id>.<ext>`, **fora do `build/`** (§4): é material meu, que nenhum
comando sabe refazer, e vai pro git junto com o `script.md`.

A extensão é escolha minha e a busca é por glob no id — Manim cospe mp4, um diagrama sai png,
uma captura pode ser mov, e o pipeline não tem por que ter opinião. Dois arquivos com o mesmo
id é `ErroDeUso` citando os dois: escolher por sorteio seria pior.

## Tipo de cena virou rótulo

`cenas.py` continua existindo, mas o tipo não escolhe mais ferramenta nem extensão. Ele
valida o marcador no `script.md` e me diz, na folha, que espécie de trabalho aquela cena é.
Tipo novo é uma linha na tabela e mais nada.

`nota=` vale pra qualquer tipo: é recado meu pra mim mesma, e sai na folha.

## Critério de pronto

`studio pedidos 01` lista as 18 cenas do vídeo 01 com duração e fala, e o `montar` monta o
vídeo inteiro a partir do que já existe em `assets/`. ✅

## O que ficou fora

- **Estimar esforço por cena.** A folha diz quanto tempo de vídeo falta, não quantas horas de
  trabalho. Chutar horas seria inventar número.
- **Abrir o Manim pra mim.** A folha é a encomenda; produzir é fora.
