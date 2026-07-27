"""script.md → `Roteiro`. Só sintaxe: quem valida marcador é `validacao.py`.

`interpretar` recebe uma **string**, não um projeto — dá pra reproduzir um bug no REPL
com o pedaço de markdown que quebrou, sem pasta de vídeo nenhuma (convenções §12).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from studio import cenas as registro
from studio import texto as t
from studio import validacao
from studio.projeto import ErroDeUso, Projeto, raiz_studio
from studio.roteiro import Bloco, Cena, Fala, Roteiro, Short

RE_MARCADOR = re.compile(r"^ {0,3}<!--\s*(cena|short)\s*:\s*(.*?)\s*-->\s*$")
RE_ATRIBUTO = re.compile(r"""([a-zA-Z_][\w-]*)=(?:"([^"]*)"|'([^']*)'|(\S+))""")
RE_TITULO = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
RE_CERCA = re.compile(r"^ {0,3}(```|~~~)")
RE_FALA = re.compile(r"^ {0,3}>")
RE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def atributos(conteudo: str) -> tuple[str, dict[str, str]]:
    """`terminal id=play-demo fonte=x.tape` → `("terminal", {"id": ..., "fonte": ...})`."""
    cabeca = conteudo.split(maxsplit=1)[0] if conteudo.split() else ""
    params = {
        m.group(1): next(g for g in m.groups()[1:] if g is not None)
        for m in RE_ATRIBUTO.finditer(conteudo)
    }
    return cabeca, params


