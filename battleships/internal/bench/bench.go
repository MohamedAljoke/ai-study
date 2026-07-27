package bench

import (
	"fmt"
	"math/rand/v2"

	"battleships/internal/game"
	"battleships/internal/placement"
	"battleships/internal/replay"
	"battleships/internal/targeting"
)

const seed = 42

func Play(p placement.Factory, s targeting.Factory, gameIdx int, rec *replay.Recorder) (int, error) {
	rng := rand.New(rand.NewPCG(seed, uint64(gameIdx)))

	var b game.Board
	if err := p.Place(&b, game.Fleet, rng); err != nil {
		return 0, err
	}

	if err := rec.Snapshot(&b, "initial fleet"); err != nil {
		return 0, err
	}

	strategy := s.New(rng)

	for shots := 1; shots <= game.BoardSize*game.BoardSize; shots++ {
		q := strategy.Next()

		res, err := b.Fire(q)
		if err != nil {
			return 0, fmt.Errorf("shot %d at %v: %w", shots, q, err)
		}
		strategy.Observe(q, res)

		if err := rec.Snapshot(&b, fmt.Sprintf("shot %d at %v: %s", shots, q, describe(res))); err != nil {
			return 0, err
		}

		if b.AllSunk() {
			return shots, nil
		}
	}

	return 0, fmt.Errorf("fleet still afloat after every cell was shot")
}

func describe(r game.Result) string {
	switch {
	case r.Sunk != nil:
		return "hit, sank " + r.Sunk.Type.Name
	case r.Hit:
		return "hit"
	default:
		return "miss"
	}
}

type stats struct {
	total, best, worst, played int
}

func (s stats) average() float64 {
	if s.played == 0 {
		return 0
	}

	return float64(s.total) / float64(s.played)
}

func (s *stats) record(shots int) {
	if s.played == 0 || shots < s.best {
		s.best = shots
	}
	s.worst = max(s.worst, shots)
	s.total += shots
	s.played++
}
