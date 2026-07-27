"""As checagens do roteiro: parâmetro de cena, intervalo de linhas, aviso de leitura.

Separado da leitura de propósito. Quando o `studio narracao` reclamar de um marcador,
o erro nasce aqui — e dá pra mexer nas regras sem abrir o parser.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from studio import cenas as registro
from studio import texto as t
from studio.projeto import ErroDeUso
from studio.roteiro import Aviso, Cena, Roteiro

RE_INTERVALO = re.compile(r"^(\d+)-(\d+)$")
RE_DIGITO = re.compile(r"\d")

# quem recebe (linha, mensagem) e devolve o erro já com arquivo:linha na frente
Erro = Callable[[int, str], ErroDeUso]


def validar_cena(roteiro: Roteiro, cena: Cena, erro: Erro, base_repo: Path | None) -> None:
    """Marcador bem formado. O **asset** não é conferido aqui: ele nasce depois.

    Antes existia aviso de "fonte que ainda não existe", porque o studio ia gerar a cena
    a partir dela. Agora quem responde o que falta é a folha de pedidos, com duração
    junto — avisar aqui seria dizer a mesma coisa duas vezes e pior.
    """
    tipo = registro.TIPOS[cena.tipo]

    if faltando := [p for p in tipo.obrigatorios if p not in cena.params]:
        raise erro(cena.linha, f"cena {cena.tipo} '{cena.id}' sem {'=, '.join(faltando)}=")
    if sobrando := [p for p in cena.params if p not in tipo.parametros]:
        raise erro(
            cena.linha,
            f"parâmetro desconhecido em {cena.tipo}: {', '.join(sobrando)} "
            f"(aceita: {', '.join(tipo.parametros)})",
        )

    # `arquivo=` aponta pro código de verdade do repositório (§Nomes), e é a única coisa
    # que dá pra conferir agora: se o trecho não existe, o roteiro está falando de nada
    if base_repo is None or "arquivo" not in cena.params:
        return
    caminho = base_repo / cena.params["arquivo"]
    if not caminho.is_file():
        raise erro(cena.linha, f"arquivo={cena.params['arquivo']} não existe ({caminho})")
    if "linhas" in cena.params:
        _validar_linhas(cena, caminho, erro)


def _validar_linhas(cena: Cena, caminho: Path, erro: Erro) -> None:
    intervalo = RE_INTERVALO.fullmatch(cena.params["linhas"])
    if not intervalo:
        raise erro(cena.linha, f"linhas={cena.params['linhas']} — esperado a-b, ex: 12-28")
    inicio, fim = int(intervalo.group(1)), int(intervalo.group(2))
    total = len(caminho.read_text(encoding="utf-8").splitlines())
    if not 1 <= inicio <= fim <= total:
        raise erro(
            cena.linha,
            f"linhas={cena.params['linhas']} fora de {caminho.name}, que tem {total} linhas",
        )


def avisar_da_fala(roteiro: Roteiro, numero: int, bruta: str, limpa: str) -> None:
    """Não é erro: é coisa que eu leio diferente do que está escrito."""
    for trecho in t.RE_CRASE.findall(bruta):
        if trecho.strip():
            roteiro.avisos.append(Aviso("codigo", numero, trecho.strip()))
    if RE_DIGITO.search(limpa):
        roteiro.avisos.append(Aviso("digito", numero, limpa))
