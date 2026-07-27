import pytest

from studio import cache


@pytest.fixture
def build(tmp_path):
    entrada = tmp_path / "narration.txt"
    entrada.write_text("a regra é uma linha só")
    saida = tmp_path / "words.json"
    saida.write_text("[]")
    return entrada, saida


def test_saida_que_nao_existe_precisa_ser_feita(tmp_path, build):
    entrada, _ = build
    assert cache.precisa_refazer(tmp_path / "nada.json", [entrada])


def test_saida_sem_marca_precisa_ser_refeita(build):
    entrada, saida = build
    assert cache.precisa_refazer(saida, [entrada])


def test_registrar_deixa_em_dia(build):
    entrada, saida = build
    cache.registrar(saida, [entrada])
    assert not cache.precisa_refazer(saida, [entrada])


def test_mudar_a_entrada_invalida(build):
    entrada, saida = build
    cache.registrar(saida, [entrada])
    entrada.write_text("outro texto")
    assert cache.precisa_refazer(saida, [entrada])


def test_mudar_o_parametro_invalida(build):
    entrada, saida = build
    cache.registrar(saida, [entrada], {"idioma": "pt"})
    assert not cache.precisa_refazer(saida, [entrada], {"idioma": "pt"})
    assert cache.precisa_refazer(saida, [entrada], {"idioma": "en"})


def test_mudar_a_ferramenta_invalida(build):
    """Sem isso, mexer no gerador serve arquivo velho como se fosse novo."""
    entrada, saida = build
    cache.registrar(saida, [entrada], ferramenta="alinhar/abc123")
    assert cache.precisa_refazer(saida, [entrada], ferramenta="alinhar/def456")


def test_conteudo_igual_com_nome_diferente_e_assinatura_diferente(tmp_path):
    um = tmp_path / "um.txt"
    outro = tmp_path / "outro.txt"
    um.write_text("igual")
    outro.write_text("igual")
    assert cache.assinatura([um]) != cache.assinatura([outro])


def test_diretorio_como_entrada_soma_o_conteudo(tmp_path):
    pasta = tmp_path / "tapes"
    pasta.mkdir()
    (pasta / "a.tape").write_text("um")
    antes = cache.assinatura([pasta])

    (pasta / "b.tape").write_text("dois")
    assert cache.assinatura([pasta]) != antes


def test_entrada_que_sumiu_estoura(tmp_path):
    with pytest.raises(FileNotFoundError):
        cache.assinatura([tmp_path / "fantasma.txt"])


def test_registrar_o_que_nao_foi_gerado_estoura(tmp_path, build):
    entrada, _ = build
    with pytest.raises(FileNotFoundError):
        cache.registrar(tmp_path / "nada.json", [entrada])


def test_versao_muda_quando_o_modulo_muda():
    from studio import alinhador, legendas

    assert cache.versao_de(alinhador) != cache.versao_de(legendas)
    assert cache.versao_de(alinhador) == cache.versao_de(alinhador)


def test_versao_do_comando_inclui_o_proprio_modulo():
    """A serialização do JSON mora no comando: mexer nele tem que invalidar."""
    from studio import alinhador
    from studio.comandos import alinhar, narracao

    assert alinhar.FERRAMENTA != narracao.FERRAMENTA
    assert cache.versao_do_comando(alinhar.__name__) != cache.versao_de(alinhador)


def test_arquivo_intocado_nao_conta_como_editado(build):
    entrada, saida = build
    cache.registrar(saida, [entrada])
    assert not cache.foi_editado(saida)


def test_edicao_a_mao_e_detectada(build):
    """O timeline.json é editável de propósito — sobrescrever calado seria pior."""
    entrada, saida = build
    cache.registrar(saida, [entrada])

    saida.write_text('[{"inicio": 161.9}]')
    assert cache.foi_editado(saida)


def test_edicao_a_mao_nao_confunde_com_entrada_velha(build):
    """Mexer no arquivo gerado não faz o cache achar que a entrada mudou."""
    entrada, saida = build
    cache.registrar(saida, [entrada])

    saida.write_text("mexido")
    assert not cache.precisa_refazer(saida, [entrada])


def test_marca_de_versao_antiga_nao_acusa_edicao(build):
    """Marca sem a 2ª linha: não dá pra saber, e chutar 'foi editado' travaria o pipeline."""
    entrada, saida = build
    cache.registrar(saida, [entrada])
    marca = saida.parent / f"{saida.name}.hash"
    marca.write_text(marca.read_text().splitlines()[0] + "\n")

    assert cache.foi_editado(saida) is False
    assert not cache.precisa_refazer(saida, [entrada])


def test_saida_sem_marca_nenhuma_nao_acusa_edicao(build):
    _, saida = build
    assert cache.foi_editado(saida) is False
