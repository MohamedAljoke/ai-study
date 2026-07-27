"""Parser do roteiro. Markdown legível de um lado, fonte de dados do outro."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from studio import cenas as registro
from studio import texto as t
from studio.projeto import ErroDeUso, Projeto, raiz_studio

RE_MARCADOR = re.compile(r"^ {0,3}<!--\s*(cena|short)\s*:\s*(.*?)\s*-->\s*$")
RE_ATRIBUTO = re.compile(r"""([a-zA-Z_][\w-]*)=(?:"([^"]*)"|'([^']*)'|(\S+))""")
RE_TITULO = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
RE_CERCA = re.compile(r"^ {0,3}(```|~~~)")
RE_FALA = re.compile(r"^ {0,3}>")
RE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RE_INTERVALO = re.compile(r"^(\d+)-(\d+)$")
RE_DIGITO = re.compile(r"\d")


@dataclass
class Fala:
    linha: int
    texto: str
    palavra_inicio: int
    palavra_fim: int


@dataclass
class Bloco:
    titulo: str
    nivel: int
    linha: int
    palavra_inicio: int
    palavra_fim: int = -1


@dataclass
class Cena:
    id: str
    tipo: str
    linha: int
    params: dict[str, str] = field(default_factory=dict)
    palavra_inicio: int = -1
    palavra_fim: int = -1

    @property
    def manual(self) -> bool:
        return registro.TIPOS[self.tipo].manual


@dataclass
class Short:
    id: str
    titulo: str
    linha: int
    linha_fim: int = -1
    palavra_inicio: int = -1
    palavra_fim: int = -1


@dataclass
class Aviso:
    tipo: str
    linha: int
    texto: str


@dataclass
class Roteiro:
    titulo: str
    origem: Path
    falas: list[Fala] = field(default_factory=list)
    blocos: list[Bloco] = field(default_factory=list)
    cenas: list[Cena] = field(default_factory=list)
    shorts: list[Short] = field(default_factory=list)
    avisos: list[Aviso] = field(default_factory=list)
    eventos: list[tuple[str, object]] = field(default_factory=list)
    total_palavras: int = 0

    def duracao(self, wpm: int = t.PALAVRAS_POR_MINUTO) -> float:
        return t.estimar_duracao(self.total_palavras, wpm)

    def narracao(self) -> str:
        return "\n\n".join(f.texto for f in self.falas) + "\n"

    def leitura(self) -> str:
        linhas = [f"# {self.titulo}", ""]
        for tipo, evento in self.eventos:
            if tipo == "bloco":
                linhas += ["", f"## {evento.titulo}", ""]
            elif tipo == "cena":
                linhas.append(f"<!-- {evento.tipo}: {evento.id} -->")
            elif tipo == "short-inicio":
                linhas.append(f"<!-- short ▶ {evento.id} — {evento.titulo} -->")
            elif tipo == "short-fim":
                linhas.append(f"<!-- short ■ {evento.id} -->")
            else:
                linhas += [evento.texto, ""]
        return "\n".join(linhas).strip() + "\n"

    def json(self) -> dict:
        return {
            "video": self.origem.parent.name,
            "titulo": self.titulo,
            "palavras": self.total_palavras,
            "duracao_estimada": round(self.duracao(), 1),
            "blocos": [
                {
                    "titulo": b.titulo,
                    "nivel": b.nivel,
                    "linha": b.linha,
                    "palavra_inicio": b.palavra_inicio,
                    "palavra_fim": b.palavra_fim,
                }
                for b in self.blocos
            ],
            "cenas": [
                {
                    "id": c.id,
                    "tipo": c.tipo,
                    "linha": c.linha,
                    "params": c.params,
                    "palavra_inicio": c.palavra_inicio,
                    "palavra_fim": c.palavra_fim,
                }
                for c in self.cenas
            ],
            "shorts": [
                {
                    "id": s.id,
                    "titulo": s.titulo,
                    "linha": s.linha,
                    "palavra_inicio": s.palavra_inicio,
                    "palavra_fim": s.palavra_fim,
                }
                for s in self.shorts
            ],
        }


