"""studio duble NN — voz sintética temporária, pra destravar o pipeline sem a minha.

O dublê existe pra eu poder escrever e testar os sprints 2 a 5 antes de gravar. Ele
tem as mesmas palavras na mesma ordem do narration.txt, que é tudo que o alinhador
precisa. Ele nunca vira vídeo publicado: mora em build/, tem nome próprio e todo
comando que usar ele avisa.
"""

from __future__ import annotations

import os
import subprocess
import sys
import wave
from pathlib import Path

from studio import cache
from studio import texto as t
from studio.projeto import ErroDeUso, resolver

FERRAMENTA = "duble/" + cache.versao_de(sys.modules[__name__])

VOZ = "pt_BR-faber-medium"
WPM_DA_VOZ = 219  # medido no roteiro inteiro; amostra curta mente por causa do silêncio
TAXA = 48000

INSTALAR = "uv sync --extra duble"


def em_dia(projeto, wpm: int = t.PALAVRAS_POR_MINUTO) -> bool:
    params = {"voz": VOZ, "wpm": wpm}
    return not cache.precisa_refazer(
        projeto.duble, [projeto.narracao_txt], params, FERRAMENTA
    )


def _pasta_vozes() -> Path:
    raiz = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser()
    return raiz / "studio" / "vozes"


def _carregar_voz(length_scale: float):
    try:
        from piper import PiperVoice, SynthesisConfig
        from piper.download_voices import download_voice
    except ImportError as erro:
        raise ErroDeUso(f"piper não instalado — rode: {INSTALAR}") from erro

    pasta = _pasta_vozes()
    modelo = pasta / f"{VOZ}.onnx"
    if not modelo.is_file():
        print(f"baixando a voz {VOZ} (uma vez, ~63 MB)...")
        pasta.mkdir(parents=True, exist_ok=True)
        download_voice(VOZ, pasta)

    return PiperVoice.load(modelo), SynthesisConfig(length_scale=length_scale)


def _sintetizar(texto: str, saida: Path, length_scale: float) -> None:
    voz, config = _carregar_voz(length_scale)
    bruto = saida.with_suffix(".bruto.wav")

    with wave.open(str(bruto), "wb") as arquivo:
        voz.synthesize_wav(texto, arquivo, syn_config=config)

    _converter(bruto, saida)
    bruto.unlink()


def _converter(entrada: Path, saida: Path) -> None:
    """Mono 48k, o mesmo formato que eu vou entregar gravando de verdade."""
    comando = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(entrada),
        "-ac", "1", "-ar", str(TAXA),
        str(saida),
    ]  # fmt: skip
    try:
        subprocess.run(comando, check=True)
    except FileNotFoundError as erro:
        raise ErroDeUso("ffmpeg não encontrado — instale pra converter o áudio") from erro
    except subprocess.CalledProcessError as erro:
        raise ErroDeUso(f"ffmpeg falhou ao converter o dublê ({erro.returncode})") from erro


def _duracao(wav: Path) -> float:
    with wave.open(str(wav), "rb") as arquivo:
        return arquivo.getnframes() / arquivo.getframerate()


def duble(numero: str, wpm: int = t.PALAVRAS_POR_MINUTO) -> int:
    projeto = resolver(numero)

    if not projeto.narracao_txt.is_file():
        raise ErroDeUso(f"falta o narration.txt — rode antes: studio narracao {projeto.numero}")

    if projeto.wav.is_file():
        print(f"{projeto.wav.name} já existe — o dublê não é usado quando tem a minha voz")

    texto = projeto.narracao_txt.read_text(encoding="utf-8")
    palavras = len(t.palavras(texto))
    length_scale = WPM_DA_VOZ / wpm
    params = {"voz": VOZ, "wpm": wpm}

    projeto.garantir_build()
    if cache.precisa_refazer(projeto.duble, [projeto.narracao_txt], params, FERRAMENTA):
        print(f"sintetizando {t.formatar_numero(palavras)} palavras com {VOZ}...")
        _sintetizar(texto, projeto.duble, length_scale)
        cache.registrar(projeto.duble, [projeto.narracao_txt], params, FERRAMENTA)
    else:
        print("(sem mudança no narration.txt — dublê já estava em dia)")

    real = _duracao(projeto.duble)
    estimado = t.estimar_duracao(palavras, wpm)
    print(
        f"build/{projeto.duble.name} — {t.formatar_duracao(real)} "
        f"(estimativa era {t.formatar_duracao(estimado)})"
    )
    print("\n⚠ voz sintética, só pra destravar o código. O vídeo final precisa da minha.")
    return 0
