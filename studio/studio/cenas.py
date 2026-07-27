"""Tipos de cena e seus parâmetros. O sprint 4 lê esta mesma tabela."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TipoCena:
    nome: str
    descricao: str
    obrigatorios: tuple[str, ...] = ()
    opcionais: tuple[str, ...] = ()
    fontes: tuple[str, ...] = ()
    adiados: tuple[str, ...] = ()
    manual: bool = False
    base: str = "video"

    @property
    def parametros(self) -> tuple[str, ...]:
        return self.obrigatorios + self.opcionais


TIPOS: dict[str, TipoCena] = {
    t.nome: t
    for t in (
        TipoCena(
            "terminal",
            "gravação de terminal a partir de um .tape (VHS)",
            obrigatorios=("fonte",),
            adiados=("fonte",),
        ),
        TipoCena(
            "codigo",
            "trecho de código renderizado",
            obrigatorios=("arquivo",),
            opcionais=("linhas", "destaque"),
            fontes=("arquivo",),
            base="repo",
        ),
        TipoCena(
            "manim",
            "animação de algoritmo",
            obrigatorios=("classe",),
            opcionais=("dados", "turnos"),
            adiados=("dados",),
        ),
        TipoCena(
            "replay",
            "replay de partida a partir de snapshot do Go",
            obrigatorios=("dados",),
            opcionais=("estrategia",),
            adiados=("dados",),
        ),
        TipoCena(
            "card",
            "cartela de texto",
            obrigatorios=("titulo",),
            opcionais=("subtitulo", "template"),
        ),
        TipoCena(
            "diagrama",
            "diagrama Mermaid",
            obrigatorios=("fonte",),
            adiados=("fonte",),
        ),
        TipoCena(
            "tela",
            "gravação minha de tela — vira placeholder até eu gravar",
            opcionais=("nota",),
            manual=True,
        ),
    )
}

CAMPOS_COMUNS = ("id",)


def existe(nome: str) -> bool:
    return nome in TIPOS


def nomes() -> list[str]:
    return list(TIPOS)
