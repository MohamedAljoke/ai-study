"""As rotas. Finas de propósito: cada uma pergunta ao `estado` ou às `tarefas` e serializa.

Regra que vale pra este arquivo inteiro: **se uma rota precisar decidir alguma coisa sobre
o pipeline, a decisão está no lugar errado** — ela mora em `comandos/`, e aqui só passa.

Este é o único arquivo do projeto que sabe que o FastAPI existe (§9), e por isso é o único
que importa ele no topo — quem carrega este módulo é `comandos/ui.py`, com import tardio e
`ErroDeUso` trazendo o comando de instalação. Sem `from __future__ import annotations`
de propósito: o FastAPI resolve os tipos dos parâmetros em tempo de execução, e com
anotação adiada ele não acha `UploadFile`.
"""

import json
from pathlib import Path
from typing import Annotated

from fastapi import Body, FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse

from studio.projeto import ErroDeUso, Projeto, resolver
from studio.ui import estado, tarefas

PASTA = Path(__file__).parent
TIPOS = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}

SEM_CACHE = {"cache-control": "no-store"}
"""A página é lida do disco a cada pedido: editar o CSS e dar F5 tem que bastar."""


def _pagina(nome: str) -> Response:
    arquivo = PASTA / nome
    return Response(
        arquivo.read_text(encoding="utf-8"),
        media_type=TIPOS[arquivo.suffix],
        headers=SEM_CACHE,
    )


# --- escrita em disco, com as guardas ---


def _limpar_asset(projeto: Projeto, id: str) -> None:
    """Some com a versão anterior: duas extensões pro mesmo id é `ErroDeUso` no `asset_de`."""
    if not projeto.assets.is_dir():
        return
    for antigo in projeto.assets.glob(f"{id}.*"):
        if antigo.is_file():
            antigo.unlink()


def _guardar_asset(projeto: Projeto, id: str, nome: str, dados: bytes) -> str:
    """Grava `assets/<id>.<ext>`. O `id` vem da timeline, nunca da string do cliente."""
    if id not in {c["id"] for c in estado.cenas(projeto)}:
        raise ErroDeUso(f"'{id}' não é uma cena deste vídeo — refaça a timeline")

    extensao = Path(nome).suffix.lstrip(".").lower()
    if extensao not in estado.EXTENSOES:
        raise ErroDeUso(
            f"não sei o que fazer com '{nome}' — use um destes: {', '.join(estado.EXTENSOES)}"
        )

    projeto.assets.mkdir(parents=True, exist_ok=True)
    _limpar_asset(projeto, id)
    destino = projeto.assets / f"{id}.{extensao}"
    destino.write_bytes(dados)
    return destino.name


def _guardar_script(projeto: Projeto, texto: str, assinatura: str) -> None:
    """Recusa sobrescrever edição que aconteceu fora da página, no espírito do §5."""
    atual = estado.assinatura(projeto)
    if atual and assinatura and atual != assinatura:
        raise ErroDeUso(
            "o script.md mudou no disco depois que a página carregou — "
            "recarregue antes de salvar, pra não perder a outra edição"
        )
    projeto.script.write_text(texto, encoding="utf-8")


def _midia(projeto: Projeto, tipo: str, nome: str) -> Path:
    if tipo == "audio":
        return projeto.audio()[0]
    if tipo == "video":
        return projeto.video
    if tipo == "rascunho":
        return projeto.video_de("rascunho")
    if tipo == "assets":
        caminho = projeto.assets / Path(nome).name  # `.name` corta qualquer subida de pasta
        if caminho.is_file():
            return caminho
    raise ErroDeUso(f"não tenho {tipo}/{nome} do vídeo {projeto.numero}")


def criar_app() -> FastAPI:
    app = FastAPI(title="studio", docs_url=None, redoc_url=None)

    @app.exception_handler(ErroDeUso)
    async def _erro_previsto(_: Request, erro: ErroDeUso) -> JSONResponse:
        """Erro previsto vira 400 com a mensagem inteira — elas trazem o conserto (§9)."""
        return JSONResponse({"erro": str(erro)}, status_code=400)

    # --- a página ---

    @app.get("/")
    def raiz() -> Response:
        return _pagina("pagina.html")

    @app.get("/pagina.js")
    def script_da_pagina() -> Response:
        return _pagina("pagina.js")

    @app.get("/pagina.css")
    def estilo() -> Response:
        folha = estado.marca_css() + (PASTA / "pagina.css").read_text(encoding="utf-8")
        return Response(folha, media_type="text/css", headers=SEM_CACHE)

    # --- estado ---

    @app.get("/api/videos")
    def videos() -> list[dict]:
        return estado.videos()

    @app.get("/api/videos/{numero}")
    def video(numero: str) -> dict:
        return estado.de_projeto(resolver(numero))

    @app.put("/api/videos/{numero}/script")
    def salvar_script(numero: str, corpo: Annotated[dict, Body()]) -> dict:
        projeto = resolver(numero)
        _guardar_script(projeto, corpo.get("texto", ""), corpo.get("assinatura", ""))
        return estado.script(projeto)

    # --- os arquivos que eu largo ---

    @app.post("/api/videos/{numero}/audio")
    async def subir_audio(numero: str, arquivo: Annotated[UploadFile, File()]) -> dict:
        projeto = resolver(numero)
        if Path(arquivo.filename or "").suffix.lower() != ".wav":
            raise ErroDeUso("a narração tem que ser .wav — é o que o alinhador lê")
        projeto.wav.write_bytes(await arquivo.read())
        return estado.midia(projeto)

    @app.post("/api/videos/{numero}/assets/{id}")
    async def subir_asset(numero: str, id: str, arquivo: Annotated[UploadFile, File()]) -> dict:
        projeto = resolver(numero)
        nome = _guardar_asset(projeto, id, arquivo.filename or "", await arquivo.read())
        return {"arquivo": nome, "cenas": estado.cenas(projeto)}

    @app.delete("/api/videos/{numero}/assets/{id}")
    def apagar_asset(numero: str, id: str) -> dict:
        projeto = resolver(numero)
        _limpar_asset(projeto, id)
        return {"cenas": estado.cenas(projeto)}

    @app.get("/midia/{numero}/{tipo}")
    @app.get("/midia/{numero}/{tipo}/{nome}")
    def midia(numero: str, tipo: str, nome: str = "") -> FileResponse:
        return FileResponse(_midia(resolver(numero), tipo, nome), headers=SEM_CACHE)

    # --- etapas rodando ---

    @app.post("/api/tarefas")
    def rodar_etapa(corpo: Annotated[dict, Body()]) -> dict:
        tarefa = tarefas.iniciar(
            corpo.get("comando", ""), corpo.get("numero", ""), corpo.get("flags", [])
        )
        return tarefa.json()

    @app.get("/api/tarefas/{id}")
    def uma_tarefa(id: str) -> dict:
        return tarefas.obter(id).json()

    @app.get("/api/tarefas/{id}/log")
    def log(id: str) -> StreamingResponse:
        tarefas.obter(id)  # erra agora, não no meio do stream

        def eventos():
            for linha in tarefas.acompanhar(id):
                yield f"data: {json.dumps({'linha': linha})}\n\n"
            yield f"data: {json.dumps({'fim': tarefas.obter(id).codigo})}\n\n"

        return StreamingResponse(eventos(), media_type="text/event-stream", headers=SEM_CACHE)

    return app
