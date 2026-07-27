"""studio narracao NN — script.md → narration.txt, o texto que eu leio."""

from __future__ import annotations

import json
from collections import Counter

from studio import cache, leitura, validacao
from studio import roteiro as parser
from studio import texto as t
from studio.projeto import resolver

FERRAMENTA = "narracao/" + cache.versao_do_comando(__name__, leitura, validacao, parser, t)

EXPLICACAO = {
    "codigo": "código na narração — eu leio diferente do que está escrito",
    "digito": 'dígito na narração — eu leio "noventa e cinco", o alinhador vê "95"',
}


def saidas(projeto) -> tuple:
    return (projeto.narracao_txt, projeto.leitura, projeto.marcadores)


def em_dia(projeto, wpm: int = t.PALAVRAS_POR_MINUTO) -> bool:
    """Quem gera é quem sabe se está velho. O status pergunta em vez de chutar mtime."""
    return all(
        not cache.precisa_refazer(saida, [projeto.script], {"wpm": wpm}, FERRAMENTA)
        for saida in saidas(projeto)
    )


def _avisos(roteiro: parser.Roteiro) -> list[str]:
    linhas = []

    for tipo, explicacao in EXPLICACAO.items():
        achados = [a for a in roteiro.avisos if a.tipo == tipo]
        if not achados:
            continue
        linhas.append(f"  {len(achados)}x {explicacao}")
        for aviso in achados[:3]:
            trecho = aviso.texto if len(aviso.texto) <= 60 else aviso.texto[:57] + "..."
            linhas.append(f"    linha {aviso.linha}: {trecho}")
        if len(achados) > 3:
            linhas.append(f"    (+{len(achados) - 3})")

    if len(roteiro.shorts) < 3:
        linhas.append(
            f"  {len(roteiro.shorts)} shorts marcados — menos de 3 é sinal de roteiro morno"
        )

    return linhas


def _resumo(roteiro: parser.Roteiro, wpm: int) -> None:
    duracao = t.formatar_duracao(roteiro.duracao(wpm))
    print(
        f"narration.txt — {t.formatar_numero(roteiro.total_palavras)} palavras, "
        f"~{duracao} a {wpm} wpm"
    )

    if roteiro.cenas:
        tipos = Counter(c.tipo for c in roteiro.cenas)
        detalhe = ", ".join(f"{n} {tipo}" for tipo, n in tipos.most_common())
        print(f"{len(roteiro.cenas)} cenas: {detalhe}")
    else:
        print("0 cenas — o roteiro ainda não tem marcadores")

    if roteiro.shorts:
        partes = []
        for short in roteiro.shorts:
            palavras = short.palavra_fim - short.palavra_inicio
            duracao = t.formatar_duracao(t.estimar_duracao(palavras, wpm))
            partes.append(f"{short.id} (~{duracao})")
        print(f"{len(roteiro.shorts)} shorts: {', '.join(partes)}")

    if avisos := _avisos(roteiro):
        print("\navisos:")
        print("\n".join(avisos))


def narracao(numero: str, wpm: int = t.PALAVRAS_POR_MINUTO) -> int:
    projeto = resolver(numero)
    roteiro = leitura.ler(projeto)
    projeto.garantir_build()

    conteudos = (
        roteiro.narracao(),
        roteiro.leitura(),
        json.dumps(roteiro.json(), indent=2, ensure_ascii=False) + "\n",
    )
    params = {"wpm": wpm}

    refeito = False
    for saida, conteudo in zip(saidas(projeto), conteudos, strict=True):
        if cache.precisa_refazer(saida, [projeto.script], params, FERRAMENTA):
            saida.write_text(conteudo, encoding="utf-8")
            cache.registrar(saida, [projeto.script], params, FERRAMENTA)
            refeito = True

    _resumo(roteiro, wpm)
    if not refeito:
        print("\n(sem mudança no script.md — arquivos já estavam em dia)")
    return 0
