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

var All = []Factory{
	{Name: "random", New: NewRandom},
	{Name: "hunt", New: NewHuntTarget},
	{Name: "parity", New: NewParity},
	{Name: "density", New: NewDensity},
}
