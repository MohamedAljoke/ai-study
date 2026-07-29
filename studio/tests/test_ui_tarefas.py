import pytest

from studio.projeto import ErroDeUso
from studio.ui import tarefas


@pytest.fixture(autouse=True)
def limpar():
    tarefas.esquecer()
    yield
    tarefas.esquecer()


@pytest.fixture
def casa(tmp_path, monkeypatch):
    """Um `studio/` de mentira, pra o subprocesso não depender dos meus vídeos de verdade."""
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "script.md").write_text("# {{TITULO}}\n", encoding="utf-8")
    video = tmp_path / "videos" / "01-teste"
    video.mkdir(parents=True)
    (video / "script.md").write_text("# Teste\n\n> Uma frase qualquer.\n", encoding="utf-8")
    monkeypatch.setenv("STUDIO_HOME", str(tmp_path))
    return tmp_path


def rodar(*args) -> tarefas.Tarefa:
    tarefa = tarefas.iniciar(*args)
    list(tarefas.acompanhar(tarefa.id))
    return tarefa


# --- o que pode virar linha de comando ---


def test_comando_inventado_nao_vira_subprocesso():
    with pytest.raises(ErroDeUso, match="desconhecido"):
        tarefas.iniciar("rm", "01")


def test_comando_que_ainda_e_stub_nao_roda():
    """`shorts` está no PIPELINE mas não tem implementação — sprint 7."""
    with pytest.raises(ErroDeUso, match="desconhecido"):
        tarefas.iniciar("shorts", "01")


def test_flag_que_o_comando_nao_declara_e_recusada():
    """A página não escolhe argumento de subprocesso: quem declara é o PIPELINE."""
    with pytest.raises(ErroDeUso, match="não tem a opção"):
        tarefas.iniciar("montar", "01", ["--saida=/etc/passwd"])


def test_flag_declarada_atravessa():
    assert tarefas._argumentos("montar", "01", ["--rascunho"]) == ["montar", "01", "--rascunho"]


def test_a_interface_nao_roda_a_si_mesma():
    with pytest.raises(ErroDeUso, match="a si mesma"):
        tarefas.iniciar("ui", "01")


# --- rodar de verdade ---


def test_etapa_que_da_certo_termina_em_zero_e_traz_a_saida(casa):
    tarefa = rodar("status", "01")
    assert tarefa.codigo == 0
    assert any("01-teste" in linha for linha in tarefa.linhas)


def test_erro_de_uso_chega_na_pagina_em_vez_de_sumir_no_stderr(casa):
    """O stderr entra no mesmo log: a mensagem de erro traz o conserto junto (§9)."""
    tarefa = rodar("status", "99")
    assert tarefa.codigo == 1
    assert any("erro:" in linha for linha in tarefa.linhas)


def test_acompanhar_entrega_toda_linha_uma_vez_so(casa):
    tarefa = tarefas.iniciar("status", "01")
    vistas = list(tarefas.acompanhar(tarefa.id))
    assert vistas == tarefa.linhas


def test_quem_chega_depois_do_fim_recebe_o_log_inteiro(casa):
    """A página recarregada no meio de uma montagem não pode perder o que já passou."""
    tarefa = rodar("status", "01")
    assert list(tarefas.acompanhar(tarefa.id)) == tarefa.linhas


def test_duas_etapas_ao_mesmo_tempo_brigariam_pelo_mesmo_build(casa):
    tarefas.iniciar("status", "01")
    with pytest.raises(ErroDeUso, match="já tem uma etapa rodando"):
        tarefas.iniciar("status", "01")


def test_terminada_uma_da_pra_comecar_a_proxima(casa):
    rodar("status", "01")
    assert tarefas.iniciar("status", "01").terminou is False


def test_tarefa_desconhecida_e_erro_legivel():
    with pytest.raises(ErroDeUso, match="tarefa desconhecida"):
        tarefas.obter("nao-existe")
