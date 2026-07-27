"""Quem fornece cada cena: arquivo meu, quadro congelado da anterior, ou cartela.

O studio não gera mídia (§3). Ele diz o que falta e junta o que chegou — e esta é a
pergunta que separa as duas coisas. Um lugar só responde: a folha de pedidos e a
montagem consultam **este** módulo, e por isso não conseguem discordar sobre o que a
cena `parity-prova` mostra.

Função pura: recebe as cenas e um dicionário de caminhos, não vasculha disco. Quem sabe
procurar em `assets/` é `Projeto.asset_de` (§12).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from studio.timeline import CenaEmTempo

PRONTO, CONGELADO, CARTELA = "pronto", "congelado", "cartela"
"""Como a cena vai aparecer no vídeo. Só `PRONTO` é material de verdade."""


@dataclass(frozen=True)
class Pedido:
    """Uma cena e o que entra nela. Vira uma seção do `pedidos.md` e um segmento."""

    id: str
    tipo: str
    inicio: float
    fim: float
    origem: str
    fonte: Path | None = None
    """De onde sai a imagem. `None` = ninguém tem nada, vai ser cartela."""
    congela: str = ""
    """Id da cena que empresta o último quadro. Só faz sentido em `CONGELADO`."""
    params: dict[str, str] = field(default_factory=dict)
    fala: str = ""
    """O que eu falo enquanto a cena está no ar — é isso que define a animação."""

    @property
    def duracao(self) -> float:
        return self.fim - self.inicio

    @property
    def falta(self) -> bool:
        return self.origem != PRONTO


def resolver(
    cenas: list[CenaEmTempo],
    achados: dict[str, Path],
    falas: dict[str, str] | None = None,
) -> list[Pedido]:
    """Percorre as cenas em ordem; quem não tem arquivo herda o quadro da última que teve.

    Congelar esconde o buraco de propósito, pra o vídeo ficar assistível antes de estar
    pronto. Quem mostra o buraco é a folha de pedidos e a saída do comando, nunca o
    vídeo — ver §3.
    """
    falas = falas or {}
    pedidos = []
    ultimo: tuple[str, Path] | None = None

    for cena in cenas:
        arquivo = achados.get(cena.id)
        if arquivo is not None:
            origem, fonte, congela = PRONTO, arquivo, ""
            ultimo = (cena.id, arquivo)
        elif ultimo is not None:
            origem, (congela, fonte) = CONGELADO, ultimo
        else:
            # nada antes desta cena: não existe quadro pra congelar, e o vídeo tem que
            # começar mostrando alguma coisa
            origem, fonte, congela = CARTELA, None, ""

        pedidos.append(
            Pedido(
                id=cena.id,
                tipo=cena.tipo,
                inicio=cena.inicio,
                fim=cena.fim,
                origem=origem,
                fonte=fonte,
                congela=congela,
                params=cena.params,
                fala=falas.get(cena.id, ""),
            )
        )
    return pedidos


def faltando(pedidos: list[Pedido]) -> list[Pedido]:
    return [p for p in pedidos if p.falta]


def segundos_faltando(pedidos: list[Pedido]) -> float:
    """Quanto vídeo eu ainda tenho que produzir. É a estimativa de trabalho da folha."""
    return sum(p.duracao for p in faltando(pedidos))
