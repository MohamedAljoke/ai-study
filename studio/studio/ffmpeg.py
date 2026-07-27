"""Falar com o ffmpeg. É o único arquivo do projeto que monta linha de comando dele.

Convenções §9: dependência pesada atrás de interface pequena. Quem renderiza descreve o
que quer — o dialeto do ffmpeg (escape do drawtext, `tpad`, concat demuxer) mora aqui, e
trocar de ferramenta de render um dia é mexer neste arquivo.

O que **não** entra: decidir o que renderizar. Cor de marca é `marca.py`, duração de cena
é `montagem.py`.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from studio import processos
from studio.projeto import ErroDeUso

INSTALAR = "sudo apt install ffmpeg   (ou brew install ffmpeg)"

FONTES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
)


@dataclass(frozen=True)
class Perfil:
    """Como o vídeo sai. O rascunho existe pra eu assistir em ciclo curto."""

    nome: str = "final"
    largura: int = 1920
    altura: int = 1080
    fps: int = 30
    crf: int = 20
    preset: str = "medium"

    @property
    def tamanho(self) -> str:
        return f"{self.largura}x{self.altura}"


FINAL = Perfil()
RASCUNHO = Perfil(nome="rascunho", largura=960, altura=540, crf=30, preset="ultrafast")


def exigir(binario: str = "ffmpeg") -> str:
    if caminho := shutil.which(binario):
        return caminho
    raise ErroDeUso(f"{binario} não encontrado — instale com:  {INSTALAR}")


def fonte() -> str:
    for caminho in FONTES:
        if Path(caminho).is_file():
            return caminho
    raise ErroDeUso(
        "nenhuma fonte TrueType pro texto do placeholder — "
        "instale com:  sudo apt install fonts-dejavu-core"
    )


def executar(comando: list[str], oque: str) -> subprocess.CompletedProcess:
    """Roda um binário do ffmpeg. Falha vira ErroDeUso dizendo o que estava fazendo."""
    return processos.executar(comando, oque, INSTALAR)


def rodar(argumentos: list[str], oque: str) -> str:
    """ffmpeg silencioso e sem perguntar antes de sobrescrever. Devolve o stderr."""
    comando = [exigir(), "-hide_banner", "-loglevel", "error", "-y", *argumentos]
    return executar(comando, oque).stderr


def escapar(conteudo: str) -> str:
    """Escape do `drawtext`, que é lido duas vezes: uma como filtro, outra como texto."""
    for de, para in (("\\", r"\\"), (":", r"\:"), ("'", r"\'"), ("%", r"\%")):
        conteudo = conteudo.replace(de, para)
    return conteudo


def texto(conteudo: str, y: str, tamanho: int, cor: str) -> str:
    """Um `drawtext` centrado na horizontal. Devolve o fragmento, não roda nada."""
    return (
        f"drawtext=fontfile={fonte()}:text='{escapar(conteudo)}':fontcolor={cor}"
        f":fontsize={tamanho}:x=(w-text_w)/2:y={y}"
    )


def quadro(fundo: str, filtros: list[str], saida: Path, perfil: Perfil, oque: str) -> None:
    """Um PNG desenhado do zero, sem arquivo de entrada."""
    saida.parent.mkdir(parents=True, exist_ok=True)
    rodar(
        [
            "-f", "lavfi", "-i", f"color=c={fundo}:s={perfil.tamanho}",
            "-vf", ",".join(filtros), "-frames:v", "1", str(saida),
        ],  # fmt: skip
        oque,
    )


def ultimo_quadro(entrada: Path, saida: Path) -> None:
    """O último frame de um vídeo, como PNG — é ele que congela no lugar do que falta.

    `-sseof -1` posiciona no último segundo e `-update 1` deixa cada frame sobrescrever
    a saída, então o que resta no arquivo é o frame final. Só serve pra vídeo: imagem
    parada não tem "último quadro" e nem precisa passar por aqui.
    """
    saida.parent.mkdir(parents=True, exist_ok=True)
    rodar(
        [
            "-sseof", "-1", "-i", str(entrada),
            "-update", "1", "-frames:v", "1", str(saida),
        ],  # fmt: skip
        f"congelar o último quadro de {entrada.name}",
    )


def _enquadrar(perfil: Perfil, fundo: str) -> str:
    """Cabe na tela inteira sem distorcer, com o resto preenchido pela cor de fundo."""
    return (
        f"scale={perfil.largura}:{perfil.altura}:force_original_aspect_ratio=decrease,"
        f"pad={perfil.largura}:{perfil.altura}:(ow-iw)/2:(oh-ih)/2:color={fundo},"
        f"setsar=1,fps={perfil.fps}"
    )


def segmento(
    entrada: Path,
    saida: Path,
    duracao: float,
    parado: bool,
    perfil: Perfil,
    fundo: str,
) -> None:
    """Uma cena normalizada: tamanho, fps e a duração exata que a timeline pediu.

    Imagem vira vídeo pelo `-loop`. Vídeo curto demais segura o último frame (`tpad`);
    longo demais é cortado pelo `-t`. Nos dois casos a saída dura o que foi pedido —
    é isso que faz o `concat` no fim bater com o áudio.
    """
    saida.parent.mkdir(parents=True, exist_ok=True)
    filtros = _enquadrar(perfil, fundo)
    if parado:
        origem = ["-loop", "1", "-t", f"{duracao:.3f}", "-i", str(entrada)]
    else:
        origem = ["-i", str(entrada)]
        filtros += f",tpad=stop_mode=clone:stop_duration={duracao:.3f}"

    rodar(
        [
            *origem, "-vf", filtros, "-t", f"{duracao:.3f}", "-an",
            "-c:v", "libx264", "-preset", perfil.preset, "-crf", str(perfil.crf),
            "-pix_fmt", "yuv420p", "-r", str(perfil.fps), str(saida),
        ],  # fmt: skip
        f"renderizar {saida.name}",
    )


def lista_concat(segmentos: list[Path]) -> str:
    """O formato do concat demuxer. Aspas simples escapadas, um arquivo por linha."""
    return "".join(f"file '{str(s.resolve())}'\n" for s in segmentos)


def juntar(lista: Path, audio: Path, saida: Path, oque: str) -> None:
    """Emenda os segmentos e põe a narração inteira por cima, sem recodificar vídeo."""
    saida.parent.mkdir(parents=True, exist_ok=True)
    rodar(
        [
            "-f", "concat", "-safe", "0", "-i", str(lista), "-i", str(audio),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-shortest", str(saida),
        ],  # fmt: skip
        oque,
    )
