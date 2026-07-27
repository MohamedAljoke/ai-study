"""O que o arquivo de som é, medido com ffmpeg. Nada aqui corrige nada."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from studio import texto as t
from studio.projeto import ErroDeUso

TAXA = 48000
CANAIS = 1
LUFS_ALVO = -16.0
LUFS_TOLERANCIA = 1.5
TOLERANCIA_DURACAO = 0.35

RE_LUFS = re.compile(r"^\s*I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", re.MULTILINE)


@dataclass(frozen=True)
class Audio:
    caminho: Path
    duracao: float
    canais: int
    taxa: int

    def __str__(self) -> str:
        canais = {1: "mono", 2: "estéreo"}.get(self.canais, f"{self.canais} canais")
        return (
            f"{t.formatar_duracao(self.duracao)} ({self.duracao:.1f}s), "
            f"{canais} {self.taxa // 1000}k"
        )


def _rodar(comando: list[str], oque: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(comando, capture_output=True, text=True, check=True)
    except FileNotFoundError as erro:
        raise ErroDeUso(f"{comando[0]} não encontrado — instale pra {oque}") from erro
    except subprocess.CalledProcessError as erro:
        raise ErroDeUso(f"{comando[0]} falhou ao {oque}: {erro.stderr.strip()}") from erro


def sondar(wav: Path) -> Audio:
    saida = _rodar(
        [
            "ffprobe", "-v", "error", "-of", "json",
            "-show_entries", "format=duration:stream=channels,sample_rate",
            str(wav),
        ],  # fmt: skip
        f"ler {wav.name}",
    ).stdout
    dados = json.loads(saida)
    fluxo = dados["streams"][0]
    return Audio(
        caminho=wav,
        duracao=float(dados["format"]["duration"]),
        canais=int(fluxo["channels"]),
        taxa=int(fluxo["sample_rate"]),
    )


def loudness(wav: Path) -> float | None:
    """LUFS integrado. None quando o ffmpeg não devolve o resumo — é aviso, não erro."""
    saida = _rodar(
        ["ffmpeg", "-nostats", "-i", str(wav), "-filter:a", "ebur128", "-f", "null", "-"],
        f"medir o volume de {wav.name}",
    ).stderr
    achados = RE_LUFS.findall(saida)
    return float(achados[-1]) if achados else None


def conferir(
    audio: Audio,
    lufs: float | None,
    palavras: int,
    wpm: int = t.PALAVRAS_POR_MINUTO,
) -> list[str]:
    """Avisos legíveis com o comando de correção junto. Quem corrige sou eu."""
    avisos = []

    if audio.canais != CANAIS:
        avisos.append(
            f"{audio.canais} canais, esperado mono — "
            f"ffmpeg -i {audio.caminho.name} -ac 1 -ar {TAXA} saida.wav"
        )
    if audio.taxa != TAXA:
        avisos.append(
            f"{audio.taxa} Hz, esperado {TAXA} — "
            f"ffmpeg -i {audio.caminho.name} -ac 1 -ar {TAXA} saida.wav"
        )

    esperada = t.estimar_duracao(palavras, wpm)
    if esperada and abs(audio.duracao - esperada) / esperada > TOLERANCIA_DURACAO:
        avisos.append(
            f"{t.formatar_duracao(audio.duracao)} pra {t.formatar_numero(palavras)} palavras, "
            f"esperado ~{t.formatar_duracao(esperada)} — texto e áudio podem ser de versões "
            f"diferentes"
        )

    if lufs is not None and abs(lufs - LUFS_ALVO) > LUFS_TOLERANCIA:
        avisos.append(
            f"{lufs:.1f} LUFS, alvo {LUFS_ALVO:.0f} — Auphonic, ou "
            f"ffmpeg -i {audio.caminho.name} -af loudnorm=I={LUFS_ALVO:.0f} saida.wav"
        )

    return avisos
