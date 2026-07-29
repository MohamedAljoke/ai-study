"""O estado de um vídeo como dado serializável. Sem HTTP, sem FastAPI, sem print.

É o núcleo testável da UI, e a fronteira que impede a página de inventar regra: tudo aqui
é tradução do que `comandos/status.py` e `comandos/pedidos.py` já respondem (§8). Quando a
página mostrar estado errado, o bug é neste arquivo ou lá — nunca no JavaScript.
"""

from __future__ import annotations

from pathlib import Path

from studio import cache, leitura, marca, relogio
from studio import pedidos as registro
from studio import texto as t
from studio.comandos import status
from studio.comandos.pedidos import levantar
from studio.projeto import ErroDeUso, Projeto, listar
from studio.roteiro import Roteiro

EXTENSOES = ("mp4", "mov", "webm", "png", "jpg", "jpeg", "gif")
"""O que a página aceita como asset. A montagem trata vídeo e imagem parado igual."""


def assinatura(projeto: Projeto) -> str:
    """Hash do `script.md` no disco, pra detectar edição por fora enquanto eu escrevo."""
    return cache.assinatura([projeto.script]) if projeto.script.is_file() else ""


def marca_css() -> str:
    """As cores do canal viram variáveis de CSS.

    A folha de estilo **não** repete hex nenhum: `marca.py` existe justamente pra o azul
    da página não sair meio tom diferente do azul da cartela.
    """
    cores = {
        "fundo": marca.FUNDO,
        "fundo-alt": marca.FUNDO_ALT,
        "texto": marca.TEXTO,
        "acento": marca.ACENTO,
    }
    linhas = "\n".join(f"  --{nome}: {hexa};" for nome, hexa in cores.items())
    return f":root {{\n{linhas}\n}}\n"


# --- as etapas ---


def etapas(projeto: Projeto) -> list[dict]:
    lista = status.etapas(projeto)
    pendente = status.proximo(lista)
    return [
        {
            "rotulo": etapa.rotulo,
            "estado": etapa.estado,
            "detalhe": etapa.detalhe,
            "dica": etapa.dica,
            "proxima": etapa is pendente,
        }
        for etapa in lista
    ]


def _proximo(lista: list[dict]) -> str:
    proxima = next((e for e in lista if e["proxima"]), None)
    if proxima is None:
        return "nada — o vídeo está montado"
    return proxima["dica"] or proxima["rotulo"]


# --- o roteiro ---


def _previa(roteiro: Roteiro) -> dict:
    return {
        "titulo": roteiro.titulo,
        "narracao": roteiro.narracao(),
        "palavras": roteiro.total_palavras,
        "duracao": t.formatar_duracao(roteiro.duracao()),
        "cenas": [
            {"id": c.id, "tipo": c.tipo, "linha": c.linha, "params": c.params}
            for c in roteiro.cenas
        ],
        "shorts": [{"id": s.id, "titulo": s.titulo, "linha": s.linha} for s in roteiro.shorts],
        "avisos": [
            {"tipo": a.tipo, "linha": a.linha, "texto": a.texto} for a in roteiro.avisos
        ],
    }


def script(projeto: Projeto) -> dict:
    """O texto do `script.md` e o que ele produz — ou o erro, com arquivo e linha (§12)."""
    if not projeto.script.is_file():
        return {"texto": "", "assinatura": "", "erro": "", "previa": None}

    dados = {
        "texto": projeto.script.read_text(encoding="utf-8"),
        "assinatura": assinatura(projeto),
        "erro": "",
        "previa": None,
    }
    try:
        dados["previa"] = _previa(leitura.ler(projeto))
    except ErroDeUso as erro:
        dados["erro"] = str(erro)
    return dados


# --- as cenas ---


def _midia(projeto: Projeto, arquivo: Path | None) -> str:
    if arquivo is None:
        return ""
    return f"/midia/{projeto.numero}/assets/{arquivo.name}"


def cenas(projeto: Projeto) -> list[dict]:
    """Um card por cena, na ordem do vídeo. Vazio enquanto não houver timeline."""
    if not projeto.timeline.is_file():
        return []

    lista = levantar(projeto)
    return [
        {
            "id": pedido.id,
            "tipo": pedido.tipo,
            "inicio": relogio.formatar(pedido.inicio),
            "fim": relogio.formatar(pedido.fim),
            "duracao": round(pedido.duracao, 1),
            "origem": pedido.origem,
            "falta": pedido.falta,
            "congela": pedido.congela,
            "params": pedido.params,
            "fala": pedido.fala,
            "arquivo": pedido.fonte.name if pedido.origem == registro.PRONTO else "",
            "midia": _midia(projeto, pedido.fonte) if pedido.origem == registro.PRONTO else "",
        }
        for pedido in lista
    ]


def _placar(lista: list[dict]) -> dict:
    faltando = [c for c in lista if c["falta"]]
    segundos = sum(c["duracao"] for c in faltando)
    return {
        "total": len(lista),
        "prontas": len(lista) - len(faltando),
        "faltando": len(faltando),
        "restante": t.formatar_duracao(segundos) if faltando else "",
    }


# --- os arquivos que a página toca ---


def midia(projeto: Projeto) -> dict:
    audio, eh_duble = projeto.audio()
    rascunho = projeto.video_de("rascunho")
    return {
        "audio": f"/midia/{projeto.numero}/audio" if audio.is_file() else "",
        "duble": eh_duble,
        "video": f"/midia/{projeto.numero}/video" if projeto.video.is_file() else "",
        "rascunho": f"/midia/{projeto.numero}/rascunho" if rascunho.is_file() else "",
    }


# --- o pacote inteiro ---


def resumo(projeto: Projeto) -> dict:
    """O suficiente pro seletor de vídeos: nome e em que passo está."""
    lista = etapas(projeto)
    return {
        "numero": projeto.numero,
        "nome": projeto.nome,
        "etapas": lista,
        "proximo": _proximo(lista),
    }


def de_projeto(projeto: Projeto) -> dict:
    lista = etapas(projeto)
    das_cenas = cenas(projeto)
    return {
        "numero": projeto.numero,
        "nome": projeto.nome,
        "etapas": lista,
        "proximo": _proximo(lista),
        "script": script(projeto),
        "cenas": das_cenas,
        "placar": _placar(das_cenas),
        "midia": midia(projeto),
    }


def videos() -> list[dict]:
    return [resumo(projeto) for projeto in listar()]
