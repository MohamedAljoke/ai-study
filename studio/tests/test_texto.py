from studio import texto as t


def test_limpar_tira_markdown_e_preserva_pontuacao():
    assert t.limpar("> A regra é **uma** linha: `theirs.Fire(p)`.") == (
        "A regra é uma linha: theirs.Fire(p)."
    )


def test_limpar_tira_marcador_de_lista():
    assert t.limpar("> 1. Comece com o quadrado.") == "Comece com o quadrado."
    assert t.limpar("> - Um item") == "Um item"


def test_limpar_preserva_acento_e_travessao():
    assert t.limpar("> Bora — e o começo é burro.") == "Bora — e o começo é burro."


def test_limpar_resolve_link():
    assert t.limpar("> Está no [repositório](https://x.dev).") == "Está no repositório."


def test_palavra_e_a_unidade():
    assert t.palavras("A última versão faz em 44.") == [
        "A",
        "última",
        "versão",
        "faz",
        "em",
        "44.",
    ]


def test_duracao_por_ritmo_de_leitura():
    assert t.estimar_duracao(150, wpm=150) == 60
    assert t.formatar_duracao(427) == "7min07"
    assert t.formatar_duracao(44.4) == "44s"
