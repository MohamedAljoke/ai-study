import json

import pytest

from studio import marca
from studio.projeto import Projeto
from studio.ui import estado

ROTEIRO = """# Batalha Naval

<!-- cena: terminal id=abertura nota="o bench rodando" -->

> Eu fiz o computador jogar trinta e duas mil vezes.

<!-- short: inicio id=uma-linha titulo="Uma linha" -->
<!-- cena: manim id=parity classe=ShipOverlay -->

> O menor navio ocupa duas casas.

<!-- short: fim id=uma-linha -->
"""


def projeto(tmp_path, roteiro: str = ROTEIRO) -> Projeto:
    p = Projeto(tmp_path / "01-teste")
    p.garantir_build()
    p.script.write_text(roteiro, encoding="utf-8")
    return p


def com_timeline(tmp_path, **params) -> Projeto:
    p = projeto(tmp_path)
    linha = {
        "video": p.nome,
        "audio": "narration.wav",
        "duracao": 20.0,
        "cenas": [
            {"id": "abertura", "tipo": "terminal", "inicio": 0.0, "fim": 8.0, "params": {}},
            {
                "id": "parity",
                "tipo": "manim",
                "inicio": 8.0,
                "fim": 20.0,
                "params": params or {"classe": "ShipOverlay"},
            },
        ],
    }
    p.timeline.write_text(json.dumps(linha), encoding="utf-8")
    return p


def asset(p: Projeto, nome: str) -> None:
    p.assets.mkdir(exist_ok=True)
    (p.assets / nome).write_bytes(b"fake")


# --- o roteiro ---


def test_script_valido_traz_a_previa_do_que_eu_vou_ler(tmp_path):
    dados = estado.script(projeto(tmp_path))
    assert dados["erro"] == ""
    assert dados["previa"]["titulo"] == "Batalha Naval"
    assert "trinta e duas mil vezes" in dados["previa"]["narracao"]


def test_script_invalido_devolve_erro_com_arquivo_e_linha_em_vez_de_estourar(tmp_path):
    quebrado = ROTEIRO.replace("id=parity", "id=abertura")
    dados = estado.script(projeto(tmp_path, quebrado))
    assert dados["previa"] is None
    assert "script.md:" in dados["erro"]
    assert "abertura" in dados["erro"]


def test_script_invalido_ainda_devolve_o_texto_pra_eu_consertar(tmp_path):
    """Se a página perdesse o texto no erro, eu não teria como corrigir o roteiro nela."""
    dados = estado.script(projeto(tmp_path, ROTEIRO.replace("id=parity", "id=abertura")))
    assert dados["texto"].startswith("# Batalha Naval")


def test_video_sem_script_nao_estoura(tmp_path):
    p = Projeto(tmp_path / "01-teste")
    p.garantir_build()
    assert estado.script(p) == {"texto": "", "assinatura": "", "erro": "", "previa": None}


def test_assinatura_muda_quando_o_script_muda(tmp_path):
    p = projeto(tmp_path)
    antes = estado.assinatura(p)
    p.script.write_text(ROTEIRO + "\n> mais uma frase.\n", encoding="utf-8")
    assert estado.assinatura(p) != antes


# --- as cenas ---


def test_sem_timeline_a_lista_de_cenas_vem_vazia(tmp_path):
    assert estado.cenas(projeto(tmp_path)) == []


def test_cena_com_asset_aponta_pro_arquivo_e_pra_url_da_midia(tmp_path):
    p = com_timeline(tmp_path)
    asset(p, "parity.mp4")
    cena = estado.cenas(p)[1]
    assert not cena["falta"]
    assert cena["arquivo"] == "parity.mp4"
    assert cena["midia"] == "/midia/01/assets/parity.mp4"


def test_cena_sem_asset_diz_de_quem_ela_congela_o_quadro(tmp_path):
    p = com_timeline(tmp_path)
    asset(p, "abertura.mp4")
    cena = estado.cenas(p)[1]
    assert cena["falta"]
    assert cena["congela"] == "abertura"
    assert cena["midia"] == ""