@dataclass
class Leitor:
    """O estado que atravessa o arquivo, linha a linha.

    `tokens` é a contagem canônica de palavras — é o índice dela que o sprint 2 casa
    com o tempo. Marcador não tem posição própria: ele fica `pendente` até o próximo
    parágrafo de fala existir, e herda a primeira palavra dele.
    """

    roteiro: Roteiro
    base_repo: Path | None = None

    tokens: list[str] = field(default_factory=list)
    pendentes: list[Cena | Short] = field(default_factory=list)
    abertos: dict[str, Short] = field(default_factory=dict)
    ids: dict[str, int] = field(default_factory=dict)
    paragrafo: list[str] = field(default_factory=list)
    linha_paragrafo: int = 0
    dentro_de_cerca: bool = False

    def erro(self, linha: int, msg: str) -> ErroDeUso:
        return ErroDeUso(f"{self.roteiro.origem.name}:{linha}: {msg}")

    def fechar_paragrafo(self) -> None:
        if not self.paragrafo:
            return
        conteudo = t.limpar_bloco(" ".join(self.paragrafo))
        inicio = len(self.tokens)
        for pendente in self.pendentes:
            pendente.palavra_inicio = inicio
        self.pendentes.clear()
        self.tokens.extend(t.palavras(conteudo))
        fala = Fala(self.linha_paragrafo, conteudo, inicio, len(self.tokens))
        self.roteiro.falas.append(fala)
        self.roteiro.eventos.append(("fala", fala))
        self.paragrafo = []

    def registrar_id(self, id: str, linha: int) -> None:
        if not RE_ID.fullmatch(id):
            raise self.erro(linha, f"id '{id}' não é kebab-case (ex: mapa-de-calor)")
        if id in self.ids:
            raise self.erro(linha, f"id '{id}' já usado na linha {self.ids[id]}")
        self.ids[id] = linha

    # --- um método por espécie de marcador ---

    def cena(self, numero: int, cabeca: str, params: dict[str, str]) -> None:
        if not registro.existe(cabeca):
            raise self.erro(
                numero,
                f"tipo de cena desconhecido: '{cabeca}' (tem: {', '.join(registro.nomes())})",
            )
        if "id" not in params:
            raise self.erro(numero, f"cena {cabeca} sem id=")
        self.registrar_id(params["id"], numero)

        cena = Cena(id=params.pop("id"), tipo=cabeca, linha=numero, params=params)
        validacao.validar_cena(self.roteiro, cena, self.erro, self.base_repo)
        self.roteiro.cenas.append(cena)
        self.roteiro.eventos.append(("cena", cena))
        self.pendentes.append(cena)

    def short_inicio(self, numero: int, params: dict[str, str]) -> None:
        if "id" not in params:
            raise self.erro(numero, "short sem id=")
        if "titulo" not in params:
            raise self.erro(numero, f"short '{params['id']}' sem titulo=")
        self.registrar_id(params["id"], numero)

        short = Short(id=params["id"], titulo=params["titulo"], linha=numero)
        self.abertos[short.id] = short
        self.roteiro.shorts.append(short)
        self.roteiro.eventos.append(("short-inicio", short))
        self.pendentes.append(short)

    def short_fim(self, numero: int, params: dict[str, str]) -> None:
        id = params.get("id", "")
        if id not in self.abertos:
            raise self.erro(numero, f"short '{id}' fechado sem ter sido aberto")
        short = self.abertos.pop(id)
        short.linha_fim = numero
        short.palavra_fim = len(self.tokens)
        self.roteiro.eventos.append(("short-fim", short))

    def marcador(self, numero: int, especie: str, conteudo: str) -> None:
        self.fechar_paragrafo()
        cabeca, params = atributos(conteudo)

        if especie == "cena":
            self.cena(numero, cabeca, params)
        elif cabeca == "inicio":
            self.short_inicio(numero, params)
        elif cabeca == "fim":
            self.short_fim(numero, params)
        else:
            raise self.erro(numero, f"short espera 'inicio' ou 'fim', veio '{cabeca}'")

    # --- o resto do markdown ---

    def titulo(self, numero: int, nivel: int, nome: str) -> None:
        self.fechar_paragrafo()
        if nivel == 1:
            self.roteiro.titulo = nome
            return
        bloco = Bloco(nome, nivel, numero, len(self.tokens))
        self.roteiro.blocos.append(bloco)
        self.roteiro.eventos.append(("bloco", bloco))

    def fala(self, numero: int, bruta: str) -> None:
        crua = t.sem_citacao(bruta)
        if not crua:
            self.fechar_paragrafo()
            return
        if not self.paragrafo:
            self.linha_paragrafo = numero
        self.paragrafo.append(crua)
        validacao.avisar_da_fala(self.roteiro, numero, bruta, t.limpar(bruta))

    def linha(self, numero: int, bruta: str) -> None:
        """Uma linha do arquivo. A ordem dos testes aqui é a gramática do roteiro."""
        if RE_CERCA.match(bruta):
            self.fechar_paragrafo()
            self.dentro_de_cerca = not self.dentro_de_cerca
        elif self.dentro_de_cerca:
            return
        elif marcador := RE_MARCADOR.match(bruta):
            self.marcador(numero, marcador.group(1), marcador.group(2))
        elif titulo := RE_TITULO.match(bruta):
            self.titulo(numero, len(titulo.group(1)), titulo.group(2))
        elif RE_FALA.match(bruta):
            self.fala(numero, bruta)
        else:
            self.fechar_paragrafo()

    def fechar(self) -> Roteiro:
        self.fechar_paragrafo()

        if self.pendentes:
            pendente = self.pendentes[0]
            raise self.erro(
                pendente.linha, f"marcador '{pendente.id}' não tem narração depois dele"
            )
        if self.abertos:
            short = next(iter(self.abertos.values()))
            raise self.erro(short.linha, f"short '{short.id}' aberto e nunca fechado")

        self.roteiro.total_palavras = len(self.tokens)
        _fechar_intervalos(self.roteiro, len(self.tokens))
        return self.roteiro


def _fechar_intervalos(roteiro: Roteiro, total: int) -> None:
    """Cada cena e cada bloco vão até onde o próximo começa. O último vai até o fim."""
    for lista in (roteiro.cenas, roteiro.blocos):
        ordenada = sorted(lista, key=lambda x: x.palavra_inicio)
        for atual, proximo in zip(ordenada, ordenada[1:], strict=False):
            atual.palavra_fim = proximo.palavra_inicio
        if ordenada:
            ordenada[-1].palavra_fim = total


def interpretar(fonte: str, origem: Path, base_repo: Path | None = None) -> Roteiro:
    leitor = Leitor(
        roteiro=Roteiro(titulo=origem.parent.name, origem=origem),
        base_repo=base_repo,
    )
    for numero, bruta in enumerate(fonte.splitlines(), start=1):
        leitor.linha(numero, bruta)
    return leitor.fechar()


def ler(projeto: Projeto) -> Roteiro:
    if not projeto.script.is_file():
        raise ErroDeUso(f"{projeto.script} não existe")
    return interpretar(
        projeto.script.read_text(encoding="utf-8"),
        origem=projeto.script,
        base_repo=raiz_studio().parent,
    )
