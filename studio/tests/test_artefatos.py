import json

import pytest

from studio import artefatos
from studio.projeto import ErroDeUso

MARCADORES = {
    "video": "01-batalha-naval",
    "titulo": "Vídeo 01",
    "palavras": 1093,
    "duracao_estimada": 437.2,
    "blocos": [{"titulo": "Abertura", "nivel": 2, "linha": 3, "palavra_inicio": 0}],
    "cenas": [
        {
            "id": "abertura-bench",
            "tipo": "terminal",
            "linha": 21,
            "params": {"fonte": "tapes/bench.tape"},
            "palavra_inicio": 0,
            "palavra_fim": 106,
        }
    ],
    "shorts": [
        {
            "id": "95-para-44",
            "titulo": "De 95 tiros para 44",
            "linha": 24,
            "palavra_inicio": 12,
            "palavra_fim": 96,
        }
    ],
}

PALAVRAS = {
    "video": "01-batalha-naval",
    "duracao": 421.837,
    "palavras": 2,
    "lista": [
        {"indice": 0, "palavra": "Eu", "inicio": 0.0, "fim": 0.18, "score": 0.53},
        {"indice": 1, "palavra": "fiz", "inicio": 0.3, "fim": 0.52, "score": 0.815},
    ],
}


def escrever(tmp_path, nome, dados):
    caminho = tmp_path / nome
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return caminho


def test_marcadores_do_formato_real(tmp_path):
    m = artefatos.ler_marcadores(escrever(tmp_path, "marcadores.json", MARCADORES))

    assert m.video == "01-batalha-naval"
    assert m.palavras == 1093
    assert m.cenas[0].id == "abertura-bench"
    assert m.cenas[0].params == {"fonte": "tapes/bench.tape"}
    assert m.cenas[0].palavra_fim == 106
    assert m.shorts[0].titulo == "De 95 tiros para 44"


def test_bloco_e_campo_extra_sao_ignorados(tmp_path):
    """A timeline não usa bloco. Campo a mais no JSON não pode quebrar a leitura."""
    dados = {**MARCADORES, "inventado": 1}
    dados["cenas"] = [{**MARCADORES["cenas"][0], "futuro": "foco"}]
    assert artefatos.ler_marcadores(escrever(tmp_path, "m.json", dados)).cenas[0].tipo


def cena_sem(campo: str) -> dict:
    cena = {k: v for k, v in MARCADORES["cenas"][0].items() if k != campo}
    return {**MARCADORES, "cenas": [cena]}


def test_cena_sem_params_usa_o_padrao(tmp_path):
    dados = cena_sem("params")
    assert artefatos.ler_marcadores(escrever(tmp_path, "m.json", dados)).cenas[0].params == {}


def test_cena_sem_campo_obrigatorio_diz_qual(tmp_path):
    dados = cena_sem("palavra_inicio")
    with pytest.raises(ErroDeUso, match="cena sem palavra_inicio"):
        artefatos.ler_marcadores(escrever(tmp_path, "m.json", dados))


def test_marcadores_sem_contagem_de_palavras(tmp_path):
    dados = {k: v for k, v in MARCADORES.items() if k != "palavras"}
    with pytest.raises(ErroDeUso, match="sem palavras"):
        artefatos.ler_marcadores(escrever(tmp_path, "m.json", dados))


def test_arquivo_que_nao_existe(tmp_path):
    with pytest.raises(ErroDeUso, match="não existe"):
        artefatos.ler_marcadores(tmp_path / "sumiu.json")


def test_json_truncado_nao_estoura_cru(tmp_path):
    caminho = tmp_path / "words.json"
    caminho.write_text('{"lista": [{"indice": 0,', encoding="utf-8")
    with pytest.raises(ErroDeUso, match="não é JSON válido"):
        artefatos.ler_palavras(caminho)


def test_json_que_e_uma_lista_no_topo(tmp_path):
    caminho = tmp_path / "words.json"
    caminho.write_text("[]", encoding="utf-8")
    with pytest.raises(ErroDeUso, match="objeto JSON no topo"):
        artefatos.ler_palavras(caminho)


def test_palavras_viram_o_tipo_do_alinhador(tmp_path):
    palavras = artefatos.ler_palavras(escrever(tmp_path, "words.json", PALAVRAS))

    assert [p.indice for p in palavras] == [0, 1]
    assert palavras[0].palavra == "Eu"
    assert palavras[1].inicio == 0.3
    assert not palavras[0].estimada


def test_duracao_vem_do_words_json(tmp_path):
    assert artefatos.duracao_do_audio(escrever(tmp_path, "w.json", PALAVRAS)) == 421.837


def test_words_json_sem_duracao_manda_realinhar(tmp_path):
    dados = {k: v for k, v in PALAVRAS.items() if k != "duracao"}
    with pytest.raises(ErroDeUso, match="studio alinhar"):
        artefatos.duracao_do_audio(escrever(tmp_path, "w.json", dados))


TIMELINE = {
    "video": "01-batalha-naval",
    "audio": "narration.duble.wav",
    "duracao": 421.837,
    "cenas": [
        {
            "id": "abertura-bench",
            "tipo": "terminal",
            "inicio": 0.0,
            "fim": 40.58,
            "palavra_inicio": 0,
            "palavra_fim": 96,
            "params": {"nota": "bench rodando"},
        }
    ],
}


def test_timeline_volta_com_as_cenas_em_tempo(tmp_path):
    linha = artefatos.ler_timeline(escrever(tmp_path, "timeline.json", TIMELINE))

    assert linha.duracao == 421.837
    assert linha.cenas[0].id == "abertura-bench"
    assert linha.cenas[0].duracao == 40.58
    assert linha.cenas[0].params["nota"] == "bench rodando"


def test_timeline_sem_duracao_e_arquivo_incompleto(tmp_path):
    dados = {k: v for k, v in TIMELINE.items() if k != "duracao"}
    with pytest.raises(ErroDeUso, match="refaça o build"):
        artefatos.ler_timeline(escrever(tmp_path, "timeline.json", dados))


def test_cena_sem_campo_obrigatorio_diz_qual_faltou(tmp_path):
    dados = dict(TIMELINE)
    dados["cenas"] = [{k: v for k, v in TIMELINE["cenas"][0].items() if k != "inicio"}]
    with pytest.raises(ErroDeUso, match="cena sem inicio"):
        artefatos.ler_timeline(escrever(tmp_path, "timeline.json", dados))


def test_intervalo_de_palavras_volta_junto_com_o_tempo(tmp_path):
    """É ele que deixa a folha de pedidos citar o que eu falo durante a cena."""
    linha = artefatos.ler_timeline(escrever(tmp_path, "timeline.json", TIMELINE))
    (cena,) = linha.cenas
    assert (cena.palavra_inicio, cena.palavra_fim) == (0, 96)
