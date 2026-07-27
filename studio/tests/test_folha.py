from pathlib import Path

from studio import folha, pedidos
from studio.timeline import CenaEmTempo


def cena(id: str, inicio: float, fim: float, tipo: str = "manim", **params) -> CenaEmTempo:
    return CenaEmTempo(id=id, tipo=tipo, inicio=inicio, fim=fim, params=params)


def escrever(cenas, achados=None, falas=None) -> str:
    lista = pedidos.resolver(list(cenas), achados or {}, falas or {})
    return folha.escrever("01-batalha-naval", lista)


def test_cena_que_falta_diz_onde_largar_o_arquivo():
    texto = escrever([cena("parity-prova", 34.1, 48.3)])
    assert "falta — largue em `assets/parity-prova.<ext>`" in texto


def test_cena_pronta_mostra_o_arquivo_que_foi_achado():
    achados = {"a": Path("/videos/01/assets/a.mov")}
    texto = escrever([cena("a", 0.0, 5.0)], achados)
    assert "✓ pronto — `assets/a.mov`" in texto


def test_duracao_da_cena_aparece_no_titulo():
    """É o número que eu levo pro Manim — sem ele a folha não serve pra nada."""
    texto = escrever([cena("parity-prova", 34.1, 48.3)])
    assert "**14.2s**" in texto
    assert "00:34.1 → 00:48.3" in texto


def test_a_fala_da_cena_sai_como_citacao():
    texto = escrever([cena("a", 0.0, 5.0)], falas={"a": "um navio de duas casas"})
    assert "> um navio de duas casas" in texto


def test_fala_longa_quebra_em_varias_linhas_de_citacao():
    fala = "palavra " * 60
    texto = escrever([cena("a", 0.0, 5.0)], falas={"a": fala})
    citadas = [linha for linha in texto.splitlines() if linha.startswith("> ")]
    assert len(citadas) > 1
    assert all(len(linha) <= folha.COLUNA + 2 for linha in citadas)


def test_cena_sem_fala_nao_deixa_citacao_vazia():
    texto = escrever([cena("a", 0.0, 5.0)])
    assert not [linha for linha in texto.splitlines() if linha.startswith(">")]


def test_params_do_marcador_aparecem_pra_eu_saber_o_que_animar():
    texto = escrever([cena("a", 0.0, 5.0, classe="ShipOverlay")])
    assert "`classe=ShipOverlay`" in texto


def test_cena_congelada_diz_de_quem_ela_herda_o_quadro():
    achados = {"a": Path("/videos/01/assets/a.mp4")}
    texto = escrever([cena("a", 0.0, 5.0), cena("b", 5.0, 9.0)], achados)
    assert "congela o último quadro de `b`" not in texto
    assert "congela o último quadro de `a`" in texto


def test_cena_sem_nada_antes_dela_avisa_da_cartela():
    texto = escrever([cena("a", 0.0, 5.0)])
    assert "cartela com o id" in texto


def test_resumo_conta_prontas_faltando_e_o_tempo_a_produzir():
    achados = {"a": Path("/videos/01/assets/a.mp4")}
    texto = escrever(
        [cena("a", 0.0, 60.0), cena("b", 60.0, 130.0), cena("c", 130.0, 180.0)], achados
    )
    assert "3 cenas · 1 prontas · 2 faltando · 02:00 de vídeo a produzir" in texto


def test_todas_as_cenas_entram_na_ordem_do_video():
    texto = escrever([cena("a", 0.0, 5.0), cena("b", 5.0, 9.0), cena("c", 9.0, 12.0)])
    assert texto.index("`a`") < texto.index("`b`") < texto.index("`c`")


def test_folha_de_video_sem_cena_nenhuma_ainda_e_markdown_valido():
    texto = escrever([])
    assert texto.startswith("# Pedidos — 01-batalha-naval")
    assert texto.endswith("\n")
