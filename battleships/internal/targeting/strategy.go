package targeting

import (
	"math/rand/v2"

	"battleships/internal/game"
)

type Strategy interface {
	Next() game.Position
	Observe(p game.Position, r game.Result)
}

type Factory struct {
	Name string
	New  func(rng *rand.Rand) Strategy
}
