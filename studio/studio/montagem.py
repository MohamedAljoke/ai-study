"""Pedidos + tempo → o plano de render. Função pura, não roda ffmpeg nem imprime.

O trabalho de verdade aqui é um só e é chato: **converter segundo em frame sem acumular
erro.** Cada segmento é codificado com uma duração inteira de frames; se cada um for
arredondado por conta própria, o erro soma cena a cena e a última entra meio segundo
adiantada em cima de um áudio que não se moveu. Por isso a conta é feita na borda
acumulada (`frame do fim`), não na duração de cada cena.

Quem decide **o que** cada cena mostra é `pedidos.py`; aqui só se decide por quanto
tempo. Reproduzível no REPL com uma lista na mão, sem pasta de vídeo nenhuma (§12).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from studio.ffmpeg import Perfil
from studio.pedidos import PRONTO, Pedido

PARADAS = (".png", ".jpg", ".jpeg", ".webp")
"""Extensões que são imagem: viram vídeo pelo `-loop`, não têm frame pra segurar."""


@dataclass(frozen=True)
class Segmento:
    """Uma cena virando um pedaço de vídeo com duração exata."""

    id: str
    entrada: Path
    duracao: float
    parado: bool
    origem: str = PRONTO
    congela: str = ""

    @property
    def falta(self) -> bool:
        """A cena não tem asset meu: o que está na tela é substituto."""
        return self.origem != PRONTO


@dataclass(frozen=True)
class Plano:
    segmentos: list[Segmento]
    audio: Path
    perfil: Perfil

    @property
    def duracao(self) -> float:
        return sum(s.duracao for s in self.segmentos)

    @property
    def faltando(self) -> list[Segmento]:
        return [s for s in self.segmentos if s.falta]


def _quadros(segundos: float, fps: int) -> int:
    return round(segundos * fps)


def planejar(
    pedidos: list[Pedido],
    substitutos: dict[str, Path],
    audio: Path,
    perfil: Perfil,
) -> Plano:
    """Um pedido vira um segmento, na ordem, sem buraco e sem sobreposição.

    `substitutos` é o quadro parado que entra no lugar de cada cena que falta — quadro
    congelado da anterior ou cartela. Quem os desenha é o comando; aqui eles são só um
    caminho, e é isso que mantém esta função testável sem ffmpeg.
    """
    segmentos = []
    borda = 0

    for pedido in pedidos:
        entrada = pedido.fonte if pedido.origem == PRONTO else substitutos.get(pedido.id)
        if entrada is None:
            raise KeyError(f"sem substituto pra cena '{pedido.id}'")

        # nunca zero frames: cena de duração nula quebraria o ffmpeg, e a conferência
        # já avisou que o roteiro tem dois marcadores na mesma palavra
        fim = max(_quadros(pedido.fim, perfil.fps), borda + 1)
        segmentos.append(
            Segmento(
                id=pedido.id,
                entrada=entrada,
                duracao=(fim - borda) / perfil.fps,
                parado=entrada.suffix.lower() in PARADAS,
                origem=pedido.origem,
                congela=pedido.congela,
            )
        )
        borda = fim

    return Plano(segmentos=segmentos, audio=audio, perfil=perfil)
