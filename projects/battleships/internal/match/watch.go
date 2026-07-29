package match

import (
	"fmt"
	"math/rand/v2"

	"battleships/internal/game"
	"battleships/internal/placement"
	"battleships/internal/targeting"
)

// Step is one shot in a race, attributed by side index rather than by name so
// a strategy can be raced against itself.
type Step struct {
	By   int
	At   game.Position
	Hit  bool
	Sunk string
}

// Race is a finished game between two strategies, recorded shot by shot. It is
// played to completion up front and handed over whole: the client scrubs
// through Steps at whatever speed it likes, forwards or back.
type Race struct {
	Names  [2]string
	Boards [2]game.Board // final layouts, revealed — the game is over
	Steps  []Step
	Winner int
	Shots  [2]int
}

// Run plays two strategies against each other, each shooting at the other's
// fleet, side 0 first. The seed makes a race reproducible and therefore
// shareable, the same way internal/bench pins its seed.
func Run(a, b targeting.Factory, layout placement.Factory, seed uint64) (*Race, error) {
	rng := rand.New(rand.NewPCG(seed, seed+1))

	r := &Race{Names: [2]string{a.Name, b.Name}, Winner: -1}
	ai := [2]targeting.Strategy{a.New(rng), b.New(rng)}

	for i := range r.Boards {
		if err := layout.Place(&r.Boards[i], game.Fleet, rng); err != nil {
			return nil, fmt.Errorf("placing fleet %d: %w", i, err)
		}
	}

	for side := 0; r.Winner < 0; side = 1 - side {
		target := &r.Boards[1-side]

		p := ai[side].Next()

		res, err := target.Fire(p)
		if err != nil {
			return nil, fmt.Errorf("%s fired at %v: %w", r.Names[side], p, err)
		}
		ai[side].Observe(p, res)

		step := Step{By: side, At: p, Hit: res.Hit}
		if res.Sunk != nil {
			step.Sunk = res.Sunk.Type.Name
		}
		r.Steps = append(r.Steps, step)
		r.Shots[side]++

		if target.AllSunk() {
			r.Winner = side
		}
	}

	return r, nil
}
