V ?=
STUDIO := uv run studio

.DEFAULT_GOAL := ajuda

.PHONY: ajuda setup test check fmt limpar novo status narracao duble alinhar timeline assets montar shorts thumb meta tudo

ajuda:
	@echo "manutenção"
	@echo "  make setup            instala o ambiente"
	@echo "  make test             roda os testes"
	@echo "  make check            lint"
	@echo "  make fmt              formata"
	@echo "  make limpar V=01      apaga o build/ do vídeo (ou de todos, sem V)"
	@echo ""
	@echo "pipeline               (V=NN, ex: make status V=01)"
	@echo "  make novo NOME=01-batalha-naval"
	@echo "  make status V=01"
	@echo "  make narracao V=01     → narration.txt, o texto que eu leio"
	@echo "  make duble V=01        → voz sintética, pra testar sem gravar"
	@echo "  make alinhar V=01      → words.json + legendas"
	@echo "  make timeline V=01     → timeline.json + shorts.json"
	@echo "  make assets V=01       → as cenas"
	@echo "  make montar V=01       → video.mp4"
	@echo "  make shorts V=01       → verticais"
	@echo "  make thumb V=01        → thumb.png"
	@echo "  make meta V=01         → título, descrição, capítulos"
	@echo "  make tudo V=01"
	@echo ""
	@$(STUDIO) --version

setup:
	uv sync

test:
	uv run pytest -q

check:
	uv run --with ruff ruff check studio tests

fmt:
	uv run --with ruff ruff format studio
	uv run --with ruff ruff check --fix studio

limpar:
ifdef V
	rm -rf videos/$(V)-*/build
	@echo "build/ do vídeo $(V) apagado"
else
	rm -rf videos/*/build
	@echo "todos os build/ apagados"
endif

exige-v:
	@test -n "$(V)" || { echo "falta o vídeo: make $(MAKECMDGOALS) V=01"; exit 1; }

novo:
	@test -n "$(NOME)" || { echo "falta o nome: make novo NOME=01-batalha-naval"; exit 1; }
	$(STUDIO) novo $(NOME)

status:
	$(STUDIO) status $(V)

narracao duble alinhar timeline assets montar shorts thumb meta tudo: exige-v
	$(STUDIO) $@ $(V)
