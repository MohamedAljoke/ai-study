"""A cartela navy com o id escrito em cima. O último recurso da montagem.

Só entra quando não há **nada** antes pra congelar — na prática, as cenas do começo do
vídeo enquanto eu ainda não produzi nada. É desenhada pelo ffmpeg, sem ferramenta
externa nenhuma: o studio não gera mídia (§3), e esta é a exceção mínima que impede o
vídeo de abrir em preto.

Não imprime e não sabe de projeto: recebe id, tipo e onde escrever.
"""

from __future__ import annotations

from pathlib import Path

from studio import ffmpeg, marca

TAMANHO_ID = 96
TAMANHO_TIPO = 36

TIPO_APAGADO = f"{marca.TEXTO}@0.45"
"""O tipo é contexto, não a informação. Cinza da paleta em cima do navy some."""


def desenhar(id: str, tipo: str, saida: Path) -> None:
    filtros = [
        ffmpeg.texto(id, "(h-text_h)/2-40", TAMANHO_ID, marca.TEXTO),
        ffmpeg.texto(tipo, "(h-text_h)/2+90", TAMANHO_TIPO, TIPO_APAGADO),
    ]
    ffmpeg.quadro(marca.FUNDO, filtros, saida, ffmpeg.FINAL, f"desenhar a cartela {id}")
