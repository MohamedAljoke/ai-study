"""Pedidos → o texto do `pedidos.md`. A encomenda que eu levo pro Manim.

É o mesmo papel que o `legendas.py` tem no sprint 2: dado com tempo entra, formato de
saída sai. Não decide nada sobre asset (isso é `pedidos.py`) e não imprime (§8) —
devolve `str`.

O que a folha precisa responder sem eu abrir mais nada: **quanto tempo a cena dura** e
**o que eu falo enquanto ela está no ar**. Duração sem a fala faz eu animar no escuro;
fala sem duração faz eu animar 30s pra um buraco de 12.
"""

from __future__ import annotations

import textwrap

from studio import relogio
from studio.pedidos import CONGELADO, PRONTO, Pedido, faltando, segundos_faltando

COLUNA = 88
"""Onde a citação da fala quebra. É markdown pra eu ler, não pra máquina."""


def _titulo(pedido: Pedido) -> str:
    faixa = f"{relogio.formatar(pedido.inicio)} → {relogio.formatar(pedido.fim)}"
    return f"## `{pedido.id}` — {pedido.tipo} · {faixa} · **{pedido.duracao:.1f}s**"


def _entrega(pedido: Pedido) -> list[str]:
    """A linha que diz se a cena chegou, e o que o vídeo mostra enquanto não chega."""
    if pedido.origem == PRONTO and pedido.fonte is not None:
        return [f"✓ pronto — `assets/{pedido.fonte.name}`"]

    linhas = [f"falta — largue em `assets/{pedido.id}.<ext>`"]
    if pedido.origem == CONGELADO:
        linhas.append(f"por enquanto o vídeo congela o último quadro de `{pedido.congela}`")
    else:
        linhas.append("por enquanto o vídeo mostra uma cartela com o id")
    return linhas


def _params(pedido: Pedido) -> list[str]:
    if not pedido.params:
        return []
    return ["", " · ".join(f"`{chave}={valor}`" for chave, valor in pedido.params.items())]


def _fala(pedido: Pedido) -> list[str]:
    if not pedido.fala.strip():
        return []
    envolvido = textwrap.wrap(pedido.fala.strip(), width=COLUNA) or [""]
    return ["", *(f"> {linha}" for linha in envolvido)]


def _cabecalho(video: str, pedidos: list[Pedido]) -> list[str]:
    pendentes = faltando(pedidos)
    prontos = len(pedidos) - len(pendentes)
    resumo = (
        f"{len(pedidos)} cenas · {prontos} prontas · {len(pendentes)} faltando · "
        f"{relogio.formatar_curto(segundos_faltando(pedidos))} de vídeo a produzir"
    )
    return [
        f"# Pedidos — {video}",
        "",
        resumo,
        "",
        "Cada cena vira um arquivo em `assets/<id>.<extensão>` — mp4, png ou mov, tanto",
        "faz. A duração abaixo é a que a narração já fixou: o que sobrar é cortado e o",
        "que faltar segura o último quadro, então mirar nela é o que evita retrabalho.",
    ]


def escrever(video: str, pedidos: list[Pedido]) -> str:
    """A folha inteira — o que falta e o que já chegou, na ordem do vídeo."""
    linhas = _cabecalho(video, pedidos)
    for pedido in pedidos:
        linhas += ["", "", _titulo(pedido), "", *_entrega(pedido)]
        linhas += _params(pedido)
        linhas += _fala(pedido)
    return "\n".join(linhas).rstrip() + "\n"
