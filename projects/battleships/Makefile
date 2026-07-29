GAMES ?= 5000
TRACE_GAMES ?= 3
PKG ?= ./...

.PHONY: play serve matrix bench traces test fmt vet check clean

play:
	go run ./cmd/play

serve:
	go run ./cmd/server -addr :8080

matrix:
	go test ./internal/bench -run TestMatrix -games $(GAMES) -v

bench:
	go test ./internal/bench -run '^$$' -bench BenchmarkMatrix -benchtime 2000x

traces:
	go test ./internal/bench -run TestTraces -traces -traces.games $(TRACE_GAMES) -v

test:
	go test -short $(PKG)

fmt:
	gofmt -l -w .

vet:
	go vet $(PKG)

check: fmt vet test

clean:
	rm -rf internal/bench/traces
