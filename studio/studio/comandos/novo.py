"""studio novo NN-slug — cria a pasta do vídeo a partir do template."""

from __future__ import annotations

from studio.projeto import ErroDeUso, Projeto, pasta_templates, pasta_videos, validar_nome


def _titulo(slug: str) -> str:
    return slug.replace("-", " ").capitalize()


def novo(nome: str) -> int:
    numero, slug = validar_nome(nome)

    raiz = pasta_videos() / nome
    if raiz.exists():
        raise ErroDeUso(f"{raiz.relative_to(pasta_videos().parent)} já existe")

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

    print(f"criado videos/{nome}/")
    for caminho in (projeto.script, projeto.assets, projeto.thumb_vars, projeto.build):
        marca = "  (descartável)" if caminho == projeto.build else ""
        print(f"  {caminho.relative_to(raiz)}{marca}")
    print(f"\npróximo:  escrever o roteiro, depois  studio narracao {numero}")
    return 0
