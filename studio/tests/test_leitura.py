from studio.leitura import atributos


def test_cabeca_e_o_primeiro_token():
    cabeca, params = atributos("terminal id=play-demo fonte=tapes/play.tape")
    assert cabeca == "terminal"
    assert params == {"id": "play-demo", "fonte": "tapes/play.tape"}


def test_valor_com_espaco_entre_aspas():
    _, params = atributos('inicio id=uma-linha titulo="Uma linha, 15 tiros a menos"')
    assert params["titulo"] == "Uma linha, 15 tiros a menos"


def test_aspas_simples_tambem_valem():
    _, params = atributos("inicio id=x titulo='Com aspas simples'")
    assert params["titulo"] == "Com aspas simples"


def test_valor_vazio_entre_aspas():
    _, params = atributos('card id=x titulo=""')
    assert params["titulo"] == ""


def test_marcador_sem_atributo_nenhum():
    assert atributos("tela") == ("tela", {})


def test_marcador_vazio_nao_quebra():
    assert atributos("") == ("", {})


def test_caminho_com_dois_pontos_e_barra_sobrevive():
    _, params = atributos("codigo id=x arquivo=battleships/internal/game/board.go linhas=23-40")
    assert params["arquivo"] == "battleships/internal/game/board.go"
    assert params["linhas"] == "23-40"
