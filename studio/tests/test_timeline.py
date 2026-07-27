import pytest

from studio import timeline
from studio.alinhador import Palavra
from studio.artefatos import MarcadorCena, Marcadores, MarcadorShort
from studio.projeto import ErroDeUso

DURACAO = 10.0


def palavras(quantas: int = 10) -> list[Palavra]:
    """Uma palavra por segundo, falando por 0,8s e calando por 0,2s."""
    return [
        Palavra(indice=i, palavra=f"p{i}", inicio=float(i), fim=i + 0.8, score=0.9)
        for i in range(quantas)
    ]


def cena(id: str, inicio: int, fim: int, tipo: str = "tela", **params) -> MarcadorCena:
    return MarcadorCena(
        id=id, tipo=tipo, linha=1, palavra_inicio=inicio, palavra_fim=fim, params=params
    )


def short(id: str, inicio: int, fim: int) -> MarcadorShort:
    return MarcadorShort(
        id=id, titulo=f"T {id}", linha=1, palavra_inicio=inicio, palavra_fim=fim
    )


def montar(cenas=(), shorts=(), total=10, palavras_=None, duracao=DURACAO):
    marcadores = Marcadores(
        video="01-batalha-naval",
        titulo="Vídeo 01",
        palavras=total,
        cenas=list(cenas),
        shorts=list(shorts),
    )
    lista = palavras(total) if palavras_ is None else palavras_
    return timeline.montar(marcadores, lista, duracao, audio="narration.wav")


# --- a checagem que salva o pipeline inteiro ---


def test_contagem_divergente_manda_realinhar():
    """Índices dos dois arquivos com significados diferentes = timeline toda errada."""
    with pytest.raises(ErroDeUso, match="studio alinhar 01"):
        montar(total=12, palavras_=palavras(10))


def test_indice_alem_do_fim_da_lista_nao_estoura_cru():
    with pytest.raises(ErroDeUso, match=r"cena 'x' aponta pra palavra 99"):
        montar([cena("x", 99, 100)])


def test_indice_negativo_tambem_e_recusado():
    with pytest.raises(ErroDeUso, match="aponta pra palavra -1"):
        montar([cena("x", -1, 3)])


# --- posicionamento das cenas ---


def test_primeira_cena_comeca_no_segundo_zero():
    """Mesmo que a primeira palavra só soe em 0.18: senão o vídeo abre em preto."""
    lista = [Palavra(0, "Eu", 0.18, 0.4, 0.5), *palavras(10)[1:]]
    (unica,) = montar([cena("abertura", 0, 10)], palavras_=lista).cenas
    assert unica.inicio == 0.0


def test_cena_do_meio_comeca_na_palavra_dela():
    _, meio, _ = montar([cena("a", 0, 3), cena("b", 3, 7), cena("c", 7, 10)]).cenas
    assert meio.inicio == 3.0


def test_cena_termina_onde_a_proxima_comeca():
    """Vídeo contínuo: sem buraco e sem sobreposição entre cenas."""
    resultado = montar([cena("a", 0, 3), cena("b", 3, 7), cena("c", 7, 10)]).cenas
    assert [(c.inicio, c.fim) for c in resultado] == [
        (0.0, 3.0),
        (3.0, 7.0),
        (7.0, 10.0),
    ]


def test_ultima_cena_vai_ate_o_fim_do_audio():
    resultado = montar([cena("a", 0, 5), cena("b", 5, 10)], duracao=12.5).cenas
    assert resultado[-1].fim == 12.5


def test_cenas_saem_em_ordem_de_tempo_mesmo_vindo_fora_de_ordem():
    resultado = montar([cena("z", 7, 10), cena("a", 0, 7)]).cenas
    assert [c.id for c in resultado] == ["a", "z"]
    assert resultado[0].fim == resultado[1].inicio


def test_roteiro_sem_cena_nenhuma_nao_estoura():
    resultado = montar()
    assert resultado.cenas == []
    assert resultado.duracao == DURACAO


def test_duas_cenas_no_mesmo_ponto_ficam_com_duracao_zero():
    """Não é erro aqui — quem reclama é a conferência, com aviso e não com exceção."""
    resultado = montar([cena("a", 3, 3), cena("b", 3, 10)]).cenas
    assert resultado[0].duracao == 0.0


# --- tipo e intervalo de palavras ---


def test_intervalo_de_palavras_atravessa_pro_tempo():
    """A folha de pedidos recorta a fala da cena com estes dois índices."""
    (unica,) = montar([cena("grid", 0, 10)]).cenas
    assert (unica.palavra_inicio, unica.palavra_fim) == (0, 10)


def test_tipo_inventado_no_json_editado_a_mao():
    with pytest.raises(ErroDeUso, match="tipo 'holograma', que não existe"):
        montar([cena("x", 0, 10, tipo="holograma")])


def test_params_atravessam_intactos():
    (unica,) = montar([cena("parity", 0, 10, tipo="manim", classe="ShipOverlay")]).cenas
    assert unica.params == {"classe": "ShipOverlay"}


# --- shorts ---


def test_short_fecha_na_ultima_palavra_falada_mais_respiro():
    """Palavra 4 cala em 4.8; o short fecha em 5.05, não em 5.0 da palavra seguinte."""
    (unico,) = montar(shorts=[short("s", 1, 5)]).shorts
    assert unico.inicio == 1.0
    assert unico.fim == pytest.approx(4.8 + timeline.RESPIRO)


def test_short_no_fim_do_audio_nao_passa_da_duracao():
    (unico,) = montar(shorts=[short("s", 5, 10)], duracao=9.9).shorts
    assert unico.fim == 9.9


def test_short_comecando_na_palavra_zero():
    (unico,) = montar(shorts=[short("s", 0, 4)]).shorts
    assert unico.inicio == 0.0


def test_shorts_saem_em_ordem_de_tempo():
    resultado = montar(shorts=[short("b", 6, 9), short("a", 1, 4)]).shorts
    assert [s.id for s in resultado] == ["a", "b"]


def test_short_invertido_nao_gera_duracao_negativa():
    """Marcador fora de ordem: a conferência avisa, mas o JSON não sai corrompido."""
    (unico,) = montar(shorts=[short("s", 8, 2)]).shorts
    assert unico.duracao >= 0


# --- serialização ---


def test_json_da_timeline_tem_o_que_a_folha_de_pedidos_precisa():
    resultado = montar([cena("play", 0, 10, tipo="terminal", nota="com o bench rodando")])
    dados = resultado.json()

    assert dados["video"] == "01-batalha-naval"
    assert dados["audio"] == "narration.wav"
    assert dados["duracao"] == 10.0
    (cena_json,) = dados["cenas"]
    assert cena_json["tipo"] == "terminal"
    assert cena_json["palavra_fim"] == 10
    assert cena_json["params"]["nota"] == "com o bench rodando"


def test_json_dos_shorts_traz_duracao_e_origem():
    dados = montar(shorts=[short("s", 1, 5)]).json_shorts()
    (short_json,) = dados["shorts"]

    assert short_json["origem"] == "01-batalha-naval"
    assert short_json["duracao"] == pytest.approx(4.05)
    assert short_json["legenda"] == "queimada"
