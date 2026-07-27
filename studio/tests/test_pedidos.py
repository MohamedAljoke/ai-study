from pathlib import Path

import pytest

from studio import pedidos
from studio.pedidos import CARTELA, CONGELADO, PRONTO
from studio.projeto import ErroDeUso, Projeto
from studio.timeline import CenaEmTempo


def cena(id: str, inicio: float, fim: float, tipo: str = "manim") -> CenaEmTempo:
    return CenaEmTempo(id=id, tipo=tipo, inicio=inicio, fim=fim)


def arquivo(id: str, extensao: str = "mp4") -> Path:
    return Path(f"/videos/01/assets/{id}.{extensao}")


# --- quem fornece cada cena ---


def test_cena_com_arquivo_no_disco_e_a_propria_fonte():
    (pedido,) = pedidos.resolver([cena("a", 0.0, 5.0)], {"a": arquivo("a")})
    assert pedido.origem == PRONTO
    assert pedido.fonte == arquivo("a")
    assert not pedido.falta


def test_cena_sem_arquivo_congela_o_quadro_da_anterior():
    lista = pedidos.resolver([cena("a", 0.0, 5.0), cena("b", 5.0, 9.0)], {"a": arquivo("a")})
    assert lista[1].origem == CONGELADO
    assert lista[1].congela == "a"
    assert lista[1].fonte == arquivo("a")


def test_duas_cenas_seguidas_sem_arquivo_congelam_a_mesma_origem():
    lista = pedidos.resolver(
        [cena("a", 0.0, 5.0), cena("b", 5.0, 9.0), cena("c", 9.0, 12.0)],
        {"a": arquivo("a")},
    )
    assert [p.congela for p in lista] == ["", "a", "a"]


def test_congelamento_anda_pra_frente_quando_aparece_asset_novo():
    """A cena vazia herda da última que tem arquivo, não da primeira do vídeo."""
    lista = pedidos.resolver(
        [cena("a", 0.0, 5.0), cena("b", 5.0, 9.0), cena("c", 9.0, 12.0)],
        {"a": arquivo("a"), "b": arquivo("b")},
    )
    assert lista[2].congela == "b"


def test_primeira_cena_sem_arquivo_vira_cartela():
    """Não existe quadro anterior pra congelar — o vídeo não pode abrir em preto."""
    lista = pedidos.resolver([cena("a", 0.0, 5.0), cena("b", 5.0, 9.0)], {"b": arquivo("b")})
    assert lista[0].origem == CARTELA
    assert lista[0].fonte is None
    assert lista[0].congela == ""


def test_video_sem_asset_nenhum_e_so_cartela():
    lista = pedidos.resolver([cena("a", 0.0, 5.0), cena("b", 5.0, 9.0)], {})
    assert [p.origem for p in lista] == [CARTELA, CARTELA]


def test_timeline_vazia_nao_estoura():
    assert pedidos.resolver([], {}) == []


# --- o que a folha precisa saber ---


def test_a_fala_da_cena_atravessa_pro_pedido():
    (pedido,) = pedidos.resolver([cena("a", 0.0, 5.0)], {}, {"a": "e é aqui que a prova"})
    assert pedido.fala == "e é aqui que a prova"


def test_params_do_marcador_atravessam_intactos():
    linha = [CenaEmTempo("a", "manim", 0.0, 5.0, params={"classe": "ShipOverlay"})]
    (pedido,) = pedidos.resolver(linha, {})
    assert pedido.params == {"classe": "ShipOverlay"}


def test_duracao_sai_do_intervalo_da_timeline():
    (pedido,) = pedidos.resolver([cena("a", 12.5, 26.7)], {})
    assert pedido.duracao == pytest.approx(14.2)


def test_segundos_faltando_soma_so_o_que_nao_esta_pronto():
    lista = pedidos.resolver([cena("a", 0.0, 5.0), cena("b", 5.0, 9.0)], {"a": arquivo("a")})
    assert pedidos.segundos_faltando(lista) == pytest.approx(4.0)
    assert [p.id for p in pedidos.faltando(lista)] == ["b"]


# --- a varredura do disco ---


def test_asset_e_achado_por_qualquer_extensao(tmp_path):
    projeto = Projeto(tmp_path)
    projeto.assets.mkdir()
    (projeto.assets / "parity-prova.mov").write_bytes(b"")
    assert projeto.asset_de("parity-prova").name == "parity-prova.mov"


def test_cena_sem_arquivo_devolve_none(tmp_path):
    projeto = Projeto(tmp_path)
    projeto.assets.mkdir()
    assert projeto.asset_de("parity-prova") is None


def test_pasta_de_assets_que_nem_existe_ainda_devolve_none(tmp_path):
    assert Projeto(tmp_path).asset_de("parity-prova") is None


def test_duas_extensoes_pro_mesmo_id_e_erro_e_nao_sorteio(tmp_path):
    projeto = Projeto(tmp_path)
    projeto.assets.mkdir()
    (projeto.assets / "x.mp4").write_bytes(b"")
    (projeto.assets / "x.png").write_bytes(b"")
    with pytest.raises(ErroDeUso, match="x.mp4, x.png"):
        projeto.asset_de("x")


def test_id_parecido_nao_e_confundido(tmp_path):
    projeto = Projeto(tmp_path)
    projeto.assets.mkdir()
    (projeto.assets / "parity-prova-2.mp4").write_bytes(b"")
    assert projeto.asset_de("parity-prova") is None
