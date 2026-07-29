"""Rodar uma etapa do pipeline em subprocesso e ver o log escorrer.

`processos.py` é pra ferramenta que responde e acaba — ele captura a saída inteira e só
devolve no fim. Aqui é o contrário: `alinhar` leva minutos, e ficar olhando uma página
parada sem saber se travou é o pior jeito de esperar. Então o processo é `Popen` e as
linhas vão aparecendo.

Subprocesso, e não chamada direta da função do comando: assim o torch e o ffmpeg ficam
fora do processo do servidor, uma etapa travada não derruba a página, e o log é
literalmente o que eu veria no terminal.

O estado mora em memória de propósito — é log, e o resultado de verdade está sempre no
`build/` (§4). Reiniciar o servidor perde o histórico e não perde trabalho.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field

from studio.projeto import ErroDeUso

INTERVALO = 0.1
"""De quanto em quanto tempo quem acompanha volta a olhar se chegou linha nova."""


@dataclass
class Tarefa:
    id: str
    comando: str
    numero: str
    argumentos: list[str]
    linhas: list[str] = field(default_factory=list)
    codigo: int | None = None
    """`None` enquanto roda. É o último campo a ser preenchido — ver `acompanhar`."""

    @property
    def terminou(self) -> bool:
        return self.codigo is not None

    def json(self) -> dict:
        return {
            "id": self.id,
            "comando": self.comando,
            "numero": self.numero,
            "linhas": list(self.linhas),
            "codigo": self.codigo,
            "terminou": self.terminou,
        }


_tarefas: dict[str, Tarefa] = {}
_atual: Tarefa | None = None
_trava = threading.Lock()


def _argumentos(comando: str, numero: str, flags: list[str]) -> list[str]:
    """Monta a linha de comando a partir do `PIPELINE`, nunca do que o cliente mandou.

    Aceitar flag arbitrária aqui seria deixar a página escolher argumento de subprocesso.
    """
    from studio.cli import PIPELINE

    if comando == "ui":
        raise ErroDeUso("a interface não roda a si mesma")

    escolhido = next((c for c in PIPELINE if c.nome == comando), None)
    if escolhido is None or escolhido.executar is None:
        raise ErroDeUso(f"comando desconhecido: {comando}")

    conhecidas = {f.nome for f in escolhido.flags}
    if desconhecidas := [f for f in flags if f not in conhecidas]:
        raise ErroDeUso(f"{comando} não tem a opção {', '.join(desconhecidas)}")
    return [comando, numero, *flags]


def _ler(tarefa: Tarefa, processo: subprocess.Popen) -> None:
    for linha in processo.stdout:  # type: ignore[union-attr]
        tarefa.linhas.append(linha.rstrip("\n"))
    processo.wait()
    if processo.returncode:
        tarefa.linhas.append(f"— saiu com código {processo.returncode}")
    tarefa.codigo = processo.returncode


def iniciar(comando: str, numero: str, flags: list[str] | None = None) -> Tarefa:
    """Uma por vez: duas montagens ao mesmo tempo brigariam pelo mesmo `build/`."""
    global _atual

    argumentos = _argumentos(comando, numero, list(flags or []))
    with _trava:
        if _atual is not None and not _atual.terminou:
            raise ErroDeUso(
                f"já tem uma etapa rodando: studio {_atual.comando} {_atual.numero}"
            )
        tarefa = Tarefa(
            id=f"{comando}-{numero}-{int(time.time() * 1000)}",
            comando=comando,
            numero=numero,
            argumentos=argumentos,
        )
        _tarefas[tarefa.id] = tarefa
        _atual = tarefa

    ambiente = {**os.environ, "PYTHONUNBUFFERED": "1"}
    processo = subprocess.Popen(
        [sys.executable, "-m", "studio.cli", *argumentos],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=ambiente,
    )
    threading.Thread(target=_ler, args=(tarefa, processo), daemon=True).start()
    return tarefa


def obter(id: str) -> Tarefa:
    if id not in _tarefas:
        raise ErroDeUso(f"tarefa desconhecida: {id}")
    return _tarefas[id]


def atual() -> Tarefa | None:
    return _atual


def acompanhar(id: str) -> Iterator[str]:
    """As linhas da tarefa, da primeira até a última, esperando pelas que faltam."""
    tarefa = obter(id)
    enviadas = 0
    while True:
        # ler o fim ANTES de drenar: `codigo` é preenchido depois da última linha, então
        # ver "terminou" aqui garante que o que vem abaixo já é tudo que existe
        acabou = tarefa.terminou
        while enviadas < len(tarefa.linhas):
            yield tarefa.linhas[enviadas]
            enviadas += 1
        if acabou:
            return
        time.sleep(INTERVALO)


def esquecer() -> None:
    """Zera o registro. Existe pros testes não herdarem tarefa de outro teste."""
    global _atual
    _tarefas.clear()
    _atual = None
