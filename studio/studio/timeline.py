"""Índice de palavra → segundo. A junção das duas metades do pipeline.

O sprint 1 diz *onde no texto* cada cena começa; o sprint 2 diz *quando* cada palavra é
falada. Aqui isso vira tempo, e do sprint 4 em diante ninguém mais precisa do `script.md`
nem do `words.json` — só desta timeline.

Função pura: recebe dado, devolve dado. Dá pra reproduzir um erro de posicionamento no
REPL com duas listas na mão, sem pasta de vídeo nenhuma (convenções §12).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from studio import cenas as registro
from studio.alinhador import Palavra
from studio.projeto import ErroDeUso

if TYPE_CHECKING:  # só anotação: quem lê os JSON é o artefatos, e ele importa daqui
    from studio.artefatos import MarcadorCena, Marcadores, MarcadorShort

RESPIRO = 0.25
"""Sobra depois da última palavra de um short, pra não cortar a sílaba final."""


@dataclass(frozen=True)
class CenaEmTempo:
    """Uma cena já posicionada. `Cena` (roteiro.py) é a mesma coisa antes do tempo.

    Carrega o intervalo de palavras junto com o de tempo: é ele que deixa a folha de
    pedidos citar o que eu falo durante a cena sem reabrir o `marcadores.json`.
    """

    id: str
    tipo: str
    inicio: float
    fim: float
    palavra_inicio: int = 0
    palavra_fim: int = 0
    params: dict[str, str] = field(default_factory=dict)

    @property
    def duracao(self) -> float:
        return self.fim - self.inicio


@dataclass(frozen=True)
class ShortEmTempo:
    id: str
    titulo: str
    inicio: float
    fim: float

    @property
    def duracao(self) -> float:
        return self.fim - self.inicio


@dataclass(frozen=True)
class Timeline:
    video: str
    audio: str
    duracao: float
    cenas: list[CenaEmTempo] = field(default_factory=list)
    shorts: list[ShortEmTempo] = field(default_factory=list)

    def json(self) -> dict:
        return {
            "video": self.video,
            "audio": self.audio,
            "duracao": round(self.duracao, 3),
            "cenas": [
                {
                    "id": c.id,
                    "tipo": c.tipo,
                    "inicio": c.inicio,
                    "fim": c.fim,
                    "palavra_inicio": c.palavra_inicio,
                    "palavra_fim": c.palavra_fim,
                    "params": c.params,
                }
                for c in self.cenas
            ],
        }

    def json_shorts(self) -> dict:
        return {
            "video": self.video,
            "shorts": [
                {
                    "id": s.id,
                    "titulo": s.titulo,
                    "inicio": s.inicio,
                    "fim": s.fim,
                    "duracao": round(s.duracao, 3),
                    "origem": self.video,
                    "legenda": "queimada",
                }
                for s in self.shorts
            ],
        }


class Regua:
    """Converte índice de palavra em segundo. O resto do módulo só usa isto."""

    def __init__(self, palavras: list[Palavra], duracao: float):
        self.palavras = palavras
        self.duracao = duracao

    def _conferir(self, indice: int, quem: str) -> None:
        if not 0 <= indice <= len(self.palavras):
            raise ErroDeUso(
                f"{quem} aponta pra palavra {indice}, e a narração tem "
                f"{len(self.palavras)} — refaça o build/ com  studio narracao  "
                f"e  studio alinhar"
            )

    def comeco(self, indice: int, quem: str) -> float:
        """Onde a palavra começa a ser falada. A palavra 0 é o segundo zero do vídeo."""
        self._conferir(indice, quem)
        if indice == 0:
            return 0.0
        if indice == len(self.palavras):
            return self.duracao
        return self.palavras[indice].inicio

    def fim_falado(self, indice: int, quem: str) -> float:
        """Onde a palavra *anterior* a `indice` para de soar. É onde um short fecha."""
        self._conferir(indice, quem)
        if indice == 0:
            return 0.0
        return self.palavras[indice - 1].fim


def _conferir_tipo(cena: MarcadorCena) -> None:
    """O tipo é rótulo do que eu tenho que produzir, mas rótulo inventado é erro.

    O `marcadores.json` é editável à mão (§5), então a checagem não pode morar só no
    parser do markdown.
    """
    if not registro.existe(cena.tipo):
        raise ErroDeUso(
            f"cena '{cena.id}' é do tipo '{cena.tipo}', que não existe "
            f"(tem: {', '.join(registro.nomes())})"
        )


def _posicionar_cenas(cenas: list[MarcadorCena], regua: Regua) -> list[CenaEmTempo]:
    """Sem buraco: cada cena vai até onde a próxima começa, a última até o fim do áudio."""
    ordenadas = sorted(cenas, key=lambda c: c.palavra_inicio)
    if not ordenadas:
        return []
    inicios = [regua.comeco(c.palavra_inicio, f"cena '{c.id}'") for c in ordenadas]
    fins = [*inicios[1:], regua.duracao]

    posicionadas = []
    for cena, inicio, fim in zip(ordenadas, inicios, fins, strict=True):
        _conferir_tipo(cena)
        posicionadas.append(
            CenaEmTempo(
                id=cena.id,
                tipo=cena.tipo,
                inicio=round(inicio, 3),
                fim=round(fim, 3),
                palavra_inicio=cena.palavra_inicio,
                palavra_fim=cena.palavra_fim,
                params=cena.params,
            )
        )
    return posicionadas


def _posicionar_shorts(shorts: list[MarcadorShort], regua: Regua) -> list[ShortEmTempo]:
    """Short fecha na última palavra dele, não no começo da próxima: é corte, não cena."""
    posicionados = []
    for short in sorted(shorts, key=lambda s: s.palavra_inicio):
        quem = f"short '{short.id}'"
        inicio = regua.comeco(short.palavra_inicio, quem)
        fim = min(regua.fim_falado(short.palavra_fim, quem) + RESPIRO, regua.duracao)
        posicionados.append(
            ShortEmTempo(
                id=short.id,
                titulo=short.titulo,
                inicio=round(inicio, 3),
                fim=round(max(fim, inicio), 3),
            )
        )
    return posicionados


def montar(
    marcadores: Marcadores, palavras: list[Palavra], duracao: float, audio: str
) -> Timeline:
    if marcadores.palavras != len(palavras):
        raise ErroDeUso(
            f"marcadores.json tem {marcadores.palavras} palavras e words.json tem "
            f"{len(palavras)} — os índices não significam a mesma coisa.\n"
            f"  o script.md mudou depois do alinhamento. rode:  studio alinhar "
            f"{marcadores.video.split('-', 1)[0]}"
        )

    regua = Regua(palavras, duracao)
    return Timeline(
        video=marcadores.video,
        audio=audio,
        duracao=duracao,
        cenas=_posicionar_cenas(marcadores.cenas, regua),
        shorts=_posicionar_shorts(marcadores.shorts, regua),
    )
