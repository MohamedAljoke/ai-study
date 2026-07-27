"""O quadro parado que entra no lugar de uma cena que ainda não existe.

Dois casos, um assunto: congelar o último quadro da cena anterior, ou — quando não há
nada antes — desenhar a cartela com o id. Pra montagem os dois são a mesma coisa: uma
imagem que dura o tempo da cena.

Escreve em `build/substitutos/` e é cacheado (§2): o congelado depende só do asset de
origem, então trocar o placeholder de uma cena por mídia de verdade não refaz os outros.
Não imprime nada — quem conta o que aconteceu é o comando.
"""

from __future__ import annotations

from pathlib import Path

from studio import cache, ffmpeg, marca, placeholder
from studio.montagem import PARADAS
from studio.pedidos import CONGELADO, Pedido, faltando
from studio.projeto import Projeto

FERRAMENTA = "substituto/" + cache.versao_do_comando(__name__, placeholder, ffmpeg, marca)


def _params(pedido: Pedido) -> dict:
    return {"origem": pedido.origem, "tipo": pedido.tipo}


def caminho(projeto: Projeto, pedido: Pedido) -> Path:
    """Onde está (ou vai estar) o quadro desta cena. Só o caminho, sem desenhar nada.

    O `em_dia` do montar precisa da resposta sem renderizar — por isso caminho e
    desenho são funções separadas.

    Quando a cena emprestada já é imagem parada, ela mesma é o quadro: extrair o
    "último frame" de um PNG seria copiar o arquivo com passos no meio.
    """
    if pedido.origem == CONGELADO and pedido.fonte.suffix.lower() in PARADAS:
        return pedido.fonte
    return projeto.substituto(pedido.id)


def caminhos(projeto: Projeto, pedidos: list[Pedido]) -> dict[str, Path]:
    return {p.id: caminho(projeto, p) for p in faltando(pedidos)}


def desenhar(projeto: Projeto, pedidos: list[Pedido]) -> int:
    """Faz o que falta e devolve quantos quadros saíram agora."""
    feitos = 0
    for pedido in faltando(pedidos):
        saida = caminho(projeto, pedido)
        if saida == pedido.fonte:  # a cena emprestada já é uma imagem
            continue

        entradas = [pedido.fonte] if pedido.origem == CONGELADO else []
        if not cache.precisa_refazer(saida, entradas, _params(pedido), FERRAMENTA):
            continue

        if pedido.origem == CONGELADO:
            ffmpeg.ultimo_quadro(pedido.fonte, saida)
        else:
            placeholder.desenhar(pedido.id, pedido.tipo, saida)
        cache.registrar(saida, entradas, _params(pedido), FERRAMENTA)
        feitos += 1
    return feitos
