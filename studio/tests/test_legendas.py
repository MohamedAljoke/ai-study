from studio import legendas
from studio.alinhador import Palavra


def falar(frase: str, passo: float = 0.4) -> list[Palavra]:
    """Uma palavra por `passo` segundos, na ordem em que aparecem."""
    return [
        Palavra(i, palavra, round(i * passo, 3), round((i + 1) * passo, 3), 0.9)
        for i, palavra in enumerate(frase.split())
    ]


def texto_das_linhas(palavras) -> list[str]:
    return [" ".join(p.palavra for p in linha) for linha in legendas.agrupar(palavras)]


def test_quebra_no_fim_da_frase():
    linhas = texto_das_linhas(falar("A regra é uma. Bora."))
    assert linhas == ["A regra é uma.", "Bora."]


def test_ponto_final_dentro_de_aspas_tambem_fecha():
    linhas = texto_das_linhas(falar('Ele disse "não." E foi.'))
    assert linhas == ['Ele disse "não."', "E foi."]


def test_abreviacao_no_meio_nao_e_tratada_como_fim_de_frase():
    """Conhecido: quebra em '44.' porque a regra é pontuação, não gramática."""
    linhas = texto_das_linhas(falar("faz em 44. jogadas"))
    assert linhas == ["faz em 44.", "jogadas"]


def test_linha_nao_passa_da_largura_alvo():
    palavras = falar(" ".join(["palavra"] * 20))
    for linha in texto_das_linhas(palavras):
        assert len(linha) <= legendas.LARGURA


def test_linha_nao_passa_da_duracao_maxima():
    palavras = falar(" ".join(["a"] * 40), passo=1.0)
    for linha in legendas.agrupar(palavras):
        assert linha[-1].fim - linha[0].inicio <= legendas.DURACAO_MAXIMA


def test_nenhuma_palavra_se_perde_no_agrupamento():
    palavras = falar("A regra é uma linha só. Depois disso, o resto é detalhe. Bora.")
    agrupadas = [p for linha in legendas.agrupar(palavras) for p in linha]
    assert [p.indice for p in agrupadas] == [p.indice for p in palavras]


def test_srt_numera_e_usa_virgula_no_milesimo():
    saida = legendas.srt(falar("Bora. Vamos.", passo=1.5))
    assert saida == (
        "1\n00:00:00,000 --> 00:00:01,500\nBora.\n"
        "\n"
        "2\n00:00:01,500 --> 00:00:03,000\nVamos.\n"
    )


def test_vtt_tem_cabecalho_e_ponto_no_milesimo():
    saida = legendas.vtt(falar("Bora.", passo=1.5))
    assert saida == "WEBVTT\n\n00:00:00.000 --> 00:00:01.500\nBora.\n"


def test_relogio_passa_de_uma_hora():
    palavras = [Palavra(0, "fim", 3725.25, 3726.0, 0.9)]
    assert "01:02:05,250 --> 01:02:06,000" in legendas.srt(palavras)


def test_sem_palavra_nenhuma_nao_quebra():
    assert legendas.srt([]) == ""
    assert legendas.vtt([]) == "WEBVTT\n\n"
