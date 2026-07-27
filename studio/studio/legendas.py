"""Palavras com tempo → .srt e .vtt. Sai de graça do dado do alinhamento."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from studio.alinhador import Palavra

LARGURA = 42
DURACAO_MAXIMA = 6.0
FIM_DE_FRASE = ".!?…"


def _fecha_frase(palavra: str) -> bool:
    return palavra.rstrip('"\'’”)').endswith(tuple(FIM_DE_FRASE))


def agrupar(palavras: Sequence[Palavra]) -> list[list[Palavra]]:
    """Linhas de ~42 caracteres, quebrando na pontuação e nunca passando de 6s."""
    linhas: list[list[Palavra]] = []
    atual: list[Palavra] = []

    for palavra in palavras:
        largura = sum(len(p.palavra) + 1 for p in atual) + len(palavra.palavra)
        longa = atual and palavra.fim - atual[0].inicio > DURACAO_MAXIMA
        if atual and (largura > LARGURA or longa):
            linhas.append(atual)
            atual = []
        atual.append(palavra)
        if _fecha_frase(palavra.palavra):
            linhas.append(atual)
            atual = []

    if atual:
        linhas.append(atual)
    return linhas


def _relogio(segundos: float, separador: str) -> str:
    segundos = max(segundos, 0.0)
    horas, resto = divmod(segundos, 3600)
    minutos, resto = divmod(resto, 60)
    inteiros, milesimos = divmod(round(resto * 1000), 1000)
    return f"{int(horas):02d}:{int(minutos):02d}:{inteiros:02d}{separador}{milesimos:03d}"


def _blocos(palavras: Sequence[Palavra], separador: str) -> Iterable[tuple[int, str, str]]:
    for n, linha in enumerate(agrupar(palavras), start=1):
        abre = _relogio(linha[0].inicio, separador)
        fecha = _relogio(linha[-1].fim, separador)
        yield n, f"{abre} --> {fecha}", " ".join(p.palavra for p in linha)


def srt(palavras: Sequence[Palavra]) -> str:
    partes = [f"{n}\n{tempo}\n{texto}\n" for n, tempo, texto in _blocos(palavras, ",")]
    return "\n".join(partes)


def vtt(palavras: Sequence[Palavra]) -> str:
    partes = [f"{tempo}\n{texto}\n" for _, tempo, texto in _blocos(palavras, ".")]
    return "WEBVTT\n\n" + "\n".join(partes)
