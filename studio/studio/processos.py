"""Rodar binário externo e transformar falha em `ErroDeUso` legível.

Quase todo gerador chama uma ferramenta de linha de comando. O que não pode acontecer é
um traceback de `subprocess` na cara de quem só queria montar um vídeo — e quando o que
falta é a ferramenta, a mensagem vem com o comando de instalação junto (§9).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from studio.projeto import ErroDeUso


def executar(
    comando: list[str], oque: str, instalar: str = "", cwd: Path | None = None
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(comando, capture_output=True, text=True, check=True, cwd=cwd)
    except FileNotFoundError as erro:
        dica = f" — instale com:  {instalar}" if instalar else ""
        raise ErroDeUso(f"{comando[0]} não encontrado{dica}") from erro
    except subprocess.CalledProcessError as erro:
        detalhe = (erro.stderr or erro.stdout or "").strip()
        raise ErroDeUso(f"{comando[0]} falhou ao {oque}: {detalhe}") from erro
