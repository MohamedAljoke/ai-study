# studio

Pipeline de produção de vídeo do canal. Plano em `docs/README.md`, dividido em sprints.

**O studio não gera mídia.** Ele converte posição no texto em tempo, escreve a folha de
pedidos (`build/pedidos.md`: id, duração, fala) e junta os assets que o dono produziu fora —
Manim, gravação, imagem — com a narração. Asset é `videos/NN-slug/assets/<id>.<ext>`, achado
pelo id.

**As regras do projeto estão em `docs/convencoes.md` — leia antes de escrever código.**
Se um sprint contradiz as convenções, o sprint está errado.

## Este projeto não tem revisão humana

O dono escreve o roteiro e grava a voz; o código ele não revisa linha a linha. Então
**separação, simplicidade e teste são a única rede de segurança que existe aqui**. Na dúvida
entre entregar rápido e entregar separado e testado, entrega separado e testado.

## O que não negociar

**Uma etapa do pipeline por módulo** (convenções §8). Geração de voz não mora junto com
geração de texto; medição de áudio não mora junto com alinhamento. Etapa nova é arquivo novo,
nunca um `if` a mais num arquivo existente.

**Módulo não imprime e não conhece comando.** `print` só em `comandos/`. A lógica tem que
rodar em teste sem disco e sem capturar stdout.

**Dependência pesada atrás de interface pequena** (§9), com import tardio dentro da função e
`ErroDeUso` com o comando de instalação quando faltar. `alinhador.py` é o modelo: é o único
arquivo que sabe que o WhisperX existe; `ffmpeg.py` é o único que monta linha de comando do
ffmpeg.

**Tamanho é sintoma** (§10): módulo > ~200 linhas ou função > ~30 é gatilho pra olhar, não
limite burocrático.

**Teste no mesmo commit** (§11). Bug vira teste que falha antes do conserto. Nome de teste
descreve comportamento em português.

**Cache por hash da entrada** (§2), com a versão da ferramenta vinda de `cache.versao_de`.
Servir o segmento velho depois de trocar um asset é o pior modo de falha do pipeline:
silencioso, e faz debugar a etapa errada.

**Falta de asset não quebra o render** (§3). A cena congela o último quadro da anterior (ou
cartela navy, se não houver nada antes) e o vídeo monta. Como o vídeo esconde o buraco, o
buraco tem que aparecer em `pedidos.md`, na saída do `montar` e no `status` — nunca só no
silêncio. Erro fatal só em roteiro inválido.

## Antes de fechar qualquer coisa

```
make test     # pytest
make check    # ruff
```

Os dois limpos, sempre.

## Idioma

Código, testes, docs e commits em português — nomes de função, mensagem de erro e nome de
teste inclusive. É ferramenta de um canal pt-BR.
