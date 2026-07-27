"""Resolução de vídeo e caminhos. Ninguém monta caminho com string solta."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


class ErroDeUso(Exception):
    """Erro previsto, com mensagem pra pessoa. A CLI imprime e sai com código 1."""


def raiz_studio() -> Path:
    if env := os.environ.get("STUDIO_HOME"):
        return Path(env).expanduser().resolve()

    candidatos = [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent.parent]
    for dir in candidatos:
        if (dir / "pyproject.toml").is_file() and (dir / "studio").is_dir():
            return dir

    raise ErroDeUso(
        "não achei a raiz do studio — rode de dentro de studio/ ou defina STUDIO_HOME"
    )


def normalizar_numero(numero: str) -> str:
    numero = numero.strip()
    if not numero.isdigit():
        raise ErroDeUso(f"número de vídeo inválido: {numero!r} (esperado algo como 01)")
    return numero.zfill(2)


def validar_nome(nome: str) -> tuple[str, str]:
    if not (m := re.fullmatch(r"(\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)", nome)):
        raise ErroDeUso(
            f"nome inválido: {nome!r} — use NN-slug-em-kebab-case, ex: 01-batalha-naval"
        )
    return m.group(1), m.group(2)


@dataclass(frozen=True)
class Projeto:
    raiz: Path

    @property
    def nome(self) -> str:
        return self.raiz.name

    @property
    def numero(self) -> str:
        return self.nome.split("-", 1)[0]

    @property
    def slug(self) -> str:
        return self.nome.split("-", 1)[1]

    # versionado
    @property
    def script(self) -> Path:
        return self.raiz / "script.md"

    @property
    def wav(self) -> Path:
        return self.raiz / "narration.wav"

    @property
    def tapes(self) -> Path:
        return self.raiz / "tapes"

    @property
    def thumb_vars(self) -> Path:
        return self.raiz / "thumb.vars.json"

    # descartável
    @property
    def build(self) -> Path:
        return self.raiz / "build"

    @property
    def narracao_txt(self) -> Path:
        return self.build / "narration.txt"

    @property
    def leitura(self) -> Path:
        return self.build / "narration.md"

    @property
    def marcadores(self) -> Path:
        return self.build / "marcadores.json"

    @property
    def duble(self) -> Path:
        return self.build / "narration.duble.wav"

    @property
    def palavras(self) -> Path:
        return self.build / "words.json"

    @property
    def narracao_srt(self) -> Path:
        return self.build / "narration.srt"

    @property
    def narracao_vtt(self) -> Path:
        return self.build / "narration.vtt"

    @property
    def timeline(self) -> Path:
        return self.build / "timeline.json"

    @property
    def shorts_json(self) -> Path:
        return self.build / "shorts.json"

    @property
    def assets(self) -> Path:
        return self.build / "assets"

    def asset(self, id: str, extensao: str) -> Path:
        return self.assets / f"{id}.{extensao.lstrip('.')}"

    @property
    def video(self) -> Path:
        return self.build / "video.mp4"

    @property
    def legenda(self) -> Path:
        return self.build / "video.srt"

    @property
    def shorts(self) -> Path:
        return self.build / "shorts"

    @property
    def thumb(self) -> Path:
        return self.build / "thumb.png"

    @property
    def meta(self) -> Path:
        return self.build / "meta.md"

    def garantir_build(self) -> Path:
        self.build.mkdir(parents=True, exist_ok=True)
        return self.build

    def audio(self) -> tuple[Path, bool]:
        """O áudio a usar e se ele é dublê. Minha voz sempre ganha da sintética.

        Do sprint 2 em diante ninguém lê .wav direto: quem chamar isso não tem
        como montar um vídeo com voz de robô sem saber.
        """
        if self.wav.is_file():
            return self.wav, False
        return self.duble, True


def pasta_videos() -> Path:
    return raiz_studio() / "videos"


def pasta_templates() -> Path:
    return raiz_studio() / "templates"


def listar() -> list[Projeto]:
    videos = pasta_videos()
    if not videos.is_dir():
        return []
    return [Projeto(d) for d in sorted(videos.iterdir()) if d.is_dir()]


def resolver(numero: str) -> Projeto:
    numero = normalizar_numero(numero)
    achados = [p for p in listar() if p.numero == numero]

    if not achados:
        existentes = ", ".join(p.nome for p in listar()) or "nenhum"
        raise ErroDeUso(f"vídeo {numero} não existe (tem: {existentes})")
    if len(achados) > 1:
        colisao = ", ".join(p.nome for p in achados)
        raise ErroDeUso(f"mais de um vídeo com o número {numero}: {colisao}")

    return achados[0]
