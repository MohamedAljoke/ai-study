import json

import pytest

pytest.importorskip("fastapi", reason="a interface é extra opcional: uv sync --extra ui")

from fastapi.testclient import TestClient  # noqa: E402

from studio.projeto import Projeto  # noqa: E402
from studio.ui import servidor, tarefas  # noqa: E402

ROTEIRO = """# Teste

<!-- cena: terminal id=abertura -->

> Uma frase qualquer pra ter narração.

<!-- cena: manim id=parity classe=ShipOverlay -->

> Outra frase, pra segunda cena.
"""

TIMELINE = {
    "video": "01-teste",
    "audio": "narration.wav",
    "duracao": 20.0,
    "cenas": [
        {"id": "abertura", "tipo": "terminal", "inicio": 0.0, "fim": 8.0, "params": {}},
        {"id": "parity", "tipo": "manim", "inicio": 8.0, "fim": 20.0, "params": {}},
    ],
}


@pytest.fixture
def projeto(tmp_path, monkeypatch) -> Projeto:
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "script.md").write_text("# {{TITULO}}\n", encoding="utf-8")
    (tmp_path / "templates" / "thumb.vars.json").write_text("{}\n", encoding="utf-8")
    p = Projeto(tmp_path / "videos" / "01-teste")
    p.garantir_build()
    p.script.write_text(ROTEIRO, encoding="utf-8")
    p.timeline.write_text(json.dumps(TIMELINE), encoding="utf-8")
    monkeypatch.setenv("STUDIO_HOME", str(tmp_path))
    tarefas.esquecer()
    return p


@pytest.fixture
def cliente(projeto) -> TestClient:
    return TestClient(servidor.criar_app())


# --- a página ---


def test_a_pagina_e_as_cores_saem_do_servidor(cliente):
    assert "<title>studio" in cliente.get("/").text
    assert "--acento:" in cliente.get("/pagina.css").text


# --- começar um vídeo do zero ---


def test_criar_video_pela_pagina_faz_a_pasta_com_o_template(cliente, projeto):
    resposta = cliente.post("/api/videos", json={"nome": "02-arvores-de-busca"})

    assert resposta.status_code == 200
    assert resposta.json()["numero"] == "02"
    novo = projeto.raiz.parent / "02-arvores-de-busca"
    assert novo.joinpath("assets").is_dir()
    assert "# Arvores de busca" in novo.joinpath("script.md").read_text(encoding="utf-8")


def test_o_video_criado_aparece_na_listagem(cliente):
    cliente.post("/api/videos", json={"nome": "02-arvores-de-busca"})
    assert [v["numero"] for v in cliente.get("/api/videos").json()] == ["01", "02"]


def test_nome_fora_do_padrao_volta_como_erro_de_uso(cliente):
    resposta = cliente.post("/api/videos", json={"nome": "Árvores de Busca"})

    assert resposta.status_code == 400
    assert "NN-slug" in resposta.json()["erro"]


def test_repetir_o_numero_de_outro_video_e_recusado(cliente):
    resposta = cliente.post("/api/videos", json={"nome": "01-outra-coisa"})

    assert resposta.status_code == 400
    assert "já é do 01-teste" in resposta.json()["erro"]


def test_criar_por_cima_de_video_que_existe_e_recusado(cliente):
    """A página não pode ser um jeito mais fácil de apagar roteiro por cima."""
    resposta = cliente.post("/api/videos", json={"nome": "01-teste"})

    assert resposta.status_code == 400
    assert "já existe" in resposta.json()["erro"]


# --- estado ---


def test_a_lista_de_videos_traz_o_proximo_passo(cliente):
    (video,) = cliente.get("/api/videos").json()
    assert video["numero"] == "01"
    assert video["proximo"]


def test_video_que_nao_existe_e_400_com_mensagem_e_nao_traceback(cliente):
    resposta = cliente.get("/api/videos/99")
    assert resposta.status_code == 400
    assert "99" in resposta.json()["erro"]


def test_o_estado_traz_script_cenas_e_placar(cliente):
    dados = cliente.get("/api/videos/01").json()
    assert dados["script"]["previa"]["titulo"] == "Teste"
    assert [c["id"] for c in dados["cenas"]] == ["abertura", "parity"]
    assert dados["placar"] == {"total": 2, "prontas": 0, "faltando": 2, "restante": "20s"}


# --- o roteiro ---


def test_salvar_o_script_grava_e_revalida(cliente, projeto):
    atual = cliente.get("/api/videos/01").json()["script"]
    novo = ROTEIRO + "\n> Uma frase a mais no fim.\n"
    dados = cliente.put(
        "/api/videos/01/script", json={"texto": novo, "assinatura": atual["assinatura"]}
    ).json()
    assert "uma frase a mais no fim" in dados["previa"]["narracao"].lower()
    assert projeto.script.read_text(encoding="utf-8") == novo


