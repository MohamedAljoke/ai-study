// Command battleships runs headless games to measure how many shots each
// targeting strategy needs to sink a whole fleet. Every strategy faces the
// same sequence of fleets, so the numbers can be compared directly.
package main

import (
	"fmt"
	"log"
	"math/rand/v2"
	"os"
	"text/tabwriter"

	"battleships/internal/game"
	"battleships/internal/replay"
	"battleships/internal/targeting"
)

const (
	games      = 100000
	traceGames = 3
	traceDir   = "traces"
	seed       = 42
)

var strategies = []targeting.Factory{
	{Name: "random", New: targeting.NewRandom},
	{Name: "hunt", New: targeting.NewHuntTarget},
}

func main() {
	if err := os.RemoveAll(traceDir); err != nil {
		log.Fatal(err)
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "strategy\tavg\tbest\tworst")

	for _, f := range strategies {
		s, err := benchmark(f)
		if err != nil {
			log.Fatalf("%s: %v", f.Name, err)
		}
		fmt.Fprintf(w, "%s\t%.1f\t%d\t%d\n", f.Name, s.average(), s.best, s.worst)
	}

	if err := w.Flush(); err != nil {
		log.Fatal(err)
	}
	fmt.Printf("\n%d games, %d cells per board\n", games, game.BoardSize*game.BoardSize)
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

func benchmark(f targeting.Factory) (stats, error) {
	var s stats

	for g := range games {
		rng := rand.New(rand.NewPCG(seed, uint64(g)))

		// Only the first few games are traced; snapshotting every game would
		// mean millions of file writes.
		var rec *replay.Recorder
		if g < traceGames {
			var err error
			if rec, err = replay.New(traceDir, f.Name, g); err != nil {
				return s, err
			}
		}

		shots, err := play(f.New(rng), rng, rec)
		if err != nil {
			return s, fmt.Errorf("game %d: %w", g, err)
		}
		s.record(shots)
	}

	return s, nil
}

func play(s targeting.Strategy, rng *rand.Rand, rec *replay.Recorder) (int, error) {
	var b game.Board
	if err := game.PlaceFleet(&b, game.Fleet, rng); err != nil {
		return 0, err
	}

	if err := rec.Snapshot(&b, "initial fleet"); err != nil {
		return 0, err
	}

	for shots := 1; shots <= game.BoardSize*game.BoardSize; shots++ {
		p := s.Next()

		res, err := b.Fire(p)
		if err != nil {
			return 0, fmt.Errorf("shot %d at %v: %w", shots, p, err)
		}
		s.Observe(p, res)

		if err := rec.Snapshot(&b, fmt.Sprintf("shot %d at %v: %s", shots, p, describe(res))); err != nil {
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