def _atributos(conteudo: str) -> tuple[str, dict[str, str]]:
    cabeca = conteudo.split(maxsplit=1)[0] if conteudo.split() else ""
    params = {
        m.group(1): next(g for g in m.groups()[1:] if g is not None)
        for m in RE_ATRIBUTO.finditer(conteudo)
    }
    return cabeca, params


def ler(projeto: Projeto) -> Roteiro:
    if not projeto.script.is_file():
        raise ErroDeUso(f"{projeto.script} não existe")
    return interpretar(
        projeto.script.read_text(encoding="utf-8"),
        origem=projeto.script,
        base_video=projeto.raiz,
        base_repo=raiz_studio().parent,
    )


def interpretar(
    fonte: str,
    origem: Path,
    base_video: Path | None = None,
    base_repo: Path | None = None,
) -> Roteiro:
    roteiro = Roteiro(titulo=origem.parent.name, origem=origem)

    def erro(linha: int, msg: str) -> ErroDeUso:
        return ErroDeUso(f"{origem.name}:{linha}: {msg}")

    tokens: list[str] = []
    pendentes: list[Cena | Short] = []
    abertos: dict[str, Short] = {}
    ids: dict[str, int] = {}
    paragrafo: list[str] = []
    linha_paragrafo = 0
    dentro_de_cerca = False

    def fechar_paragrafo() -> None:
        nonlocal paragrafo
        if not paragrafo:
            return
        conteudo = t.limpar_bloco(" ".join(paragrafo))
        inicio = len(tokens)
        for pendente in pendentes:
            pendente.palavra_inicio = inicio
        pendentes.clear()
        tokens.extend(t.palavras(conteudo))
        fala = Fala(linha_paragrafo, conteudo, inicio, len(tokens))
        roteiro.falas.append(fala)
        roteiro.eventos.append(("fala", fala))
        paragrafo = []

    def registrar_id(id: str, linha: int) -> None:
        if not RE_ID.fullmatch(id):
            raise erro(linha, f"id '{id}' não é kebab-case (ex: mapa-de-calor)")
        if id in ids:
            raise erro(linha, f"id '{id}' já usado na linha {ids[id]}")
        ids[id] = linha

    for numero, bruta in enumerate(fonte.splitlines(), start=1):
        if RE_CERCA.match(bruta):
            fechar_paragrafo()
            dentro_de_cerca = not dentro_de_cerca
            continue
        if dentro_de_cerca:
            continue

        if marcador := RE_MARCADOR.match(bruta):
            fechar_paragrafo()
            especie, conteudo = marcador.group(1), marcador.group(2)
            cabeca, params = _atributos(conteudo)

            if especie == "cena":
                if not registro.existe(cabeca):
                    raise erro(
                        numero,
                        f"tipo de cena desconhecido: '{cabeca}' "
                        f"(tem: {', '.join(registro.nomes())})",
                    )
                if "id" not in params:
                    raise erro(numero, f"cena {cabeca} sem id=")
                registrar_id(params["id"], numero)
                id = params.pop("id")
                cena = Cena(id=id, tipo=cabeca, linha=numero, params=params)
                _validar_cena(roteiro, cena, erro, base_video, base_repo)
                roteiro.cenas.append(cena)
                roteiro.eventos.append(("cena", cena))
                pendentes.append(cena)

            elif cabeca == "inicio":
                if "id" not in params:
                    raise erro(numero, "short sem id=")
                if "titulo" not in params:
                    raise erro(numero, f"short '{params['id']}' sem titulo=")
                registrar_id(params["id"], numero)
                short = Short(id=params["id"], titulo=params["titulo"], linha=numero)
                abertos[short.id] = short
                roteiro.shorts.append(short)
                roteiro.eventos.append(("short-inicio", short))
                pendentes.append(short)

            elif cabeca == "fim":
                id = params.get("id", "")
                if id not in abertos:
                    raise erro(numero, f"short '{id}' fechado sem ter sido aberto")
                short = abertos.pop(id)
                short.linha_fim = numero
                short.palavra_fim = len(tokens)
                roteiro.eventos.append(("short-fim", short))

            else:
                raise erro(numero, f"short espera 'inicio' ou 'fim', veio '{cabeca}'")
            continue

        if titulo := RE_TITULO.match(bruta):
            fechar_paragrafo()
            nivel, nome = len(titulo.group(1)), titulo.group(2)
            if nivel == 1:
                roteiro.titulo = nome
                continue
            bloco = Bloco(nome, nivel, numero, len(tokens))
            roteiro.blocos.append(bloco)
            roteiro.eventos.append(("bloco", bloco))
            continue

        if RE_FALA.match(bruta):
            crua = t.sem_citacao(bruta)
            if not crua:
                fechar_paragrafo()
                continue
            if not paragrafo:
                linha_paragrafo = numero
            paragrafo.append(crua)
            _avisar(roteiro, numero, bruta, t.limpar(bruta))
            continue

        fechar_paragrafo()

    fechar_paragrafo()

    if pendentes:
        pendente = pendentes[0]
        raise erro(pendente.linha, f"marcador '{pendente.id}' não tem narração depois dele")
    if abertos:
        short = next(iter(abertos.values()))
        raise erro(short.linha, f"short '{short.id}' aberto e nunca fechado")

    roteiro.total_palavras = len(tokens)
    _fechar_intervalos(roteiro, len(tokens))
    return roteiro


