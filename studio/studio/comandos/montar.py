"""studio montar NN — timeline + assets + narração → video.mp4.

O marco do projeto: daqui pra frente o studio não ajuda a editar, ele monta.

Renderiza **um segmento por cena** e emenda no fim, em vez de um filtro gigante. Custa
disco e ganha as duas coisas que importam num pipeline sem revisão humana: quando uma
cena sai errada dá pra abrir só ela (§12), e trocar um substituto por mídia de verdade
re-renderiza um segmento, não sete minutos (§2).

Cena que ainda não existe não para a montagem (§3): ela mostra o último quadro da cena
anterior, congelado. Quem diz o que falta é a folha de pedidos e o resumo aqui embaixo —
nunca o silêncio.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from studio import cache, ffmpeg, marca, montagem, pedidos, relogio, substitutos
from studio.comandos.pedidos import levantar
from studio.ffmpeg import FINAL, RASCUNHO, Perfil
from studio.montagem import Plano, Segmento
from studio.pedidos import CONGELADO, Pedido
from studio.projeto import ErroDeUso, Projeto, resolver

FERRAMENTA = "montar/" + cache.versao_do_comando(
    __name__, montagem, pedidos, substitutos, ffmpeg, marca
)

LARGURA_ID = 22


def _perfil(rascunho: bool) -> Perfil:
    return RASCUNHO if rascunho else FINAL


def _planejar(projeto: Projeto, perfil: Perfil, lista: list[Pedido]) -> Plano:
    som, _ = projeto.audio()
    return montagem.planejar(lista, substitutos.caminhos(projeto, lista), som, perfil)


def _params_do_segmento(segmento: Segmento, perfil: Perfil) -> dict:
    return {"duracao": segmento.duracao, "parado": segmento.parado, **vars(perfil)}


def caminhos_dos_segmentos(projeto: Projeto, plano: Plano) -> list[Path]:
    return [projeto.segmento(plano.perfil.nome, s.id) for s in plano.segmentos]


def entradas_do_video(projeto: Projeto, plano: Plano) -> list[Path]:
    """O vídeo final é feito dos **segmentos**, não dos assets.

    Um só lugar calculando isso porque `em_dia` e `_emendar` têm que concordar: quando
    divergiram, o status dizia "desatualizado" e o `montar` dizia "já estava em dia" —
    duas respostas diferentes pra mesma pergunta, que é o pior jeito de perder confiança
    no cache.
    """
    return [*caminhos_dos_segmentos(projeto, plano), plano.audio]


def em_dia(projeto: Projeto, rascunho: bool = False) -> bool:
    """Quem gera é quem sabe se está velho. O status pergunta em vez de chutar mtime."""
    if not projeto.timeline.is_file():
        return False
    perfil = _perfil(rascunho)
    try:
        plano = _planejar(projeto, perfil, levantar(projeto))
    except ErroDeUso:
        return False
    saida = projeto.video_de(perfil.nome)
    if not all(e.exists() for e in entradas_do_video(projeto, plano)):
        return False
    return not cache.precisa_refazer(
        saida, entradas_do_video(projeto, plano), vars(perfil), FERRAMENTA
    )


def _renderizar(projeto: Projeto, plano: Plano) -> int:
    """Cada cena vira um mp4 normalizado. Devolve quantas foram refeitas agora."""
    perfil = plano.perfil
    feitos = 0
    for segmento in plano.segmentos:
        saida = projeto.segmento(perfil.nome, segmento.id)
        params = _params_do_segmento(segmento, perfil)
        if not cache.precisa_refazer(saida, [segmento.entrada], params, FERRAMENTA):
            continue
        ffmpeg.segmento(
            segmento.entrada, saida, segmento.duracao, segmento.parado, perfil, marca.FUNDO
        )
        cache.registrar(saida, [segmento.entrada], params, FERRAMENTA)
        feitos += 1
    return feitos


def _emendar(projeto: Projeto, plano: Plano) -> bool:
    """Junta os segmentos com a narração inteira. Devolve se refez alguma coisa."""
    perfil = plano.perfil
    saida = projeto.video_de(perfil.nome)
    entradas = entradas_do_video(projeto, plano)

    if not cache.precisa_refazer(saida, entradas, vars(perfil), FERRAMENTA):
        return False

    lista = projeto.segmentos / perfil.nome / "lista.txt"
    lista.parent.mkdir(parents=True, exist_ok=True)
    lista.write_text(
        ffmpeg.lista_concat(caminhos_dos_segmentos(projeto, plano)), encoding="utf-8"
    )
    ffmpeg.juntar(lista, plano.audio, saida, f"emendar o {saida.name}")
    cache.registrar(saida, entradas, vars(perfil), FERRAMENTA)
    return True


def _legenda(projeto: Projeto) -> bool:
    """A legenda vai ao lado, não queimada — no longo o YouTube usa o arquivo."""
    if not projeto.narracao_srt.is_file():
        return False
    shutil.copyfile(projeto.narracao_srt, projeto.legenda)
    return True


def _exigir(projeto: Projeto) -> None:
    n = projeto.numero
    if not projeto.timeline.is_file():
        raise ErroDeUso(f"falta o timeline.json — rode antes:  studio timeline {n}")
    som, _ = projeto.audio()
    if not som.is_file():
        raise ErroDeUso(
            f"nenhum áudio — grave {projeto.wav.name}, ou gere um provisório com  "
            f"studio duble {n}"
        )


def _cabecalho(plano: Plano, eh_duble: bool) -> None:
    perfil = plano.perfil
    print(
        f"{len(plano.segmentos)} cenas, {relogio.formatar_curto(plano.duracao)}, "
        f"{perfil.tamanho} @{perfil.fps}fps"
    )
    for segmento in plano.faltando:
        substituto = (
            f"congela o quadro de {segmento.congela}"
            if segmento.origem == CONGELADO
            else "cartela com o id"
        )
        print(f"  ⚠ {segmento.id:<{LARGURA_ID}} falta o asset — {substituto}")
    if eh_duble:
        print("  ⚠ narração do dublê — este arquivo não é publicável")


def montar(numero: str, rascunho: bool = False) -> int:
    projeto = resolver(numero)
    _exigir(projeto)

    perfil = _perfil(rascunho)
    lista = levantar(projeto)
    projeto.garantir_build()
    substitutos.desenhar(projeto, lista)

    plano = _planejar(projeto, perfil, lista)
    _, eh_duble = projeto.audio()
    _cabecalho(plano, eh_duble)

    feitos = _renderizar(projeto, plano)
    print(f"\n{feitos} segmentos renderizados, {len(plano.segmentos) - feitos} em cache")

    saida = projeto.video_de(perfil.nome)
    if _emendar(projeto, plano):
        print(f"→ build/{saida.name}")
    else:
        print(f"(build/{saida.name} já estava em dia)")

    if _legenda(projeto):
        print(f"→ build/{projeto.legenda.name}")

    if faltam := pedidos.faltando(lista):
        print(f"\n{len(faltam)} cenas ainda sem asset — build/{projeto.pedidos_md.name} lista")
    return 0
