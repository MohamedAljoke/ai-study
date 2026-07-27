from pathlib import Path

from studio import ffmpeg


def test_escape_do_drawtext_protege_dois_pontos_e_apostrofo():
    # o filtro é parseado duas vezes; ':' cru corta o argumento no meio
    assert ffmpeg.escapar("board.go:43-60") == r"board.go\:43-60"
    assert ffmpeg.escapar("d'água") == r"d\'água"


def test_escape_da_barra_vem_antes_das_outras():
    # se a barra fosse escapada por último, ela escaparia o escape das anteriores
    assert ffmpeg.escapar(r"a\b:c") == r"a\\b\:c"


def test_lista_de_concat_usa_caminho_absoluto():
    # o demuxer resolve caminho relativo à lista, não ao diretório de quem chamou
    lista = ffmpeg.lista_concat([Path("build/segmentos/a.mp4")])
    assert lista.startswith("file '/")
    assert lista.endswith("build/segmentos/a.mp4'\n")


def test_uma_linha_por_segmento():
    linhas = ffmpeg.lista_concat([Path("a.mp4"), Path("b.mp4")]).splitlines()
    assert len(linhas) == 2


def test_rascunho_e_menor_e_mais_rapido_que_o_final():
    # o rascunho existe pra ciclo curto; se não for mais barato, não serve pra nada
    assert ffmpeg.RASCUNHO.largura < ffmpeg.FINAL.largura
    assert ffmpeg.RASCUNHO.crf > ffmpeg.FINAL.crf


def test_tamanho_do_perfil_e_o_que_o_ffmpeg_espera():
    assert ffmpeg.FINAL.tamanho == "1920x1080"


def test_binario_que_nao_existe_vira_erro_com_a_instalacao_junto():
    from studio.projeto import ErroDeUso

    try:
        ffmpeg.exigir("ffmpeg-que-nao-existe")
    except ErroDeUso as erro:
        assert "apt install ffmpeg" in str(erro)
    else:
        raise AssertionError("deveria ter recusado")
