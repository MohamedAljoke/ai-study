"""studio alinhar NN — áudio + narration.txt → tempo de cada palavra e legendas."""

from __future__ import annotations

import json

from studio import alinhador, artefatos, audio, cache, legendas
from studio import texto as t
from studio.alinhador import IDIOMA, Palavra
from studio.projeto import ErroDeUso, resolver

FERRAMENTA = "alinhar/" + cache.versao_do_comando(__name__, alinhador, artefatos, legendas, t)

CONFIANCA_BAIXA = 0.5
PIORES = 8


def saidas(projeto) -> tuple:
    return (projeto.palavras, projeto.narracao_srt, projeto.narracao_vtt)


def _entradas(projeto) -> list:
    som, _ = projeto.audio()
    return [projeto.narracao_txt, som]


def em_dia(projeto, idioma: str = IDIOMA) -> bool:
    """Quem gera é quem sabe se está velho. O status pergunta em vez de chutar mtime."""
    som, _ = projeto.audio()
    if not (som.is_file() and projeto.narracao_txt.is_file()):
        return False
    return all(
        not cache.precisa_refazer(saida, _entradas(projeto), {"idioma": idioma}, FERRAMENTA)
        for saida in saidas(projeto)
    )


def _relogio(segundos: float) -> str:
    return f"{int(segundos) // 60:02d}:{int(segundos) % 60:02d}"


def _json(projeto, palavras: list[Palavra], som, eh_duble: bool) -> str:
    alinhadas = [p for p in palavras if not p.estimada]
    media = sum(p.score for p in alinhadas) / len(alinhadas) if alinhadas else 0.0
    dados = {
        "video": projeto.nome,
        "audio": str(som.caminho.relative_to(projeto.raiz)),
        "duble": eh_duble,
        "duracao": round(som.duracao, 3),
        "palavras": len(palavras),
        "estimadas": len(palavras) - len(alinhadas),
        "confianca_media": round(media, 3),
        "lista": [
            {
                "indice": p.indice,
                "palavra": p.palavra,
                "inicio": p.inicio,
                "fim": p.fim,
                "score": p.score,
            }
            for p in palavras
        ],
    }
    return json.dumps(dados, indent=2, ensure_ascii=False) + "\n"


def _relatorio(palavras: list[Palavra]) -> None:
    total = len(palavras)
    alinhadas = [p for p in palavras if not p.estimada]
    media = sum(p.score for p in alinhadas) / len(alinhadas) if alinhadas else 0.0
    print(
        f"{t.formatar_numero(len(alinhadas))}/{t.formatar_numero(total)} alinhadas, "
        f"confiança média {media:.2f}"
    )

    if faltando := [p for p in palavras if p.estimada]:
        print(
            f"{t.formatar_numero(len(faltando))} sem tempo próprio, interpoladas entre as "
            f"vizinhas — o alinhador não reconheceu"
        )

    fracas = sorted(
        (p for p in alinhadas if p.score < CONFIANCA_BAIXA), key=lambda p: p.score
    )
    if not fracas:
        return
    print(f"{len(fracas)} palavras com confiança < {CONFIANCA_BAIXA}:")
    amostra = ", ".join(f'"{p.palavra}" ({_relogio(p.inicio)})' for p in fracas[:PIORES])
    resto = f" (+{len(fracas) - PIORES})" if len(fracas) > PIORES else ""
    print(f"  {amostra}{resto}")


def alinhar(numero: str, idioma: str = IDIOMA) -> int:
    projeto = resolver(numero)

    if not projeto.narracao_txt.is_file():
        raise ErroDeUso(f"falta o narration.txt — rode antes: studio narracao {projeto.numero}")

    caminho, eh_duble = projeto.audio()
    if not caminho.is_file():
        raise ErroDeUso(
            f"nenhum áudio — grave {projeto.wav.name} lendo build/narration.txt, "
            f"ou gere um provisório com  studio duble {projeto.numero}"
        )

    texto = projeto.narracao_txt.read_text(encoding="utf-8")
    nossas = t.palavras(texto)

    som = audio.sondar(caminho)
    lufs = audio.loudness(caminho)
    volume = f", {lufs:.1f} LUFS" if lufs is not None else ""
    print(f"áudio: {som}{volume}")
    for aviso in audio.conferir(som, lufs, len(nossas)):
        print(f"  aviso: {aviso}")

    projeto.garantir_build()
    entradas = [projeto.narracao_txt, caminho]
    params = {"idioma": idioma}
    refazer = [
        s for s in saidas(projeto) if cache.precisa_refazer(s, entradas, params, FERRAMENTA)
    ]

    if refazer:
        quantas = t.formatar_numero(len(nossas))
        print(f"alinhando {quantas} palavras... (whisperx, {idioma}, cpu)")
        alinhadas = alinhador.alinhar(caminho, texto, som.duracao, idioma)
        palavras = alinhador.casar(nossas, alinhadas, som.duracao)

        conteudos = {
            projeto.palavras: _json(projeto, palavras, som, eh_duble),
            projeto.narracao_srt: legendas.srt(palavras),
            projeto.narracao_vtt: legendas.vtt(palavras),
        }
        for saida, conteudo in conteudos.items():
            saida.write_text(conteudo, encoding="utf-8")
            cache.registrar(saida, entradas, params, FERRAMENTA)
    else:
        palavras = artefatos.ler_palavras(projeto.palavras)

    _relatorio(palavras)

    if refazer:
        for saida in saidas(projeto):
            print(f"→ build/{saida.name}")
    else:
        print("\n(sem mudança no texto nem no áudio — já estava alinhado)")

    if eh_duble:
        print("\n⚠ alinhado com o dublê. Regravar com a minha voz refaz tudo isto.")
    return 0