def test_script_invalido_e_salvo_mesmo_assim_com_o_erro_apontando_a_linha(cliente):
    atual = cliente.get("/api/videos/01").json()["script"]
    quebrado = ROTEIRO.replace("id=parity", "id=abertura")
    dados = cliente.put(
        "/api/videos/01/script", json={"texto": quebrado, "assinatura": atual["assinatura"]}
    ).json()
    assert "script.md:" in dados["erro"]
    assert dados["previa"] is None


def test_edicao_por_fora_nao_e_sobrescrita_em_silencio(cliente, projeto):
    """Mesmo princípio do `--forcar` do timeline (§5): conserto meu não some sozinho."""
    velha = cliente.get("/api/videos/01").json()["script"]["assinatura"]
    projeto.script.write_text(ROTEIRO + "\n> editado no editor de texto.\n", encoding="utf-8")

    resposta = cliente.put(
        "/api/videos/01/script", json={"texto": "outro", "assinatura": velha}
    )
    assert resposta.status_code == 400
    assert "recarregue" in resposta.json()["erro"]
    assert "editado no editor de texto" in projeto.script.read_text(encoding="utf-8")


# --- os arquivos que eu largo ---


def test_asset_largado_vira_arquivo_com_a_extensao_que_veio(cliente, projeto):
    resposta = cliente.post(
        "/api/videos/01/assets/parity",
        files={"arquivo": ("saida.mov", b"video", "video/quicktime")},
    )
    assert resposta.json()["arquivo"] == "parity.mov"
    assert (projeto.assets / "parity.mov").read_bytes() == b"video"


def test_trocar_a_extensao_nao_deixa_o_arquivo_velho_pra_tras(cliente, projeto):
    """Dois arquivos com o mesmo id fazem `asset_de` recusar a cena inteira."""
    cliente.post("/api/videos/01/assets/parity", files={"arquivo": ("a.mp4", b"1")})
    cliente.post("/api/videos/01/assets/parity", files={"arquivo": ("a.png", b"2")})
    assert [p.name for p in sorted(projeto.assets.iterdir())] == ["parity.png"]
    assert projeto.asset_de("parity").name == "parity.png"


def test_asset_de_cena_que_nao_existe_e_recusado(cliente, projeto):
    resposta = cliente.post(
        "/api/videos/01/assets/inventada", files={"arquivo": ("x.mp4", b"1")}
    )
    assert resposta.status_code == 400
    assert not projeto.assets.exists()


def test_id_com_caminho_dentro_nao_escreve_fora_de_assets(cliente, projeto):
    resposta = cliente.post(
        "/api/videos/01/assets/..%2F..%2Fscript", files={"arquivo": ("x.mp4", b"1")}
    )
    assert resposta.status_code in (400, 404)
    assert projeto.script.read_text(encoding="utf-8") == ROTEIRO


def test_extensao_estranha_e_recusada_com_a_lista_do_que_serve(cliente):
    resposta = cliente.post(
        "/api/videos/01/assets/parity", files={"arquivo": ("x.exe", b"1")}
    )
    assert resposta.status_code == 400
    assert "mp4" in resposta.json()["erro"]


def test_apagar_asset_devolve_a_cena_pro_estado_de_falta(cliente):
    cliente.post("/api/videos/01/assets/parity", files={"arquivo": ("x.mp4", b"1")})
    cenas = cliente.delete("/api/videos/01/assets/parity").json()["cenas"]
    assert cenas[1]["falta"]


def test_audio_que_nao_e_wav_e_recusado(cliente, projeto):
    resposta = cliente.post(
        "/api/videos/01/audio", files={"arquivo": ("narracao.mp3", b"som")}
    )
    assert resposta.status_code == 400
    assert not projeto.wav.exists()


def test_wav_largado_vira_a_narracao_do_video(cliente, projeto):
    dados = cliente.post(
        "/api/videos/01/audio", files={"arquivo": ("narration.wav", b"som")}
    ).json()
    assert projeto.wav.read_bytes() == b"som"
    assert dados["duble"] is False


# --- mídia ---


def test_asset_pronto_pode_ser_visto_na_pagina(cliente):
    cliente.post("/api/videos/01/assets/parity", files={"arquivo": ("x.png", b"imagem")})
    assert cliente.get("/midia/01/assets/parity.png").content == b"imagem"


def test_midia_nao_serve_arquivo_de_fora_da_pasta(cliente):
    assert cliente.get("/midia/01/assets/..%2F..%2Fscript.md").status_code in (400, 404)


# --- etapas rodando ---


def test_rodar_uma_etapa_devolve_o_id_e_o_log_escorre(cliente):
    tarefa = cliente.post("/api/tarefas", json={"comando": "status", "numero": "01"}).json()
    with cliente.stream("GET", f"/api/tarefas/{tarefa['id']}/log") as fluxo:
        texto = "".join(fluxo.iter_text())
    assert "01-teste" in texto
    assert '"fim": 0' in texto


def test_comando_proibido_nao_vira_subprocesso(cliente):
    resposta = cliente.post("/api/tarefas", json={"comando": "rm -rf /", "numero": "01"})
    assert resposta.status_code == 400


def test_log_de_tarefa_inexistente_e_erro_legivel(cliente):
    assert cliente.get("/api/tarefas/nao-existe/log").status_code == 400
