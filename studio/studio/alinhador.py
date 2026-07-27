"""Texto conhecido + áudio → tempo de cada palavra.

A única parte do studio que sabe que o WhisperX existe. É a dependência mais pesada
do projeto e a mais provável de trocar (aeneas, stable-ts), então o resto do código
só enxerga `alinhar` e `Alinhada`.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from studio.projeto import ErroDeUso

IDIOMA = "pt"
DISPOSITIVO = "cpu"
INSTALAR = "uv sync --extra alinhamento"

RE_NAO_LETRA = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Alinhada:
    """Uma palavra como o alinhador a devolveu. Sem tempo quando ele não conseguiu."""

    palavra: str
    inicio: float | None
    fim: float | None
    score: float


@dataclass(frozen=True)
class Palavra:
    """Uma palavra do narration.txt, com índice canônico e tempo garantido."""

    indice: int
    palavra: str
    inicio: float
    fim: float
    score: float

    @property
    def estimada(self) -> bool:
        return self.score == 0.0


def chave(palavra: str) -> str:
    """Só letras minúsculas sem acento. É o que dá pra comparar entre os dois lados."""
    sem_acento = unicodedata.normalize("NFKD", palavra.lower())
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return RE_NAO_LETRA.sub("", sem_acento)


def _interpolar(inicio: float, fim: float, quantas: int) -> list[tuple[float, float]]:
    passo = (fim - inicio) / quantas if quantas else 0.0
    return [(inicio + passo * i, inicio + passo * (i + 1)) for i in range(quantas)]


def casar(nossas: list[str], alinhadas: list[Alinhada], duracao: float) -> list[Palavra]:
    """Uma saída por palavra do narration.txt. Nunca uma a mais, nunca uma a menos.

    O WhisperX normaliza o texto do jeito dele e pode devolver contagem diferente. Os
    marcadores do sprint 1 apontam pros índices de `texto.palavras`, então é essa lista
    que manda: o que ele engoliu vira tempo interpolado entre os vizinhos, marcado.
    """
    tempos: list[tuple[float, float, float] | None] = [None] * len(nossas)

    blocos = difflib.SequenceMatcher(
        None, [chave(p) for p in nossas], [chave(a.palavra) for a in alinhadas], autojunk=False
    ).get_matching_blocks()

    for bloco in blocos:
        for k in range(bloco.size):
            a = alinhadas[bloco.b + k]
            if a.inicio is not None and a.fim is not None:
                tempos[bloco.a + k] = (a.inicio, a.fim, a.score)

    ancoras = [i for i, tempo in enumerate(tempos) if tempo is not None]
    if not ancoras:
        vazio = _interpolar(0.0, duracao, len(nossas))
        return [
            Palavra(i, p, round(a, 3), round(b, 3), 0.0)
            for i, (p, (a, b)) in enumerate(zip(nossas, vazio, strict=True))
        ]

    # buracos entre âncoras, e as pontas
    inicio_buraco = 0
    for fim_buraco in [*ancoras, len(nossas)]:
        if fim_buraco > inicio_buraco:
            antes = tempos[inicio_buraco - 1][1] if inicio_buraco else 0.0
            depois = tempos[fim_buraco][0] if fim_buraco < len(nossas) else duracao
            faixa = _interpolar(antes, max(depois, antes), fim_buraco - inicio_buraco)
            for i, (a, b) in zip(range(inicio_buraco, fim_buraco), faixa, strict=True):
                tempos[i] = (a, b, 0.0)
        inicio_buraco = fim_buraco + 1

    return [
        Palavra(i, p, round(a, 3), round(b, 3), round(s, 3))
        for i, (p, (a, b, s)) in enumerate(zip(nossas, tempos, strict=True))
    ]


def _importar():
    try:
        import whisperx
    except ImportError as erro:
        raise ErroDeUso(f"whisperx não instalado — rode: {INSTALAR}") from erro
    return whisperx


def alinhar(
    wav: Path,
    texto: str,
    duracao: float,
    idioma: str = IDIOMA,
    dispositivo: str = DISPOSITIVO,
) -> list[Alinhada]:
    """Um segmento só, cobrindo o áudio inteiro.

    Forced alignment com um segmento é globalmente ótimo: um erro de leitura meu no
    minuto 3 se resolve ali mesmo. Cortar o áudio em pedaços por estimativa faria o
    contrário — cada borda errada viraria drift permanente daí pra frente.
    """
    whisperx = _importar()

    modelo, meta = whisperx.load_align_model(language_code=idioma, device=dispositivo)
    som = whisperx.load_audio(str(wav))
    segmento = {"text": " ".join(texto.split()), "start": 0.0, "end": duracao}

    resultado = whisperx.align(
        [segmento], modelo, meta, som, dispositivo, return_char_alignments=False
    )

    return [
        Alinhada(
            palavra=p.get("word", ""),
            inicio=p.get("start"),
            fim=p.get("end"),
            score=float(p.get("score") or 0.0),
        )
        for p in resultado["word_segments"]
    ]
