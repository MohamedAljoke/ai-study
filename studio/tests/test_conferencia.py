from studio import conferencia
from studio.timeline import CenaEmTempo, ShortEmTempo, Timeline


def cena(id="c", inicio=0.0, fim=30.0, tipo="terminal") -> CenaEmTempo:
    return CenaEmTempo(id=id, tipo=tipo, inicio=inicio, fim=fim)


def short(id="s", inicio=0.0, fim=30.0) -> ShortEmTempo:
    return ShortEmTempo(id=id, titulo="T", inicio=inicio, fim=fim)


def conferir(cenas=None, shorts=()) -> list[conferencia.Aviso]:
    cenas = [cena()] if cenas is None else cenas
    linha = Timeline(
        video="01-batalha-naval",
        audio="narration.wav",
        duracao=30.0,
        cenas=list(cenas),
        shorts=list(shorts),
    )
    return conferencia.conferir(linha)


def tipos(avisos) -> list[str]:
    return [a.tipo for a in avisos]


def test_timeline_saudavel_nao_gera_aviso():
    assert conferir(shorts=[short(fim=35.0)]) == []


def test_short_curto_manda_mexer_no_script():
    (aviso,) = conferir(shorts=[short(fim=12.0)])
    assert aviso.tipo == "short-curto"
    assert aviso.alvo == "s"
    assert "script.md" in aviso.texto


def test_short_longo():
    assert tipos(conferir(shorts=[short(fim=75.0)])) == ["short-longo"]


def test_short_no_limite_passa():
    """20s e 60s exatos são válidos: o aviso é pra fora do intervalo."""
    assert conferir(shorts=[short(fim=20.0), short(id="b", fim=60.0)]) == []


def test_cena_sem_duracao_e_marcador_no_mesmo_ponto():
    avisos = conferir([cena("a", 0.0, 0.0), cena("b", 0.0, 30.0)])
    assert tipos(avisos) == ["cena-invertida"]
    assert "mesmo ponto do texto" in avisos[0].texto


def test_cena_relampago():
    assert tipos(conferir([cena("a", 0.0, 2.0), cena("b", 2.0, 30.0)])) == ["cena-relampago"]


def test_card_parado_tempo_demais():
    assert tipos(conferir([cena("a", 0.0, 30.0, tipo="card")])) == ["estatica-longa"]


def test_terminal_longo_nao_reclama():
    """Só imagem estática cansa. Uma gravação de terminal de 30s é normal."""
    assert conferir([cena("a", 0.0, 30.0, tipo="terminal")]) == []


def test_abertura_sem_cena():
    (aviso,) = conferir([cena("a", 4.5, 30.0)])
    assert aviso.tipo == "abertura-vazia"
    assert "00:04.5" in aviso.texto


def test_roteiro_sem_cena_nenhuma():
    assert tipos(conferir(cenas=[])) == ["sem-cena"]


def test_varios_problemas_saem_todos():
    avisos = conferir([cena("a", 1.0, 2.0), cena("b", 2.0, 30.0)], [short(fim=5.0)])
    assert tipos(avisos) == ["abertura-vazia", "cena-relampago", "short-curto"]
