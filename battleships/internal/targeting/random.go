package targeting

import (
	"math/rand/v2"

	"battleships/internal/game"
)

type Random struct {
	targets []game.Position
	next    int
}

func NewRandom(rng *rand.Rand) Strategy {
	targets := game.AllPositions()
	rng.Shuffle(len(targets), func(i, j int) {
		targets[i], targets[j] = targets[j], targets[i]
	})

	return &Random{targets: targets}
}

func (r *Random) Next() game.Position {
	p := r.targets[r.next]
	r.next++

	return p
}

func (r *Random) Observe(game.Position, game.Result) {}
