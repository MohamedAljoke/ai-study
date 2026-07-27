from studio import alinhador as a
from studio.alinhador import Alinhada


def alinhadas(*trios) -> list[Alinhada]:
    return [Alinhada(palavra, inicio, fim, score) for palavra, inicio, fim, score in trios]


def test_chave_ignora_acento_pontuacao_e_caixa():
    assert a.chave("Não,") == a.chave("nao") == "nao"
    assert a.chave("stdout.") == "stdout"
    assert a.chave("—") == ""


def test_casar_devolve_uma_palavra_por_palavra_do_texto():
    nossas = ["A", "regra", "é", "uma."]
    saida = a.casar(nossas, alinhadas(("a", 0.0, 0.4, 0.9)), duracao=2.0)

    assert [p.palavra for p in saida] == nossas
    assert [p.indice for p in saida] == [0, 1, 2, 3]


def test_casar_usa_o_tempo_do_alinhador_quando_a_palavra_bate():
    saida = a.casar(
        ["parity", "é", "melhor"],
        alinhadas(("Parity", 1.0, 1.5, 0.97), ("e", 1.5, 1.6, 0.8), ("melhor", 1.6, 2.2, 0.9)),
        duracao=3.0,
    )

    assert [(p.inicio, p.fim, p.score) for p in saida] == [
        (1.0, 1.5, 0.97),
        (1.5, 1.6, 0.8),
        (1.6, 2.2, 0.9),
    ]
    assert not any(p.estimada for p in saida)


def test_palavra_engolida_pelo_alinhador_vira_tempo_interpolado_e_marcado():
    saida = a.casar(
        ["um", "dois", "três"],
        alinhadas(("um", 0.0, 1.0, 0.9), ("tres", 3.0, 4.0, 0.9)),
        duracao=5.0,
    )

    meio = saida[1]
    assert meio.palavra == "dois"
    assert meio.estimada
    assert (meio.inicio, meio.fim) == (1.0, 3.0)
    assert not saida[0].estimada and not saida[2].estimada


def test_buraco_nas_pontas_estica_ate_zero_e_ate_o_fim_do_audio():
    saida = a.casar(
        ["antes", "meio", "depois"],
        alinhadas(("meio", 2.0, 3.0, 0.9),),
        duracao=6.0,
    )

    assert (saida[0].inicio, saida[0].fim) == (0.0, 2.0)
    assert (saida[2].inicio, saida[2].fim) == (3.0, 6.0)
    assert saida[0].estimada and saida[2].estimada


def test_sem_nenhuma_ancora_espalha_pelo_audio_inteiro():
    saida = a.casar(["um", "dois"], [], duracao=4.0)

    assert [(p.inicio, p.fim) for p in saida] == [(0.0, 2.0), (2.0, 4.0)]
    assert all(p.estimada for p in saida)


def test_palavra_sem_tempo_nao_vira_ancora():
    saida = a.casar(
        ["um", "dois"],
        alinhadas(("um", 0.0, 1.0, 0.9), ("dois", None, None, 0.0)),
        duracao=3.0,
    )

    assert saida[1].estimada
    assert (saida[1].inicio, saida[1].fim) == (1.0, 3.0)


def test_repeticao_no_audio_nao_desalinha_o_resto():
    """Eu errei a frase e repeti: o alinhador ouve palavras a mais.

    O que vier depois do trecho repetido tem que continuar com o tempo certo.
    """
    nossas = ["a", "regra", "é", "uma", "linha", "só"]
    ouvidas = alinhadas(
        ("a", 0.0, 0.2, 0.9),
        ("regra", 0.2, 0.6, 0.9),
        ("a", 0.6, 0.8, 0.9),  # repeti do começo
        ("regra", 0.8, 1.2, 0.9),
        ("é", 1.2, 1.3, 0.9),
        ("uma", 1.3, 1.6, 0.9),
        ("linha", 1.6, 2.0, 0.9),
        ("só", 2.0, 2.4, 0.9),
    )

    saida = a.casar(nossas, ouvidas, duracao=3.0)

    assert [p.palavra for p in saida] == nossas
    assert [p.inicio for p in saida[-4:]] == [1.2, 1.3, 1.6, 2.0]
    assert not any(p.estimada for p in saida[-4:])


def test_tempo_nunca_anda_pra_tras():
    saida = a.casar(
        ["um", "dois", "três", "quatro"],
        alinhadas(("um", 0.0, 1.0, 0.9), ("quatro", 4.0, 5.0, 0.9)),
        duracao=6.0,
    )

    tempos = [t for p in saida for t in (p.inicio, p.fim)]
    assert tempos == sorted(tempos)
