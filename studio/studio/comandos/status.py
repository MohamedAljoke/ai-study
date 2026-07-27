"""studio status [NN] — em que passo o vídeo está e qual é o próximo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from studio import roteiro as parser
from studio import texto as t
from studio.comandos import alinhar as gerador_alinhar
from studio.comandos import duble as gerador_duble
from studio.comandos import narracao as gerador_narracao
from studio.comandos.novo import _titulo
from studio.projeto import ErroDeUso, Projeto, listar, pasta_templates, resolver

FALTANDO, OK, VELHO, ERRO, DUBLE = "faltando", "ok", "desatualizado", "erro", "dublê"


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
        roteiro = parser.ler(projeto)
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
            [projeto.script, projeto.palavras],
            f"studio timeline {n}",
        ),
        _derivado("assets", projeto.assets, [projeto.timeline], f"studio assets {n}"),
        _derivado("montagem", projeto.video, [projeto.timeline], f"studio montar {n}"),
    ]


def _imprimir(projeto: Projeto) -> None:
    etapas = _etapas(projeto)
    largura = max(len(e.rotulo) for e in etapas) + 2

    print(f"{'vídeo:':<{largura}}{projeto.nome}")
    for etapa in etapas:
        linha = f"{etapa.rotulo + ':':<{largura}}{etapa.estado}"
        if etapa.detalhe:
            linha += f" — {etapa.detalhe}"
        print(linha)

    pendente = next((e for e in etapas if e.estado not in (OK, DUBLE)), None)
    print()
    if pendente is None:
        print("próximo:  nada — o vídeo está montado")
    else:
        print(f"próximo:  {pendente.dica or pendente.rotulo}")

    if any(e.estado == DUBLE for e in etapas):
        print("⚠ rodando com dublê — o vídeo final ainda depende de eu gravar")


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
