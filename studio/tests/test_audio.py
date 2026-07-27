from pathlib import Path

from studio import audio
from studio.audio import Audio

WAV = Path("narration.wav")


def som(duracao: float = 428.0, canais: int = audio.CANAIS, taxa: int = audio.TAXA) -> Audio:
    return Audio(caminho=WAV, duracao=duracao, canais=canais, taxa=taxa)


def test_audio_se_descreve_pra_linha_de_comando():
    assert str(som(441.3)) == "7min21 (441.3s), mono 48k"
    assert str(som(441.3, canais=2)) == "7min21 (441.3s), estéreo 48k"


def test_audio_no_formato_certo_nao_gera_aviso():
    assert audio.conferir(som(), audio.LUFS_ALVO, palavras=1069) == []


def test_estereo_e_taxa_errada_sugerem_o_ffmpeg():
    avisos = audio.conferir(som(canais=2, taxa=44100), audio.LUFS_ALVO, palavras=1069)
    assert len(avisos) == 2
    assert all("-ac 1 -ar 48000" in aviso for aviso in avisos)


def test_volume_longe_do_alvo_vira_aviso():
    (aviso,) = audio.conferir(som(), lufs=-23.0, palavras=1069)
    assert "-23.0 LUFS" in aviso and "loudnorm" in aviso


def test_volume_dentro_da_tolerancia_passa():
    assert audio.conferir(som(), lufs=audio.LUFS_ALVO + 1.0, palavras=1069) == []


def test_sem_medida_de_volume_nao_inventa_aviso():
    assert audio.conferir(som(), lufs=None, palavras=1069) == []


def test_duracao_incompativel_com_o_texto_avisa_versao_diferente():
    """O risco real: alinhar o wav de ontem com o texto de hoje."""
    (aviso,) = audio.conferir(som(duracao=60.0), audio.LUFS_ALVO, palavras=1069)
    assert "versões" in aviso


def test_texto_vazio_nao_divide_por_zero():
    assert audio.conferir(som(), audio.LUFS_ALVO, palavras=0) == []
