"""studio novo NN-slug — cria a pasta do vídeo a partir do template."""

from __future__ import annotations

from studio.projeto import (
    ErroDeUso,
    Projeto,
    listar,
    pasta_templates,
    pasta_videos,
    validar_nome,
)


def _titulo(slug: str) -> str:
    return slug.replace("-", " ").capitalize()


def criar(nome: str) -> Projeto:
    """Cria a pasta e devolve o projeto. Sem imprimir — a UI cria por aqui também."""
    numero, slug = validar_nome(nome)

    raiz = pasta_videos() / nome
    if raiz.exists():
        raise ErroDeUso(f"{raiz.relative_to(pasta_videos().parent)} já existe")

    # O número é a chave de todo comando. Dois vídeos com o mesmo `01` não quebram na
    # criação: quebram depois, no `resolver`, e derrubam junto o vídeo que já existia.
    if repetido := next((p for p in listar() if p.numero == numero), None):
        raise ErroDeUso(
            f"o número {numero} já é do {repetido.nome} — "
            f"dois vídeos com o mesmo número quebram todo comando dos dois"
        )

    templates = pasta_templates()
    modelo = (templates / "script.md").read_text(encoding="utf-8")
    thumb = (templates / "thumb.vars.json").read_text(encoding="utf-8")

    projeto = Projeto(raiz)
    projeto.assets.mkdir(parents=True)
    projeto.garantir_build()
    projeto.script.write_text(
        modelo.replace("{{TITULO}}", _titulo(slug)).replace("{{NUMERO}}", numero),
        encoding="utf-8",
    )
    projeto.thumb_vars.write_text(thumb, encoding="utf-8")
    return projeto


def novo(nome: str) -> int:
    projeto = criar(nome)
    raiz, numero = projeto.raiz, projeto.numero

    print(f"criado videos/{nome}/")
    for caminho in (projeto.script, projeto.assets, projeto.thumb_vars, projeto.build):
        marca = "  (descartável)" if caminho == projeto.build else ""
        print(f"  {caminho.relative_to(raiz)}{marca}")
    print(f"\npróximo:  escrever o roteiro, depois  studio narracao {numero}")
    return 0
