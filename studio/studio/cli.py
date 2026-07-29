"""Porta de entrada. A lista de comandos é o mapa do pipeline."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass

from studio import __version__
from studio.alinhador import IDIOMA
from studio.comandos.alinhar import alinhar
from studio.comandos.duble import duble
from studio.comandos.montar import montar
from studio.comandos.narracao import narracao
from studio.comandos.novo import novo
from studio.comandos.pedidos import pedidos_cmd
from studio.comandos.status import status
from studio.comandos.timeline import timeline_cmd
from studio.comandos.tudo import tudo
from studio.comandos.ui import PORTA, ui
from studio.projeto import ErroDeUso
from studio.texto import PALAVRAS_POR_MINUTO


@dataclass(frozen=True)
class Flag:
    nome: str
    tipo: type = str
    padrao: object = None
    ajuda: str = ""

    @property
    def destino(self) -> str:
        return self.nome.lstrip("-").replace("-", "_")


@dataclass
class Comando:
    nome: str
    ajuda: str
    sprint: int
    argumento: str = "numero"
    executar: Callable[..., int] | None = None
    opcional: bool = False
    flags: tuple[Flag, ...] = ()


PIPELINE: list[Comando] = [
    Comando("novo", "cria a pasta do vídeo a partir do template", 0, "nome", novo),
    Comando("status", "em que passo o vídeo está", 0, "numero", status, opcional=True),
    Comando(
        "narracao",
        "script.md → narration.txt, o texto que eu leio",
        1,
        "numero",
        narracao,
        flags=(
            Flag("--wpm", int, PALAVRAS_POR_MINUTO, "ritmo de leitura pra estimar duração"),
        ),
    ),
    Comando(
        "duble",
        "voz sintética temporária, pra testar o pipeline sem gravar",
        2,
        "numero",
        duble,
        flags=(Flag("--wpm", int, PALAVRAS_POR_MINUTO, "ritmo que a voz falsa imita"),),
    ),
    Comando(
        "alinhar",
        "áudio + narration.txt → words.json + legendas",
        2,
        "numero",
        alinhar,
        flags=(Flag("--idioma", str, IDIOMA, "idioma do modelo de alinhamento"),),
    ),
    Comando(
        "timeline",
        "marcadores + words.json → timeline.json",
        3,
        "numero",
        timeline_cmd,
        flags=(Flag("--forcar", bool, False, "sobrescreve mesmo se eu tiver editado à mão"),),
    ),
    Comando(
        "pedidos",
        "timeline → pedidos.md, o que eu tenho que produzir",
        4,
        "numero",
        pedidos_cmd,
    ),
    Comando(
        "montar",
        "timeline + assets/ → video.mp4",
        5,
        "numero",
        montar,
        flags=(Flag("--rascunho", bool, False, "720p e preset veloz, pra revisar rápido"),),
    ),
    Comando(
        "ui",
        "abre a interface local: roteiro, áudio e assets numa página só",
        6,
        "numero",
        ui,
        opcional=True,
        flags=(
            Flag("--porta", int, PORTA, "porta do servidor local"),
            Flag("--sem-navegador", bool, False, "não abre o navegador sozinho"),
        ),
    ),
    Comando("shorts", "os trechos marcados → verticais com legenda queimada", 7),
    Comando("thumb", "thumb.vars.json → thumb.png", 8),
    Comando("meta", "título, descrição, capítulos, tags", 8),
    Comando(
        "tudo",
        "encadeia narracao → montar",
        5,
        "numero",
        tudo,
        flags=(Flag("--rascunho", bool, False, "720p e preset veloz, pra revisar rápido"),),
    ),
]


def _stub(comando: Comando) -> int:
    print(
        f"studio {comando.nome}: não implementado — sprint {comando.sprint}\n"
        f"  plano em docs/sprint-{comando.sprint:02d}-*.md",
        file=sys.stderr,
    )
    return 2


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="studio",
        description="Pipeline de produção de vídeo do canal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="os comandos estão em ordem de pipeline; docs/README.md tem os sprints",
    )
    parser.add_argument("--version", action="version", version=f"studio {__version__}")
    subs = parser.add_subparsers(dest="comando", metavar="comando")

    for comando in PIPELINE:
        ajuda = comando.ajuda
        if comando.executar is None:
            ajuda += f"  [sprint {comando.sprint}]"
        sub = subs.add_parser(comando.nome, help=ajuda, description=ajuda)
        sub.add_argument(
            comando.argumento,
            nargs="?" if comando.opcional else None,
            help="NN-slug" if comando.argumento == "nome" else "número do vídeo, ex: 01",
        )
        for flag in comando.flags:
            if flag.tipo is bool:  # chave liga/desliga, não recebe valor
                sub.add_argument(flag.nome, action="store_true", help=flag.ajuda)
            else:
                sub.add_argument(
                    flag.nome, type=flag.tipo, default=flag.padrao, help=flag.ajuda
                )
        sub.set_defaults(_comando=comando)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)

    if not args.comando:
        parser.print_help()
        return 0

    comando: Comando = args._comando
    if comando.executar is None:
        return _stub(comando)

    extras = {flag.destino: getattr(args, flag.destino) for flag in comando.flags}
    try:
        return comando.executar(getattr(args, comando.argumento), **extras)
    except ErroDeUso as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
