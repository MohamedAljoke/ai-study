"""studio ui [NN] — a interface local do pipeline.

O comando é casca fina: sobe o servidor e sai da frente. Todo o resto continua igual —
a página roda `studio narracao 01` por subprocesso, exatamente como eu rodaria no
terminal, e escreve nos mesmos arquivos.

É aqui que mora o import tardio do extra `ui` (§9): `studio --help` não pode depender do
FastAPI estar instalado.
"""

from __future__ import annotations

import webbrowser

from studio.projeto import ErroDeUso, resolver

PORTA = 8730
ENDERECO = "127.0.0.1"
"""Só localhost. É ferramenta minha, na minha máquina: não tem login e não deve ter."""

INSTALAR = "uv sync --extra ui"


def _carregar():
    try:
        import uvicorn

        from studio.ui.servidor import criar_app
    except ImportError as erro:
        raise ErroDeUso(
            f"a interface precisa do FastAPI e do uvicorn — instale com:  {INSTALAR}"
        ) from erro
    return uvicorn, criar_app


def ui(numero: str | None = None, porta: int = PORTA, sem_navegador: bool = False) -> int:
    uvicorn, criar_app = _carregar()

    endereco = f"http://{ENDERECO}:{porta}"
    if numero:
        endereco += f"#{resolver(numero).numero}"  # erra agora se eu digitei o vídeo errado

    print(f"studio ui → {endereco}")
    print("  o roteiro, o áudio e os assets numa página só; ctrl-c pra parar")

    if not sem_navegador:
        webbrowser.open(endereco)

    uvicorn.run(criar_app(), host=ENDERECO, port=porta, log_level="warning")
    return 0
