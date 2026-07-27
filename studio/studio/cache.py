"""Cache por hash das entradas. Ver docs/convencoes.md §2."""

from __future__ import annotations

import hashlib
import json
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


def _marca(saida: Path) -> Path:
    return saida.parent / f"{saida.name}.hash"


def precisa_refazer(
    saida: Path,
    entradas: Iterable[Path],
    params: dict[str, Any] | None = None,
    ferramenta: str = "",
) -> bool:
    saida = Path(saida)
    if not saida.exists():
        return True

    marca = _marca(saida)
    if not marca.is_file():
        return True

    return marca.read_text().strip() != assinatura(entradas, params, ferramenta)


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
    marca.write_text(assinatura(entradas, params, ferramenta) + "\n")
