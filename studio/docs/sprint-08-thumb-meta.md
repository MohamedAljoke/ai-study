# Sprint 8 — Thumbnail e metadados

**Objetivo:** fechar o pacote de publicação — thumb, título, descrição, capítulos, tags.

Sprint mais barato de todos e **independente do caminho principal**: só depende do sprint 0.
Bom pra fazer numa folga, ou quando a montagem estiver travada em algum problema chato.

## Thumbnail

**Não usar geração de imagem por IA.** Thumb é 80% texto grande, e modelo de imagem escreve
texto mal. Template HTML + screenshot é determinístico, versionável e bate a marca sempre.

Stack: `thumb.html` com CSS e variáveis por vídeo → **Playwright** → PNG 1280x720.

### Cores

| Uso | Hex |
|---|---|
| Fundo / navy | `#122440` |
| Texto / logo | `#FFFFFF` |
| Fundo alternativo | `#1B3157` |
| **Acento** | `#FFB020` âmbar |

O banner do canal é navy + branco só. Elegante, mas **fraco em thumbnail** — falta ponto de
tensão. O âmbar entra **só no número ou palavra-chave** (`95 → 44`, `1 LINHA`) e **nunca em
mais de um elemento**. Mantém a identidade e dá o contraste que a miniatura precisa.

### Template

Logo (o triângulo de 3 círculos) num canto, faixa navy, título de 2–4 palavras em sans-serif
pesada (Inter / Archivo Black / Anton), opcionalmente um recorte da tela do código.

```json
{ "titulo": "95 → 44", "subtitulo": "o mesmo jogo, outro algoritmo",
  "destaque": "44", "recorte": "assets/parse-position.png" }
```

### Tarefas

1. `thumb.html` + CSS com as variáveis da marca.
2. Render via Playwright em 1280x720, com checagem de peso (< 2 MB, limite do YouTube).
3. **3 variantes de copy por vídeo**, geradas por LLM a partir do roteiro — "10 títulos de no
   máximo 4 palavras" é exatamente o tipo de coisa que a IA faz bem e eu faço devagar.
4. Contact sheet com as variantes lado a lado, pra eu escolher olhando.

## Metadados

```
$ studio meta 01
→ build/meta.md

título:     Eu ensinei um bot a jogar Batalha Naval — de 95 tiros para 44
descrição:  ...
capítulos:  00:00 O problema
            02:41 Um main.go burro
            06:10 O mapa de probabilidade
            ...
tags:       go, golang, algoritmos, batalha naval, ...
```

### Tarefas

1. **Capítulos direto da timeline** — os blocos do roteiro já são os capítulos, e os tempos já
   existem. Custo zero.
2. **Título, descrição e tags** via LLM a partir do roteiro.
3. Descrição com links fixos do canal (repositório, ferramentas) + o específico do vídeo.
4. Saída em um `meta.md` único que eu abro e copio e colo no YouTube.

## Critério de pronto

Publicar o vídeo 01 sem escrever nada na mão além de conferir e ajustar o que a IA sugeriu.

## Fora de escopo

Upload via API do YouTube. É fácil e vem depois — **o valor está antes dele**.
