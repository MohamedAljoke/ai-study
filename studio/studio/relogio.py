"""Segundo → relógio pra ler na tela. Só isso.

`legendas.py` tem a formatação do SRT/VTT, que é outro formato e tem outras regras
(vírgula decimal, hora sempre presente). Não é a mesma coisa e não deve virar a mesma
função — ver a dívida anotada em docs/convencoes.md §10.
"""

from __future__ import annotations

HORA = 3600


def _partir(segundos: float, casas: int) -> tuple[int, int, int, int]:
    """Arredonda antes de dividir: 59.96s tem que virar 01:00, não 00:60."""
    escala = 10**casas
    total = max(0, round(segundos * escala))
    resto, fracao = divmod(total, escala)
    horas, resto = divmod(resto, HORA)
    minutos, segundos_inteiros = divmod(resto, 60)
    return horas, minutos, segundos_inteiros, fracao


def formatar(segundos: float) -> str:
    """`00:22.4` — a marca de uma cena na timeline, com décimo."""
    horas, minutos, inteiros, decimo = _partir(segundos, 1)
    relogio = f"{minutos:02d}:{inteiros:02d}.{decimo}"
    return f"{horas}:{relogio}" if horas else relogio


def formatar_curto(segundos: float) -> str:
    """`07:21` — duração total, onde décimo é ruído."""
    horas, minutos, inteiros, _ = _partir(segundos, 0)
    return f"{horas}:{minutos:02d}:{inteiros:02d}" if horas else f"{minutos:02d}:{inteiros:02d}"
