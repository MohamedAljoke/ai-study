"""Tipos de cena. Depois da simplificação, o tipo é **rótulo**, não motor.

Nenhum comando gera mídia (§3): todo asset é arquivo que eu produzo fora e largo em
`assets/<id>.<ext>`. Então o tipo não escolhe ferramenta nem extensão — ele existe pra
duas coisas: validar o marcador no `script.md` e me dizer, na folha de pedidos, que
espécie de trabalho aquela cena é.

Tipo novo é uma linha aqui. Sem código junto.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TipoCena:
    nome: str
    descricao: str
    obrigatorios: tuple[str, ...] = ()
    opcionais: tuple[str, ...] = ()

    @property
    def parametros(self) -> tuple[str, ...]:
        return self.obrigatorios + self.opcionais + COMUNS


COMUNS = ("nota",)
"""Parâmetro que todo tipo aceita: um recado meu, que sai na folha de pedidos."""


TIPOS: dict[str, TipoCena] = {
    t.nome: t
    for t in (
        TipoCena("manim", "animação de algoritmo", opcionais=("classe", "dados", "turnos")),
        TipoCena(
            "codigo",
            "trecho de código na tela",
            obrigatorios=("arquivo",),
            opcionais=("linhas", "destaque"),
        ),
        TipoCena("terminal", "gravação de terminal"),
        TipoCena("tela", "gravação de tela minha"),
        TipoCena(
            "card",
            "cartela de texto",
            obrigatorios=("titulo",),
            opcionais=("subtitulo",),
        ),
        TipoCena("diagrama", "diagrama"),
        TipoCena("replay", "replay de partida", opcionais=("dados", "estrategia")),
    )
}

CAMPOS_COMUNS = ("id",)


def existe(nome: str) -> bool:
    return nome in TIPOS


def nomes() -> list[str]:
    return list(TIPOS)
