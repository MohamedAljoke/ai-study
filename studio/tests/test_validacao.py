from pathlib import Path

import pytest

from studio import validacao
from studio.projeto import ErroDeUso
from studio.roteiro import Cena, Roteiro


def erro(linha: int, msg: str) -> ErroDeUso:
    return ErroDeUso(f"script.md:{linha}: {msg}")


def validar(cena: Cena, base_repo: Path | None = None):
    """Devolve o roteiro, pra dar pra olhar os avisos que sobraram nele."""
    roteiro = Roteiro(titulo="teste", origem=Path("script.md"))
    validacao.validar_cena(roteiro, cena, erro, base_repo)
    return roteiro


def test_parametro_obrigatorio_faltando():
    with pytest.raises(ErroDeUso, match="sem arquivo="):
        validar(Cena(id="x", tipo="codigo", linha=7))


def test_parametro_desconhecido_lista_os_aceitos():
    cena = Cena(id="x", tipo="card", linha=7, params={"titulo": "T", "cor": "azul"})
    with pytest.raises(ErroDeUso, match="parâmetro desconhecido em card: cor"):
        validar(cena)


def test_erro_carrega_a_linha_do_script():
    """Sem a linha eu não sei onde ir no arquivo — convenções §12."""
    with pytest.raises(ErroDeUso, match=r"^script\.md:42:"):
        validar(Cena(id="x", tipo="codigo", linha=42))


def test_sem_base_nao_checa_arquivo():
    cena = Cena(id="x", tipo="codigo", linha=7, params={"arquivo": "nao/existe.go"})
    validar(cena)  # base_repo=None: nada a conferir


def test_arquivo_de_codigo_que_nao_existe_estoura(tmp_path):
    cena = Cena(id="x", tipo="codigo", linha=7, params={"arquivo": "sumiu.go"})
    with pytest.raises(ErroDeUso, match="arquivo=sumiu.go não existe"):
        validar(cena, base_repo=tmp_path)


def test_intervalo_de_linhas_mal_escrito(tmp_path):
    (tmp_path / "board.go").write_text("um\ndois\ntrês\n")
    cena = Cena(id="x", tipo="codigo", linha=7, params={"arquivo": "board.go", "linhas": "12"})
    with pytest.raises(ErroDeUso, match="esperado a-b"):
        validar(cena, base_repo=tmp_path)


def test_intervalo_maior_que_o_arquivo(tmp_path):
    (tmp_path / "board.go").write_text("um\ndois\ntrês\n")
    cena = Cena(id="x", tipo="codigo", linha=7, params={"arquivo": "board.go", "linhas": "2-9"})
    with pytest.raises(ErroDeUso, match="que tem 3 linhas"):
        validar(cena, base_repo=tmp_path)


def test_intervalo_dentro_do_arquivo_passa(tmp_path):
    (tmp_path / "board.go").write_text("um\ndois\ntrês\n")
    cena = Cena(id="x", tipo="codigo", linha=7, params={"arquivo": "board.go", "linhas": "2-3"})
    assert validar(cena, base_repo=tmp_path).avisos == []


def test_nota_e_aceita_em_qualquer_tipo():
    """`nota=` é recado meu pra folha de pedidos, não parâmetro de um tipo só."""
    cena = Cena(id="x", tipo="terminal", linha=7, params={"nota": "gravar com o bench rodando"})
    assert validar(cena).avisos == []


def test_asset_que_ainda_nao_existe_nao_e_problema_do_roteiro(tmp_path):
    """Quem responde o que falta é a folha de pedidos, com duração junto — não aqui."""
    cena = Cena(id="parity", tipo="manim", linha=7, params={"classe": "ShipOverlay"})
    assert validar(cena, base_repo=tmp_path).avisos == []


def test_avisa_crase_e_digito_na_fala():
    roteiro = Roteiro(titulo="teste", origem=Path("script.md"))
    bruta = "> roda o `go test` e some 44"
    validacao.avisar_da_fala(roteiro, 12, bruta, "roda o go test e some 44")

    assert [(a.tipo, a.linha) for a in roteiro.avisos] == [("codigo", 12), ("digito", 12)]


def test_fala_limpa_nao_gera_aviso():
    roteiro = Roteiro(titulo="teste", origem=Path("script.md"))
    validacao.avisar_da_fala(roteiro, 12, "> uma frase comum", "uma frase comum")
    assert roteiro.avisos == []