def _fechar_intervalos(roteiro: Roteiro, total: int) -> None:
    for lista in (roteiro.cenas, roteiro.blocos):
        ordenada = sorted(lista, key=lambda x: x.palavra_inicio)
        for atual, proximo in zip(ordenada, ordenada[1:], strict=False):
            atual.palavra_fim = proximo.palavra_inicio
        if ordenada:
            ordenada[-1].palavra_fim = total


def _validar_cena(
    roteiro: Roteiro, cena: Cena, erro, base_video: Path | None, base_repo: Path | None
) -> None:
    tipo = registro.TIPOS[cena.tipo]

    if faltando := [p for p in tipo.obrigatorios if p not in cena.params]:
        raise erro(cena.linha, f"cena {cena.tipo} '{cena.id}' sem {'=, '.join(faltando)}=")
    if sobrando := [p for p in cena.params if p not in tipo.parametros]:
        raise erro(
            cena.linha,
            f"parâmetro desconhecido em {cena.tipo}: {', '.join(sobrando)} "
            f"(aceita: {', '.join(tipo.parametros)})",
        )

    base = base_video if tipo.base == "video" else base_repo
    if base is None:
        return

    for chave in tipo.fontes:
        if chave not in cena.params:
            continue
        caminho = base / cena.params[chave]
        if not caminho.is_file():
            raise erro(cena.linha, f"{chave}={cena.params[chave]} não existe ({caminho})")
        if chave == "arquivo" and "linhas" in cena.params:
            _validar_linhas(cena, caminho, erro)

    for chave in tipo.adiados:
        if chave in cena.params and not (base_video / cena.params[chave]).exists():
            roteiro.avisos.append(
                Aviso("fonte", cena.linha, f"{cena.id}: {cena.params[chave]}")
            )


def _validar_linhas(cena: Cena, caminho: Path, erro) -> None:
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


def _avisar(roteiro: Roteiro, numero: int, bruta: str, limpa: str) -> None:
    for trecho in t.RE_CRASE.findall(bruta):
        if trecho.strip():
            roteiro.avisos.append(Aviso("codigo", numero, trecho.strip()))
    if RE_DIGITO.search(limpa):
        roteiro.avisos.append(Aviso("digito", numero, limpa))
