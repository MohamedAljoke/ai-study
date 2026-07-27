"""studio pedidos NN — a timeline vira a lista do que eu tenho que produzir.

O comando central do novo fluxo. Ele não gera mídia nenhuma: olha o que já existe em
`assets/`, cruza com a timeline e escreve `build/pedidos.md` — id, duração exata e o
trecho que eu falo durante a cena. Com isso eu abro o Manim sabendo o alvo.

Roda quantas vezes eu quiser enquanto produzo: é varredura de diretório, custa
milissegundos, e por isso não tem cache (§2 é pra coisa cara).
"""

from __future__ import annotations

from studio import artefatos, folha, pedidos
from studio import texto as t
from studio.pedidos import CONGELADO, PRONTO, Pedido
from studio.projeto import ErroDeUso, Projeto, resolver
from studio.timeline import Timeline

LARGURA_ID = 22
LARGURA_TIPO = 9

MARCA = {PRONTO: "pronto", CONGELADO: "falta (congela)", "cartela": "falta (cartela)"}


def _falas(projeto: Projeto, linha: Timeline) -> dict[str, str]:
    """O que eu falo em cada cena. Sem a narração no disco, a folha sai sem as citações."""
    if not projeto.narracao_txt.is_file():
        return {}
    narracao = projeto.narracao_txt.read_text(encoding="utf-8")
    return {c.id: t.trecho(narracao, c.palavra_inicio, c.palavra_fim) for c in linha.cenas}


def levantar(projeto: Projeto) -> list[Pedido]:
    """A pergunta "quem fornece cada cena" respondida a partir do disco.

    O `montar` chama isto também — os dois têm que enxergar exatamente a mesma coisa,
    senão a folha diz que falta e o vídeo mostra outra coisa.
    """
    linha = artefatos.ler_timeline(projeto.timeline)
    achados = {c.id: caminho for c in linha.cenas if (caminho := projeto.asset_de(c.id))}
    return pedidos.resolver(linha.cenas, achados, _falas(projeto, linha))


def _imprimir(lista: list[Pedido]) -> None:
    for pedido in lista:
        colunas = f"{pedido.id:<{LARGURA_ID}} {pedido.tipo:<{LARGURA_TIPO}}"
        print(f"  {colunas} {pedido.duracao:6.1f}s  {MARCA[pedido.origem]}")


def pedidos_cmd(numero: str) -> int:
    projeto = resolver(numero)
    if not projeto.timeline.is_file():
        raise ErroDeUso(
            f"falta o timeline.json — rode antes:  studio timeline {projeto.numero}"
        )

    lista = levantar(projeto)
    projeto.garantir_build()
    projeto.pedidos_md.write_text(folha.escrever(projeto.nome, lista), encoding="utf-8")

    _imprimir(lista)
    pendentes = pedidos.faltando(lista)
    print(
        f"\n{len(lista)} cenas — {len(lista) - len(pendentes)} prontas, "
        f"{len(pendentes)} faltando"
    )
    print(f"→ build/{projeto.pedidos_md.name}")

    if pendentes:
        segundos = pedidos.segundos_faltando(lista)
        print(f"\n{segundos:.0f}s de vídeo a produzir — largue cada arquivo em assets/<id>.*")
    return 0