def test_a_marca_de_tempo_da_cena_sai_formatada_pra_ler(tmp_path):
    cena = estado.cenas(com_timeline(tmp_path))[1]
    assert (cena["inicio"], cena["fim"], cena["duracao"]) == ("00:08.0", "00:20.0", 12.0)


def test_params_do_marcador_chegam_no_card(tmp_path):
    cena = estado.cenas(com_timeline(tmp_path, classe="HeatMap"))[1]
    assert cena["params"] == {"classe": "HeatMap"}


def test_placar_conta_o_que_falta_produzir(tmp_path):
    p = com_timeline(tmp_path)
    asset(p, "abertura.mp4")
    placar = estado.de_projeto(p)["placar"]
    assert (placar["total"], placar["prontas"], placar["faltando"]) == (2, 1, 1)
    assert placar["restante"] == "12s"


def test_placar_de_video_completo_nao_pede_mais_nada(tmp_path):
    p = com_timeline(tmp_path)
    asset(p, "abertura.mp4")
    asset(p, "parity.png")
    assert estado.de_projeto(p)["placar"]["restante"] == ""


# --- etapas e próximo passo ---


def test_as_etapas_vem_na_ordem_do_pipeline(tmp_path):
    rotulos = [e["rotulo"] for e in estado.etapas(projeto(tmp_path))]
    assert rotulos == [
        "roteiro",
        "narração",
        "áudio",
        "alinhamento",
        "timeline",
        "assets",
        "montagem",
    ]


def test_uma_etapa_so_e_marcada_como_a_proxima(tmp_path):
    lista = estado.etapas(projeto(tmp_path))
    assert sum(1 for e in lista if e["proxima"]) == 1


def test_o_proximo_passo_vem_como_texto_pronto(tmp_path):
    """É o mesmo que o `studio status` imprime — a página não recalcula a regra."""
    assert estado.de_projeto(projeto(tmp_path))["proximo"].startswith("studio narracao")


def test_asset_faltando_nao_vira_o_proximo_passo(tmp_path):
    """Cena sem arquivo é `parcial` (§3): aparece no relatório, mas não trava o pipeline."""
    etapa = next(e for e in estado.etapas(com_timeline(tmp_path)) if e["rotulo"] == "assets")
    assert etapa["estado"] == "parcial"
    assert not etapa["proxima"]


# --- mídia e cores ---


def test_sem_gravacao_a_pagina_sabe_que_esta_no_duble(tmp_path):
    p = projeto(tmp_path)
    p.duble.write_bytes(b"fake")
    assert estado.midia(p) == {
        "audio": "/midia/01/audio",
        "duble": True,
        "video": "",
        "rascunho": "",
    }


def test_minha_voz_tira_a_marca_de_duble(tmp_path):
    p = projeto(tmp_path)
    p.wav.write_bytes(b"real")
    assert estado.midia(p)["duble"] is False


def test_o_css_sai_de_marca_py_e_nao_repete_hex(tmp_path):
    css = estado.marca_css()
    assert f"--fundo: {marca.FUNDO};" in css
    assert f"--acento: {marca.ACENTO};" in css


def test_o_estado_inteiro_e_serializavel(tmp_path):
    """A rota só faz json.dumps disso. Path solto no dicionário quebraria a página."""
    p = com_timeline(tmp_path)
    asset(p, "parity.mov")
    json.dumps(estado.de_projeto(p))


def test_extensao_de_asset_aceita_video_e_imagem_parada():
    assert "mp4" in estado.EXTENSOES and "png" in estado.EXTENSOES


@pytest.mark.parametrize("campo", ["numero", "nome", "etapas", "proximo"])
def test_resumo_tem_o_que_o_seletor_de_video_precisa(tmp_path, campo):
    assert campo in estado.resumo(projeto(tmp_path))
