from pathlib import Path

import pytest

from studio import montagem, pedidos
from studio.ffmpeg import FINAL, RASCUNHO
from studio.timeline import CenaEmTempo


def cena(id, inicio, fim, tipo="manim") -> CenaEmTempo:
    return CenaEmTempo(id=id, tipo=tipo, inicio=inicio, fim=fim)


def asset(raiz: Path, id: str, extensao: str = "mp4") -> Path:
    caminho = raiz / "assets" / f"{id}.{extensao}"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(b"")
    return caminho


def planejar(tmp_path, cenas, achados=None, perfil=FINAL) -> montagem.Plano:
    """Por padrão toda cena tem asset — quem testa o congelamento passa `achados`."""
    if achados is None:
        achados = {c.id: asset(tmp_path, c.id) for c in cenas}
    lista = pedidos.resolver(list(cenas), achados)
    substitutos = {p.id: tmp_path / "build/substitutos" / f"{p.id}.png" for p in lista}
    return montagem.planejar(lista, substitutos, tmp_path / "n.wav", perfil)


def test_soma_dos_segmentos_bate_com_a_duracao_do_audio(tmp_path):
    # é isto que impede o vídeo de derivar do áudio: o áudio nunca é cortado
    cenas = [cena("a", 0.0, 40.583), cena("b", 40.583, 145.013), cena("c", 145.013, 421.837)]
    plano = planejar(tmp_path, cenas)
    assert plano.duracao == pytest.approx(421.837, abs=1 / FINAL.fps)


def test_arredondamento_nao_acumula_entre_as_cenas(tmp_path):
    # cada cena arredondando por conta própria empurraria a última pra frente;
    # a conta é feita na borda acumulada justamente pra isso não acontecer
    cenas = [cena(f"c{i}", i * 1.017, (i + 1) * 1.017) for i in range(60)]
    plano = planejar(tmp_path, cenas)
    assert plano.duracao == pytest.approx(60 * 1.017, abs=1 / FINAL.fps)


def test_cada_segmento_dura_um_numero_inteiro_de_frames(tmp_path):
    plano = planejar(tmp_path, [cena("a", 0.0, 10.017), cena("b", 10.017, 20.04)])
    for segmento in plano.segmentos:
        assert (segmento.duracao * FINAL.fps) == round(segmento.duracao * FINAL.fps)


def test_cena_de_duracao_zero_ainda_rende_um_frame(tmp_path):
    # dois marcadores na mesma palavra: a conferência avisa, mas o ffmpeg não pode receber -t 0
    plano = planejar(tmp_path, [cena("a", 0.0, 0.0), cena("b", 0.0, 5.0)])
    assert plano.segmentos[0].duracao > 0


def test_png_vira_imagem_parada_e_mp4_nao(tmp_path):
    cenas = [cena("a", 0.0, 5.0), cena("b", 5.0, 10.0)]
    achados = {"a": asset(tmp_path, "a", "png"), "b": asset(tmp_path, "b", "mp4")}
    plano = planejar(tmp_path, cenas, achados)
    assert [s.parado for s in plano.segmentos] == [True, False]


def test_extensao_em_maiuscula_ainda_e_imagem(tmp_path):
    plano = planejar(tmp_path, [cena("a", 0.0, 5.0)], {"a": asset(tmp_path, "a", "PNG")})
    assert plano.segmentos[0].parado


def test_timeline_sem_cena_nenhuma_nao_estoura(tmp_path):
    plano = planejar(tmp_path, [])
    assert plano.segmentos == []
    assert plano.duracao == 0


def test_a_ordem_dos_segmentos_e_a_ordem_da_timeline(tmp_path):
    cenas = [cena("a", 0.0, 5.0), cena("b", 5.0, 9.0), cena("c", 9.0, 12.0)]
    plano = planejar(tmp_path, cenas)
    assert [s.id for s in plano.segmentos] == ["a", "b", "c"]


