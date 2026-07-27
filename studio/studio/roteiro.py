"""O roteiro como dado: fala, bloco, cena, short, aviso.

Só os tipos e o que dá pra derivar deles. Quem lê o markdown é `leitura.py`, quem
checa marcador é `validacao.py` — este arquivo não abre arquivo nenhum.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from studio import texto as t


@dataclass
class Fala:
    linha: int
    texto: str
    palavra_inicio: int
    palavra_fim: int


@dataclass
class Bloco:
    titulo: str
    nivel: int
    linha: int
    palavra_inicio: int
    palavra_fim: int = -1


@dataclass
class Cena:
    id: str
    tipo: str
    linha: int
    params: dict[str, str] = field(default_factory=dict)
    palavra_inicio: int = -1
    palavra_fim: int = -1


@dataclass
class Short:
    id: str
    titulo: str
    linha: int
    linha_fim: int = -1
    palavra_inicio: int = -1
    palavra_fim: int = -1


@dataclass
class Aviso:
    tipo: str
    linha: int
    texto: str


@dataclass
class Roteiro:
    titulo: str
    origem: Path
    falas: list[Fala] = field(default_factory=list)
    blocos: list[Bloco] = field(default_factory=list)
    cenas: list[Cena] = field(default_factory=list)
    shorts: list[Short] = field(default_factory=list)
    avisos: list[Aviso] = field(default_factory=list)
    eventos: list[tuple[str, object]] = field(default_factory=list)
    total_palavras: int = 0

    def duracao(self, wpm: int = t.PALAVRAS_POR_MINUTO) -> float:
        return t.estimar_duracao(self.total_palavras, wpm)

    def narracao(self) -> str:
        """O que eu leio em voz alta, e o que o alinhador recebe."""
        return "\n\n".join(f.texto for f in self.falas) + "\n"

    def leitura(self) -> str:
        """A mesma narração com títulos e marcadores, pra eu não me perder na tela."""
        linhas = [f"# {self.titulo}", ""]
        for tipo, evento in self.eventos:
            if tipo == "bloco":
                linhas += ["", f"## {evento.titulo}", ""]
            elif tipo == "cena":
                linhas.append(f"<!-- {evento.tipo}: {evento.id} -->")
            elif tipo == "short-inicio":
                linhas.append(f"<!-- short ▶ {evento.id} — {evento.titulo} -->")
            elif tipo == "short-fim":
                linhas.append(f"<!-- short ■ {evento.id} -->")
            else:
                linhas += [evento.texto, ""]
        return "\n".join(linhas).strip() + "\n"

    def json(self) -> dict:
        return {
            "video": self.origem.parent.name,
            "titulo": self.titulo,
            "palavras": self.total_palavras,
            "duracao_estimada": round(self.duracao(), 1),
            "blocos": [
                {
                    "titulo": b.titulo,
                    "nivel": b.nivel,
                    "linha": b.linha,
                    "palavra_inicio": b.palavra_inicio,
                    "palavra_fim": b.palavra_fim,
                }
                for b in self.blocos
            ],
            "cenas": [
                {
                    "id": c.id,
                    "tipo": c.tipo,
                    "linha": c.linha,
                    "params": c.params,
                    "palavra_inicio": c.palavra_inicio,
                    "palavra_fim": c.palavra_fim,
                }
                for c in self.cenas
            ],
            "shorts": [
                {
                    "id": s.id,
                    "titulo": s.titulo,
                    "linha": s.linha,
                    "palavra_inicio": s.palavra_inicio,
                    "palavra_fim": s.palavra_fim,
                }
                for s in self.shorts
            ],
        }
