# Sprint 0 — Fundação

> **Feito.** `studio novo` e `studio status` funcionam; `projeto.py` é a autoridade de
> caminhos e `cache.py` a de idempotência. O `--help` lista o pipeline inteiro.

**Objetivo:** existir um comando `studio` que roda, e uma estrutura de vídeo que os próximos
sprints preenchem.

Sprint chato e curto. O valor dele é não ter que decidir estrutura de pasta no meio do sprint
3, quando eu estiver tentando fazer alinhamento funcionar.

## Entregável

```
$ studio novo 01-batalha-naval
criado videos/01-batalha-naval/
  script.md         (template)
  assets/
  thumb.vars.json   (template)
  build/            (gitignored)

$ studio status 01
vídeo:      01-batalha-naval
roteiro:    ok — 9 blocos, 0 marcadores de cena, 0 de short
narração:   faltando  (studio narracao 01)
áudio:      faltando  (gravar narration.wav)
timeline:   faltando
```

`studio status` é o comando que eu mais vou usar. Ele me diz **qual é o próximo passo** sem
eu ter que lembrar da ordem.

## Tarefas

1. **Projeto Python.** `pyproject.toml`, entry point `studio`, gerenciador de dependência
   escolhido (`uv` recomendado — rápido e resolve o inferno de venv do WhisperX/Manim).
2. **CLI com subcomandos.** Um comando por etapa, todos aceitando o número do vídeo. Só os
   stubs; cada sprint preenche o seu.
3. **Resolução de vídeo.** `01` → `videos/01-batalha-naval/`. Prefixo numérico basta, não
   precisa digitar o slug.
4. **Objeto de projeto.** Uma classe que sabe os caminhos (`script`, `narration_txt`,
   `wav`, `timeline`, `assets/<id>`). Todo sprint seguinte usa isso; ninguém monta
   caminho com string solta.
5. **`studio novo`** a partir de um template versionado.
6. **`studio status`** — inspeciona o que existe no disco e imprime o próximo passo.
7. **Cache utilitário.** Uma função `precisa_refazer(saida, entradas, params) -> bool` por
   hash. Escrita uma vez aqui, usada por todas as etapas caras. Ver
   [convenções §2](convencoes.md).
8. **`.gitignore`** de `build/`.

## Critério de pronto

- `studio novo 02-teste` cria a estrutura e `studio status 02` diz "roteiro: template não
  editado".
- `studio --help` lista todos os comandos do pipeline, mesmo os não implementados (que
  respondem "não implementado — sprint N").

Esse último ponto importa: o `--help` é o mapa do projeto e me lembra do plano sem eu abrir
os docs.

## Fora de escopo

Qualquer processamento de verdade. Nenhum comando além de `novo` e `status` faz algo neste
sprint.

## Decisão a tomar aqui

**Onde mora o `studio` no repositório.** Hoje o repo tem `battleships/` (Go) e `content/`
(markdown). O `studio` é Python e é ferramenta, não produto — mas ele vai consumir dados
exportados pelo Go (`density.json`, replays). Manter no mesmo repo enquanto for scripts;
separar só se virar produto (ver `pipeline-producao.md`: "só considerar isso um software
depois do vídeo 03").

Recomendação: **mesmo repo**, `studio/` na raiz, como está.