def test_rascunho_e_final_planejam_a_mesma_duracao(tmp_path):
    # trocar de qualidade não pode mexer na sincronia, só no tamanho do arquivo
    cenas = [cena("a", 0.0, 40.583), cena("b", 40.583, 145.013)]
    final = planejar(tmp_path, cenas).duracao
    assert final == planejar(tmp_path, cenas, perfil=RASCUNHO).duracao


def test_entrada_do_segmento_e_o_asset_que_eu_larguei(tmp_path):
    plano = planejar(tmp_path, [cena("a", 0.0, 5.0)])
    assert plano.segmentos[0].entrada == tmp_path / "assets/a.mp4"
    assert Path(plano.segmentos[0].entrada).is_absolute()


# --- cena que ainda não existe ---


def test_cena_sem_asset_entra_com_o_substituto_e_no_tempo_certo(tmp_path):
    cenas = [cena("a", 0.0, 5.0), cena("b", 5.0, 9.0)]
    plano = planejar(tmp_path, cenas, {"a": asset(tmp_path, "a")})
    congelado = plano.segmentos[1]

    assert congelado.entrada == tmp_path / "build/substitutos/b.png"
    assert congelado.parado
    assert congelado.duracao == pytest.approx(4.0)


def test_cena_congelada_lembra_de_quem_herdou(tmp_path):
    cenas = [cena("a", 0.0, 5.0), cena("b", 5.0, 9.0)]
    plano = planejar(tmp_path, cenas, {"a": asset(tmp_path, "a")})
    assert [s.id for s in plano.faltando] == ["b"]
    assert plano.segmentos[1].congela == "a"


def test_substituto_faltando_e_erro_de_programa_e_nao_video_torto(tmp_path):
    # se o comando esquecer de desenhar um substituto, o plano tem que estourar aqui e
    # não render um vídeo com uma cena a menos
    lista = pedidos.resolver([cena("a", 0.0, 5.0)], {})
    with pytest.raises(KeyError, match="'a'"):
        montagem.planejar(lista, {}, tmp_path / "n.wav", FINAL)


def test_video_todo_de_substituto_ainda_dura_o_audio_inteiro(tmp_path):
    cenas = [cena("a", 0.0, 40.583), cena("b", 40.583, 145.013)]
    plano = planejar(tmp_path, cenas, {})
    assert plano.duracao == pytest.approx(145.013, abs=1 / FINAL.fps)
    assert len(plano.faltando) == 2


# --- o acordo com o comando ---


def test_o_video_depende_dos_segmentos_e_nao_dos_assets(tmp_path):
    # bug real: `em_dia` olhava os assets e `_emendar` registrava os segmentos, então o
    # status dizia "desatualizado" e o montar dizia "já estava em dia" ao mesmo tempo
    from studio.comandos import montar as comando
    from studio.projeto import Projeto

    plano = planejar(tmp_path, [cena("a", 0.0, 5.0), cena("b", 5.0, 9.0)])
    projeto = Projeto(tmp_path)
    entradas = comando.entradas_do_video(projeto, plano)

    assert entradas[:-1] == [projeto.segmento("final", "a"), projeto.segmento("final", "b")]
    assert entradas[-1] == plano.audio
    assert not any("assets" in str(e) for e in entradas)


def test_rascunho_e_final_nao_dividem_o_mesmo_segmento(tmp_path):
    # têm resolução diferente; se dividissem o cache, um sobrescreveria o outro em silêncio
    from studio.comandos import montar as comando
    from studio.projeto import Projeto

    projeto = Projeto(tmp_path)
    final = comando.caminhos_dos_segmentos(projeto, planejar(tmp_path, [cena("a", 0.0, 5.0)]))
    rascunho = comando.caminhos_dos_segmentos(
        projeto, planejar(tmp_path, [cena("a", 0.0, 5.0)], perfil=RASCUNHO)
    )
    assert final != rascunho
