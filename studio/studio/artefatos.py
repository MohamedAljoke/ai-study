"""Os JSON do `build/` de volta pra dataclass.

Cada etapa lê arquivo e escreve arquivo (convenções §5), então alguém tem que saber o
formato de cada um — e é aqui, num lugar só. Quem consome recebe objeto, não `dict`:
`cena["palavra_inicio"]` espalhado por três módulos é como um campo renomeado vira
`KeyError` no meio do pipeline.

Arquivo corrompido ou de outra versão vira `ErroDeUso` legível, nunca `KeyError` cru.
"""

from __future__ import annotations

import json
from dataclasses import MISSING, dataclass, field
from pathlib import Path
from typing import Any

from studio.alinhador import Palavra
from studio.projeto import ErroDeUso
from studio.timeline import CenaEmTempo, ShortEmTempo, Timeline


@dataclass(frozen=True)
class MarcadorCena:
    """Uma cena como o sprint 1 a deixou: posição no texto, ainda sem tempo."""

    id: str
    tipo: str
    linha: int
    palavra_inicio: int
    palavra_fim: int
    params: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MarcadorShort:
    id: str
    titulo: str
    linha: int
    palavra_inicio: int
    palavra_fim: int


@dataclass(frozen=True)
class Marcadores:
    video: str
    titulo: str
    palavras: int
    cenas: list[MarcadorCena] = field(default_factory=list)
    shorts: list[MarcadorShort] = field(default_factory=list)


def _carregar(caminho: Path) -> dict[str, Any]:
    if not caminho.is_file():
        raise ErroDeUso(f"{caminho} não existe")
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ErroDeUso(f"{caminho.name} não é JSON válido: {erro}") from erro
    if not isinstance(dados, dict):
        raise ErroDeUso(f"{caminho.name}: esperado um objeto JSON no topo")
    return dados


def _obrigatorios(tipo: type) -> list[str]:
    return [
        nome
        for nome, campo in tipo.__dataclass_fields__.items()
        if campo.default is MISSING and campo.default_factory is MISSING
    ]


def _montar(tipo: type, dados: dict[str, Any], caminho: Path, onde: str):
    """Constrói a dataclass dizendo qual campo faltou, em vez de estourar TypeError."""
    if faltando := [c for c in _obrigatorios(tipo) if c not in dados]:
        raise ErroDeUso(
            f"{caminho.name}: {onde} sem {', '.join(faltando)} — "
            f"arquivo de uma versão antiga, apague o build/ e refaça"
        )
    return tipo(**{c: dados[c] for c in tipo.__dataclass_fields__ if c in dados})


def ler_marcadores(caminho: Path) -> Marcadores:
    dados = _carregar(caminho)
    return Marcadores(
        video=dados.get("video", ""),
        titulo=dados.get("titulo", ""),
        palavras=_inteiro(dados, "palavras", caminho),
        cenas=[_montar(MarcadorCena, c, caminho, "cena") for c in dados.get("cenas", [])],
        shorts=[_montar(MarcadorShort, s, caminho, "short") for s in dados.get("shorts", [])],
    )


def ler_palavras(caminho: Path) -> list[Palavra]:
    dados = _carregar(caminho)
    return [_montar(Palavra, p, caminho, "palavra") for p in dados.get("lista", [])]


def ler_timeline(caminho: Path) -> Timeline:
    """O `timeline.json` de volta. Do sprint 4 em diante, é daqui que todo mundo parte."""
    dados = _carregar(caminho)
    return Timeline(
        video=dados.get("video", ""),
        audio=dados.get("audio", ""),
        duracao=_numero(dados, "duracao", caminho),
        cenas=[_montar(CenaEmTempo, c, caminho, "cena") for c in dados.get("cenas", [])],
        shorts=[_montar(ShortEmTempo, s, caminho, "short") for s in dados.get("shorts", [])],
    )


def duracao_do_audio(caminho: Path) -> float:
    """A duração medida no sprint 2. Ninguém precisa abrir o wav de novo pra saber."""
    dados = _carregar(caminho)
    valor = dados.get("duracao")
    if not isinstance(valor, int | float):
        raise ErroDeUso(f"{caminho.name} sem duracao — refaça com  studio alinhar")
    return float(valor)


def _inteiro(dados: dict[str, Any], chave: str, caminho: Path) -> int:
    valor = dados.get(chave)
    if not isinstance(valor, int):
        raise ErroDeUso(f"{caminho.name} sem {chave} — arquivo incompleto, refaça o build/")
    return valor


def _numero(dados: dict[str, Any], chave: str, caminho: Path) -> float:
    valor = dados.get(chave)
    if not isinstance(valor, int | float):
        raise ErroDeUso(f"{caminho.name} sem {chave} — arquivo incompleto, refaça o build/")
    return float(valor)
