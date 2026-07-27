from pathlib import Path

import pytest

from studio import leitura, roteiro, texto
from studio.projeto import ErroDeUso

ORIGEM = Path("script.md")


def ler(fonte: str) -> roteiro.Roteiro:
    return leitura.interpretar(fonte, origem=ORIGEM)


def erro_de(fonte: str) -> str:
    with pytest.raises(ErroDeUso) as capturado:
        ler(fonte)
    return str(capturado.value)


def test_so_linha_de_citacao_vira_narracao():
    r = ler(
        """# Título

## Bloco 1

**Tela:** isso aqui é anotação minha.

> Isso eu falo.
"""
    )
    assert r.narracao().strip() == "Isso eu falo."
    assert r.total_palavras == 3
    assert r.titulo == "Título"


def test_cerca_de_codigo_com_citacao_dentro_e_ignorada():
    r = ler(
        """> Antes.

```go
// > isto é código, não narração
fmt.Println("> nem isto")
```

> Depois.
"""
    )
    assert r.narracao().split("\n\n") == ["Antes.", "Depois.\n"]


def test_negrito_atravessa_quebra_de_linha():
    r = ler("> Um teste que quebra quando o texto muda **não está testando a\n> regra**.\n")
    assert "**" not in r.narracao()
    assert r.narracao().strip().endswith("não está testando a regra.")


def test_linha_vazia_de_citacao_separa_paragrafo():
    r = ler("> Um.\n>\n> Dois.\n")
    assert [f.texto for f in r.falas] == ["Um.", "Dois."]


def test_marcador_aponta_pra_primeira_palavra_da_narracao_seguinte():
    fonte = """> Uma duas três.

<!-- cena: tela id=demo -->
> Quatro cinco.
"""
    r = ler(fonte)
    cena = r.cenas[0]
    assert cena.palavra_inicio == 3
    assert cena.palavra_fim == 5
    assert texto.palavras(r.narracao())[cena.palavra_inicio] == "Quatro"


def test_cena_termina_onde_a_proxima_comeca():
    r = ler(
        """<!-- cena: tela id=a -->
> Uma duas.

<!-- cena: tela id=b -->
> Três quatro cinco.
"""
    )
    a, b = r.cenas
    assert (a.palavra_inicio, a.palavra_fim) == (0, 2)
    assert (b.palavra_inicio, b.palavra_fim) == (2, 5)


def test_short_e_eixo_independente_e_pode_atravessar_cena():
    r = ler(
        """<!-- cena: tela id=a -->
> Uma duas.

<!-- short: inicio id=corte titulo="Um corte" -->
> Três quatro.

<!-- cena: tela id=b -->
> Cinco seis.
<!-- short: fim id=corte -->
"""
    )
    short = r.shorts[0]
    assert (short.palavra_inicio, short.palavra_fim) == (2, 6)
    assert short.titulo == "Um corte"
    assert [c.id for c in r.cenas] == ["a", "b"]


def test_narracao_e_leitura_tem_as_mesmas_palavras_faladas():
    fonte = """# T

## Bloco

<!-- cena: tela id=demo -->
> Uma duas três.

> Quatro.
"""
    r = ler(fonte)
    falada = texto.palavras(r.narracao())
    lida = [p for p in texto.palavras(r.leitura()) if not p.startswith(("#", "<!--"))]
    assert falada == [p for p in lida if p in falada]
    assert r.narracao().count("#") == 0


def test_id_duplicado_aponta_a_linha():
    mensagem = erro_de(
        """<!-- cena: tela id=demo -->
> Uma.

<!-- cena: tela id=demo -->
> Duas.
"""
    )
    assert "script.md:4" in mensagem
    assert "já usado na linha 1" in mensagem


def test_short_sem_fecho():
    assert "nunca fechado" in erro_de('<!-- short: inicio id=x titulo="T" -->\n> Uma.\n')


def test_short_fechado_sem_abrir():
    assert "sem ter sido aberto" in erro_de("> Uma.\n<!-- short: fim id=x -->\n")


def test_marcador_sem_narracao_depois():
    assert "não tem narração depois" in erro_de("> Uma.\n\n<!-- cena: tela id=fim -->\n")


def test_tipo_de_cena_desconhecido():
    assert "desconhecido" in erro_de("<!-- cena: video id=x -->\n> Uma.\n")


def test_parametro_obrigatorio_faltando():
    assert "sem arquivo=" in erro_de("<!-- cena: codigo id=x -->\n> Uma.\n")


def test_parametro_desconhecido():
    assert "desconhecido" in erro_de("<!-- cena: tela id=x cor=azul -->\n> Uma.\n")


def test_id_fora_de_kebab_case():
    assert "kebab-case" in erro_de("<!-- cena: tela id=Demo_1 -->\n> Uma.\n")


def test_short_sem_titulo():
    assert "sem titulo=" in erro_de("<!-- short: inicio id=x -->\n> Uma.\n")


def test_avisa_digito_e_codigo_sem_quebrar():
    r = ler("> Fui de 95 para 44 mexendo em `main.go`.\n")
    tipos = {a.tipo for a in r.avisos}
    assert tipos == {"digito", "codigo"}


def test_marcador_indentado_e_codigo_nao_marcador():
    r = ler("Exemplo:\n\n    <!-- cena: tela id=exemplo -->\n\n> Uma.\n")
    assert r.cenas == []
