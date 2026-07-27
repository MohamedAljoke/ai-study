from pathlib import Path

from studio.comandos.duble import WPM_DA_VOZ
from studio.projeto import Projeto


def projeto(tmp_path: Path) -> Projeto:
    p = Projeto(tmp_path / "01-teste")
    p.garantir_build()
    return p


def test_sem_audio_nenhum_aponta_pro_duble(tmp_path):
    p = projeto(tmp_path)
    caminho, eh_duble = p.audio()
    assert eh_duble
    assert caminho == p.duble


def test_duble_existindo_e_usado_e_marcado_como_duble(tmp_path):
    p = projeto(tmp_path)
    p.duble.write_bytes(b"fake")
    caminho, eh_duble = p.audio()
    assert (caminho, eh_duble) == (p.duble, True)


def test_minha_voz_ganha_do_duble(tmp_path):
    p = projeto(tmp_path)
    p.duble.write_bytes(b"fake")
    p.wav.write_bytes(b"real")
    caminho, eh_duble = p.audio()
    assert caminho == p.wav
    assert not eh_duble


def test_duble_mora_no_build_pra_ser_descartavel(tmp_path):
    p = projeto(tmp_path)
    assert p.duble.parent == p.build
    assert p.wav.parent == p.raiz


def test_escala_da_voz_freia_pro_ritmo_pedido():
    assert WPM_DA_VOZ / 150 > 1, "a voz é mais rápida que a leitura alvo, tem que frear"
