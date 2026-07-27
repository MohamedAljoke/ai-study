from studio import relogio


def test_zero():
    assert relogio.formatar(0.0) == "00:00.0"
    assert relogio.formatar_curto(0.0) == "00:00"


def test_marca_de_cena_tem_decimo():
    assert relogio.formatar(22.44) == "00:22.4"
    assert relogio.formatar(180.25) == "03:00.2"


def test_arredonda_antes_de_dividir():
    """59.96 vira 01:00.0, nunca 00:60.0."""
    assert relogio.formatar(59.96) == "01:00.0"
    assert relogio.formatar_curto(59.6) == "01:00"


def test_passando_de_uma_hora_mostra_hora():
    assert relogio.formatar(3661.5) == "1:01:01.5"
    assert relogio.formatar_curto(3661.5) == "1:01:02"


def test_abaixo_de_uma_hora_nao_mostra_hora():
    assert relogio.formatar(3599.9) == "59:59.9"


def test_duracao_do_video_01():
    """421,8s de áudio: o que o comando imprime como duração total."""
    assert relogio.formatar_curto(421.837) == "07:02"


def test_negativo_vira_zero():
    """Nunca deve acontecer, mas imprimir '-1:-30' seria pior que imprimir 0."""
    assert relogio.formatar(-5.0) == "00:00.0"
