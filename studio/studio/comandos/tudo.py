"""studio tudo NN — encadeia o pipeline inteiro até o video.mp4.

Não tem lógica própria: chama os mesmos comandos que eu chamaria na mão, na ordem, e para
no primeiro que reclamar. Cada etapa já é cacheada (§2), então rodar isto de novo depois
de mexer só no `script.md` refaz só o que depende dele.

O `ErroDeUso` de cada etapa já vem com a instrução de conserto junto; aqui só se diz em
qual passo o pipeline parou.
"""

from __future__ import annotations

from collections.abc import Callable

from studio.comandos.alinhar import alinhar
from studio.comandos.montar import montar
from studio.comandos.narracao import narracao
from studio.comandos.pedidos import pedidos_cmd
from studio.comandos.timeline import timeline_cmd
from studio.projeto import ErroDeUso, resolver

PASSOS: list[tuple[str, Callable[..., int]]] = [
    ("narracao", narracao),
    ("alinhar", alinhar),
    ("timeline", timeline_cmd),
    ("pedidos", pedidos_cmd),
    ("montar", montar),
]


def tudo(numero: str, rascunho: bool = False) -> int:
    projeto = resolver(numero)
    n = projeto.numero

    for nome, executar in PASSOS:
        print(f"── studio {nome} {n}")
        extras = {"rascunho": rascunho} if nome == "montar" else {}
        try:
            codigo = executar(n, **extras)
        except ErroDeUso as erro:
            raise ErroDeUso(f"parou em  studio {nome} {n}\n  {erro}") from erro
        if codigo != 0:
            return codigo
        print()

    return 0
