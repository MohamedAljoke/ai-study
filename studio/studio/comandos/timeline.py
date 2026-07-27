"""studio timeline NN — marcadores + words.json → timeline.json + shorts.json."""

from __future__ import annotations

import json

from studio import artefatos, cache, conferencia, relogio, timeline
from studio.projeto import ErroDeUso, Projeto, resolver

FERRAMENTA = "timeline/" + cache.versao_do_comando(
    __name__, timeline, conferencia, artefatos, relogio
)

LARGURA_TIPO = 9
LARGURA_ID = 20


def saidas(projeto: Projeto) -> tuple:
    return (projeto.timeline, projeto.shorts_json)


def _entradas(projeto: Projeto) -> list:
    return [projeto.marcadores, projeto.palavras]


def em_dia(projeto: Projeto) -> bool:
    """Quem gera é quem sabe se está velho. O status pergunta em vez de chutar mtime."""
    if not all(e.is_file() for e in _entradas(projeto)):
        return False
    return all(
        not cache.precisa_refazer(saida, _entradas(projeto), {}, FERRAMENTA)
        for saida in saidas(projeto)
    )


def _exigir_entradas(projeto: Projeto) -> None:
    n = projeto.numero
    if not projeto.marcadores.is_file():
        raise ErroDeUso(f"falta o marcadores.json — rode antes:  studio narracao {n}")
    if not projeto.palavras.is_file():
        raise ErroDeUso(f"falta o words.json — rode antes:  studio alinhar {n}")


def _detalhe(cena: timeline.CenaEmTempo) -> str:
    if dados := cena.params.get("dados"):
        return f"({dados})"
    if arquivo := cena.params.get("arquivo"):
        linhas = f":{cena.params['linhas']}" if "linhas" in cena.params else ""
        return f"({arquivo}{linhas})"
    if titulo := cena.params.get("titulo"):
        return f"“{titulo}”"
    if classe := cena.params.get("classe"):
        return f"({classe})"
    return ""


def _imprimir(linha: timeline.Timeline, avisos: list[conferencia.Aviso]) -> None:
    print(f"{len(linha.cenas)} cenas posicionadas, {len(linha.shorts)} shorts")
    print(f"duração total {relogio.formatar_curto(linha.duracao)}")
    print()

    for cena in linha.cenas:
        marca = relogio.formatar(cena.inicio)
        colunas = f"{cena.tipo:<{LARGURA_TIPO}} {cena.id:<{LARGURA_ID}}"
        print(f"  {marca}  {colunas} {_detalhe(cena)}".rstrip())

    if linha.shorts:
        print()
        for short in linha.shorts:
            faixa = f"{relogio.formatar(short.inicio)}–{relogio.formatar(short.fim)}"
            print(f"  short  {short.id:<{LARGURA_ID}} {faixa}  {short.duracao:.0f}s")

    if avisos:
        print("\navisos:")
        for aviso in avisos:
            print(f"  {aviso.texto}")


def _recusar_sobrescrever(projeto: Projeto) -> None:
    editados = [s for s in saidas(projeto) if cache.foi_editado(s)]
    if not editados:
        return
    nomes = ", ".join(f"build/{s.name}" for s in editados)
    raise ErroDeUso(
        f"{nomes} foi editado à mão depois de gerado, e regerar apagaria a correção.\n"
        f"  studio timeline {projeto.numero} --forcar   sobrescreve mesmo assim"
    )


def timeline_cmd(numero: str, forcar: bool = False) -> int:
    projeto = resolver(numero)
    _exigir_entradas(projeto)

    marcadores = artefatos.ler_marcadores(projeto.marcadores)
    palavras = artefatos.ler_palavras(projeto.palavras)
    duracao = artefatos.duracao_do_audio(projeto.palavras)
    som, eh_duble = projeto.audio()

    linha = timeline.montar(marcadores, palavras, duracao, audio=som.name)
    avisos = conferencia.conferir(linha)

    projeto.garantir_build()
    entradas = _entradas(projeto)
    conteudos = {
        projeto.timeline: linha.json(),
        projeto.shorts_json: linha.json_shorts(),
    }
    refazer = [s for s in saidas(projeto) if cache.precisa_refazer(s, entradas, {}, FERRAMENTA)]

    if refazer and not forcar:
        _recusar_sobrescrever(projeto)

    for saida in refazer:
        saida.write_text(
            json.dumps(conteudos[saida], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        cache.registrar(saida, entradas, {}, FERRAMENTA)

    _imprimir(linha, avisos)

    if refazer:
        print()
        for saida in saidas(projeto):
            print(f"→ build/{saida.name}")
    else:
        print("\n(sem mudança nos marcadores nem no alinhamento — já estava em dia)")

    if eh_duble:
        print("\n⚠ tempos vindos do dublê. Regravar com a minha voz refaz tudo isto.")
    return 0
