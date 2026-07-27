"""As regras de sanidade da timeline. Nada aqui é fatal (convenções §3).

A distinção que importa: quase todo aviso daqui aponta pra um problema de **escrita do
roteiro**, não de software. Short de 12 segundos não é bug do alinhador — é um trecho
marcado curto demais, e quem conserta sou eu no `script.md`. A mensagem tem que dizer
isso, senão eu vou procurar defeito no lugar errado.
"""

from __future__ import annotations

from dataclasses import dataclass

from studio import relogio
from studio.timeline import Timeline

SHORT_MINIMO = 20.0
SHORT_MAXIMO = 60.0
CENA_RELAMPAGO = 3.0
ESTATICA_LONGA = 25.0
ESTATICAS = ("card", "diagrama")


@dataclass(frozen=True)
class Aviso:
    tipo: str
    alvo: str
    texto: str


def _shorts(timeline: Timeline) -> list[Aviso]:
    avisos = []
    for short in timeline.shorts:
        duracao = relogio.formatar_curto(short.duracao)
        if short.duracao < SHORT_MINIMO:
            avisos.append(
                Aviso(
                    "short-curto",
                    short.id,
                    f"short '{short.id}' dura {duracao} — menos de "
                    f"{SHORT_MINIMO:.0f}s não sustenta um vertical. "
                    f"mova o marcador de fim no script.md",
                )
            )
        elif short.duracao > SHORT_MAXIMO:
            avisos.append(
                Aviso(
                    "short-longo",
                    short.id,
                    f"short '{short.id}' dura {duracao} — passa de "
                    f"{SHORT_MAXIMO:.0f}s. corte o trecho no script.md",
                )
            )
    return avisos


def _cenas(timeline: Timeline) -> list[Aviso]:
    avisos = []
    for cena in timeline.cenas:
        if cena.duracao <= 0:
            avisos.append(
                Aviso(
                    "cena-invertida",
                    cena.id,
                    f"cena '{cena.id}' não dura nada — outro marcador começa no mesmo "
                    f"ponto do texto. separe os dois no script.md",
                )
            )
        elif cena.duracao < CENA_RELAMPAGO:
            avisos.append(
                Aviso(
                    "cena-relampago",
                    cena.id,
                    f"cena '{cena.id}' dura {cena.duracao:.1f}s — não dá tempo de ver",
                )
            )
        elif cena.tipo in ESTATICAS and cena.duracao > ESTATICA_LONGA:
            avisos.append(
                Aviso(
                    "estatica-longa",
                    cena.id,
                    f"cena '{cena.id}' é um {cena.tipo} parado por "
                    f"{relogio.formatar_curto(cena.duracao)} — imagem estática cansa",
                )
            )
    return avisos


def _cobertura(timeline: Timeline) -> list[Aviso]:
    if not timeline.cenas:
        texto = "nenhuma cena no roteiro — o vídeo seria só áudio"
        return [Aviso("sem-cena", timeline.video, texto)]
    if (primeira := timeline.cenas[0]).inicio > 0:
        return [
            Aviso(
                "abertura-vazia",
                primeira.id,
                f"os primeiros {relogio.formatar(primeira.inicio)} não têm cena — "
                f"ponha um marcador antes do primeiro parágrafo",
            )
        ]
    return []


def conferir(timeline: Timeline) -> list[Aviso]:
    return _cobertura(timeline) + _cenas(timeline) + _shorts(timeline)
