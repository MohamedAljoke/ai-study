import pytest

from studio.comandos.novo import novo
from studio.projeto import ErroDeUso, Projeto


@pytest.fixture
def casa(tmp_path, monkeypatch):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "script.md").write_text("# {{TITULO}}\n\nvídeo {{NUMERO}}\n", encoding="utf-8")
    (templates / "thumb.vars.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "videos").mkdir()
    monkeypatch.setenv("STUDIO_HOME", str(tmp_path))
    return tmp_path


def test_video_novo_nasce_com_a_pasta_de_assets(casa, capsys):
    """A pasta era `tapes/` até os geradores saírem — `novo` estava quebrado desde então."""
    assert novo("07-parity") == 0
    projeto = Projeto(casa / "videos" / "07-parity")
    assert projeto.assets.is_dir()
    assert projeto.build.is_dir()


def test_o_template_chega_com_titulo_e_numero_trocados(casa, capsys):
    novo("07-parity-em-uma-linha")
    script = (casa / "videos" / "07-parity-em-uma-linha" / "script.md").read_text()
    assert "# Parity em uma linha" in script
    assert "vídeo 07" in script


def test_criar_por_cima_de_video_que_existe_e_recusado(casa):
    novo("07-parity")
    with pytest.raises(ErroDeUso, match="já existe"):
        novo("07-parity")


def test_nome_fora_do_padrao_nn_slug_e_recusado(casa):
    with pytest.raises(ErroDeUso):
        novo("parity")
