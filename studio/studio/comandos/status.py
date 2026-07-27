"""studio status [NN] — em que passo o vídeo está e qual é o próximo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from studio import leitura
from studio import pedidos as registro_pedidos
from studio import texto as t
from studio.comandos import alinhar as gerador_alinhar
from studio.comandos import duble as gerador_duble
from studio.comandos import montar as gerador_montar
from studio.comandos import narracao as gerador_narracao
from studio.comandos import timeline as gerador_timeline
from studio.comandos.novo import _titulo
from studio.comandos.pedidos import levantar
from studio.projeto import ErroDeUso, Projeto, listar, pasta_templates, resolver

FALTANDO, OK, VELHO, ERRO, DUBLE = "faltando", "ok", "desatualizado", "erro", "dublê"
PARCIAL = "parcial"
"""Asset faltando não trava o pipeline: o vídeo monta congelando o quadro anterior (§3).
Como `dublê`, é estado que aparece no relatório sem virar o "próximo passo"."""

SEGUEM = (OK, DUBLE, PARCIAL)
"""Estados que não impedem o passo seguinte de ser o próximo."""


@dataclass
class Etapa:
    rotulo: str
    estado: str
    detalhe: str = ""
    dica: str = ""


def _template_puro(projeto: Projeto) -> bool:
    modelo = (pasta_templates() / "script.md").read_text(encoding="utf-8")
    esperado = modelo.replace("{{TITULO}}", _titulo(projeto.slug)).replace(
        "{{NUMERO}}", projeto.numero
    )
    return projeto.script.read_text(encoding="utf-8").strip() == esperado.strip()


def _roteiro(projeto: Projeto) -> Etapa:
    if not projeto.script.is_file():
        return Etapa("roteiro", FALTANDO, dica="criar script.md")

    if _template_puro(projeto):
        return Etapa("roteiro", FALTANDO, "template não editado", "escrever o roteiro")

    try:
        roteiro = leitura.ler(projeto)
    except ErroDeUso as erro:
        return Etapa("roteiro", ERRO, str(erro), "corrigir o roteiro")

    duracao = t.formatar_duracao(roteiro.duracao())
    aviso = "  ⚠ menos de 3 shorts" if len(roteiro.shorts) < 3 else ""
    detalhe = (
        f"{len(roteiro.blocos)} blocos, {len(roteiro.cenas)} cenas, "
        f"{len(roteiro.shorts)} shorts, ~{duracao}{aviso}"
    )
    return Etapa("roteiro", OK, detalhe)


def _derivado(
    rotulo: str,
    saida: Path,
    fontes: list[Path],
    dica: str,
    em_dia: Callable[[], bool] | None = None,
) -> Etapa:
    if not saida.exists():
        return Etapa(rotulo, FALTANDO, dica=dica)

    if em_dia is not None:
        return Etapa(rotulo, OK) if em_dia() else Etapa(rotulo, VELHO, "a entrada mudou", dica)

    nascimento = saida.stat().st_mtime
    velhas = [f.name for f in fontes if f.exists() and f.stat().st_mtime > nascimento]
    if velhas:
        return Etapa(rotulo, VELHO, f"mudou depois: {', '.join(velhas)}", dica)
    return Etapa(rotulo, OK)


def _etapas(projeto: Projeto) -> list[Etapa]:
    n = projeto.numero
    roteiro = _roteiro(projeto)

    audio, eh_duble = projeto.audio()
    dica_gravar = f"gravar {projeto.wav.name} lendo build/narration.txt"
    if not audio.is_file():
        gravar = Etapa("áudio", FALTANDO, dica=dica_gravar)
    elif eh_duble:
        detalhe = "voz sintética, não publicável"
        if not gerador_duble.em_dia(projeto):
            detalhe += f"  ⚠ velho, refazer com  studio duble {n}"
        gravar = Etapa("áudio", DUBLE, detalhe, dica_gravar)
    else:
        gravar = Etapa("áudio", OK)

    return [
        roteiro,
        _derivado(
            "narração",
            projeto.narracao_txt,
            [projeto.script],
            f"studio narracao {n}",
            em_dia=lambda: gerador_narracao.em_dia(projeto),
        ),
        gravar,
        _derivado(
            "alinhamento",
            projeto.palavras,
            [audio],
            f"studio alinhar {n}",
            em_dia=lambda: gerador_alinhar.em_dia(projeto),
        ),
        _derivado(
            "timeline",
            projeto.timeline,
            [projeto.marcadores, projeto.palavras],
            f"studio timeline {n}",
            em_dia=lambda: gerador_timeline.em_dia(projeto),
        ),
        _assets(projeto),
        _derivado(
            "montagem",
            projeto.video,
            [projeto.timeline],
            f"studio montar {n}",
            em_dia=lambda: gerador_montar.em_dia(projeto),
        ),
    ]


def _assets(projeto: Projeto) -> Etapa:
    """Quantas cenas já têm arquivo meu. Nunca fica "ok" com asset faltando.

    O vídeo monta mesmo assim (§3), congelando o quadro anterior — e é justamente por
    isso que o buraco tem que aparecer aqui: no vídeo ele não aparece.
    """
    n = projeto.numero
    if not projeto.timeline.is_file():
        return Etapa("assets", FALTANDO, dica=f"studio timeline {n}")

    lista = levantar(projeto)
    pendentes = registro_pedidos.faltando(lista)
    if not lista:
        return Etapa("assets", FALTANDO, "o roteiro não tem cena nenhuma", "marcar cenas")
    if not pendentes:
        return Etapa("assets", OK, f"{len(lista)} de {len(lista)}")

    segundos = registro_pedidos.segundos_faltando(lista)
    detalhe = (
        f"{len(lista) - len(pendentes)} de {len(lista)} — faltam "
        f"{t.formatar_duracao(segundos)} de vídeo"
    )
    return Etapa("assets", PARCIAL, detalhe, f"studio pedidos {n}")


def _imprimir(projeto: Projeto) -> None:
    etapas = _etapas(projeto)
    largura = max(len(e.rotulo) for e in etapas) + 2

    print(f"{'vídeo:':<{largura}}{projeto.nome}")
    for etapa in etapas:
        linha = f"{etapa.rotulo + ':':<{largura}}{etapa.estado}"
        if etapa.detalhe:
            linha += f" — {etapa.detalhe}"
        print(linha)

    pendente = next((e for e in etapas if e.estado not in SEGUEM), None)
    print()
    if pendente is None:
        print("próximo:  nada — o vídeo está montado")
    else:
        print(f"próximo:  {pendente.dica or pendente.rotulo}")

    if any(e.estado == DUBLE for e in etapas):
        print("⚠ rodando com dublê — o vídeo final ainda depende de eu gravar")
    if parcial := next((e for e in etapas if e.estado == PARCIAL), None):
        print(f"⚠ assets: {parcial.detalhe} — {parcial.dica}")


def status(numero: str | None) -> int:
    if numero:
        _imprimir(resolver(numero))
        return 0

    projetos = listar()
    if not projetos:
        raise ErroDeUso("nenhum vídeo ainda — comece com  studio novo 01-slug")

    for i, projeto in enumerate(projetos):
        if i:
            print()
        _imprimir(projeto)
    return 0
