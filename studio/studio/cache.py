"""Cache por hash das entradas. Ver docs/convencoes.md §2."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

FORMATO = "1"


def _somar_arquivo(h: hashlib._Hash, arquivo: Path) -> None:
    with arquivo.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)


def assinatura(
    entradas: Iterable[Path],
    params: dict[str, Any] | None = None,
    ferramenta: str = "",
) -> str:
    h = hashlib.sha256()
    h.update(f"{FORMATO}\0{ferramenta}\0".encode())
    h.update(json.dumps(params or {}, sort_keys=True, ensure_ascii=False).encode())

    for entrada in entradas:
        entrada = Path(entrada)
        if entrada.is_dir():
            arquivos = sorted(p for p in entrada.rglob("*") if p.is_file())
        elif entrada.is_file():
            arquivos = [entrada]
        else:
            raise FileNotFoundError(f"entrada não existe: {entrada}")

        for arquivo in arquivos:
            h.update(b"\0" + str(arquivo.relative_to(entrada.parent)).encode() + b"\0")
            _somar_arquivo(h, arquivo)

    return h.hexdigest()


def versao_de(*modulos) -> str:
    """Versão da ferramenta a partir do código que a implementa.

    Sem isso, mudar o gerador não invalida nada e o cache serve arquivo velho.
    """
    h = hashlib.sha256()
    for modulo in modulos:
        _somar_arquivo(h, Path(modulo.__file__))
    return h.hexdigest()[:12]


def versao_do_comando(nome: str, *modulos) -> str:
    """`versao_de` incluindo o próprio comando. Use `__name__` no primeiro argumento.

    O comando não é só orquestração: é nele que mora a serialização do JSON de saída.
    Mudar o formato do `words.json` sem invalidar o cache devolveria o arquivo no
    formato velho, em silêncio — o modo de falha que a §2 existe pra impedir.
    """
    return versao_de(sys.modules[nome], *modulos)


def _marca(saida: Path) -> Path:
    return saida.parent / f"{saida.name}.hash"


def _do_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    _somar_arquivo(h, caminho)
    return h.hexdigest()


def _linhas_da_marca(saida: Path) -> list[str]:
    """Linha 1: assinatura das entradas. Linha 2 (opcional): hash da saída gerada.

    Marca de uma versão antiga só tem a linha 1 — nesse caso não dá pra saber se o
    arquivo foi editado, e a resposta honesta é "não sei", que aqui vira "não foi".
    """
    marca = _marca(saida)
    if not marca.is_file():
        return []
    return marca.read_text().splitlines()


def precisa_refazer(
    saida: Path,
    entradas: Iterable[Path],
    params: dict[str, Any] | None = None,
    ferramenta: str = "",
) -> bool:
    saida = Path(saida)
    if not saida.exists():
        return True

    linhas = _linhas_da_marca(saida)
    if not linhas:
        return True

    return linhas[0].strip() != assinatura(entradas, params, ferramenta)


def foi_editado(saida: Path) -> bool:
    """O arquivo mudou depois de gerado — alguém (eu) mexeu nele à mão.

    O `timeline.json` é editável de propósito (convenções §5): é a válvula de escape
    pra quando o alinhador erra uma palavra técnica. Sobrescrever esse conserto em
    silêncio seria pior que não ter a válvula.
    """
    saida = Path(saida)
    linhas = _linhas_da_marca(saida)
    if len(linhas) < 2 or not saida.is_file():
        return False
    return linhas[1].strip() != _do_arquivo(saida)


def registrar(
    saida: Path,
    entradas: Iterable[Path],
    params: dict[str, Any] | None = None,
    ferramenta: str = "",
) -> None:
    saida = Path(saida)
    if not saida.exists():
        raise FileNotFoundError(f"nada gerado em {saida}, não dá pra registrar no cache")

    marca = _marca(saida)
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text(f"{assinatura(entradas, params, ferramenta)}\n{_do_arquivo(saida)}\n")
