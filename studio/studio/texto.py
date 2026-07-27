"""Limpeza e contagem de palavra. A unidade que os sprints 2 e 3 compartilham."""

from __future__ import annotations

import re

PALAVRAS_POR_MINUTO = 150

RE_CITACAO = re.compile(r"^\s*>\s?")
RE_LISTA = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
RE_IMAGEM = re.compile(r"!\[[^\]]*\]\([^)]*\)")
RE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
RE_CRASE = re.compile(r"`+([^`]*)`+")
RE_FORTE = re.compile(r"(\*\*|__)(.+?)\1")
RE_ENFASE = re.compile(r"(?<!\w)([*_])(?!\s)(.+?)(?<!\s)\1(?!\w)")
RE_ESPACO = re.compile(r"\s+")


def sem_citacao(linha: str) -> str:
    return RE_LISTA.sub("", RE_CITACAO.sub("", linha)).strip()


def limpar_bloco(texto: str) -> str:
    """Roda no parágrafo inteiro: negrito e ênfase atravessam quebra de linha."""
    texto = RE_IMAGEM.sub("", texto)
    texto = RE_LINK.sub(r"\1", texto)
    texto = RE_CRASE.sub(r"\1", texto)
    texto = RE_FORTE.sub(r"\2", texto)
    texto = RE_ENFASE.sub(r"\2", texto)
    return RE_ESPACO.sub(" ", texto).strip()


def limpar(linha: str) -> str:
    return limpar_bloco(sem_citacao(linha))


def palavras(texto: str) -> list[str]:
    return texto.split()


def contar(texto: str) -> int:
    return len(palavras(texto))


def estimar_duracao(n_palavras: int, wpm: int = PALAVRAS_POR_MINUTO) -> float:
    return n_palavras / wpm * 60


def formatar_duracao(segundos: float) -> str:
    if segundos < 90:
        return f"{segundos:.0f}s"
    return f"{int(segundos) // 60}min{int(segundos) % 60:02d}"


def formatar_numero(n: int) -> str:
    return f"{n:_}".replace("_", ".")
