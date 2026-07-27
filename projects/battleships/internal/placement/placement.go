package placement

import (
	"fmt"
	"math/rand/v2"

	"battleships/internal/game"
)

type Factory struct {
	Name  string
	Place func(b *game.Board, fleet []game.ShipType, rng *rand.Rand) error
}

var All = []Factory{
	{Name: "uniform", Place: Uniform},
	{Name: "edges", Place: Edges},
	{Name: "center", Place: Center},
	{Name: "spread", Place: Spread},
}

var orientations = []game.Orientation{game.Horizontal, game.Vertical}

type weigh func(b *game.Board, cells []game.Position) int

func Uniform(b *game.Board, fleet []game.ShipType, rng *rand.Rand) error {
	return place(b, fleet, rng, func(*game.Board, []game.Position) int { return 1 })
}

func Edges(b *game.Board, fleet []game.ShipType, rng *rand.Rand) error {
	return place(b, fleet, rng, func(_ *game.Board, cells []game.Position) int {
		w := 0
		for _, c := range cells {
			r := maxDepth + 1 - depth(c)
			w += r * r
		}

		return w
	})
}

func Center(b *game.Board, fleet []game.ShipType, rng *rand.Rand) error {
	return place(b, fleet, rng, func(_ *game.Board, cells []game.Position) int {
		w := 0
		for _, c := range cells {
			r := 1 + depth(c)
			w += r * r
		}

		return w
	})
}

func Spread(b *game.Board, fleet []game.ShipType, rng *rand.Rand) error {
	return place(b, fleet, rng, func(b *game.Board, cells []game.Position) int {
		for _, c := range cells {
			for _, n := range around(c) {
				if b.At(n) == game.CellShip {
					return 0
				}
			}
		}

		return 1
	})
}

func place(b *game.Board, fleet []game.ShipType, rng *rand.Rand, w weigh) error {
	for _, t := range fleet {
		if err := one(b, t, rng, w); err != nil {
			return err
		}
	}

	return nil
}

type candidate struct {
	origin game.Position
	o      game.Orientation
	weight int
}

func one(b *game.Board, t game.ShipType, rng *rand.Rand, w weigh) error {
	var cands []candidate
	total := 0

	for row := range game.BoardSize {
		for col := range game.BoardSize {
			origin := game.Position{Row: row, Col: col}
			for _, o := range orientations {
				if b.CanPlace(t, origin, o) != nil {
					continue
				}

				weight := w(b, game.Span(origin, t.Size, o))
				cands = append(cands, candidate{origin: origin, o: o, weight: weight})
				total += weight
			}
		}
	}

	if len(cands) == 0 {
		return fmt.Errorf("placing %s: no legal position left on the board", t.Name)
	}

	if total == 0 {
		for i := range cands {
			cands[i].weight = 1
		}
		total = len(cands)
	}

	pick := rng.IntN(total)
	for _, c := range cands {
		if pick -= c.weight; pick < 0 {
			_, err := b.Place(t, c.origin, c.o)

			return err
		}
	}

	return fmt.Errorf("placing %s: weighted pick fell through", t.Name)
}

const maxDepth = game.BoardSize/2 - 1

func depth(p game.Position) int {
	return min(p.Row, p.Col, game.BoardSize-1-p.Row, game.BoardSize-1-p.Col)
}

func around(p game.Position) []game.Position {
	var ns []game.Position
	for dr := -1; dr <= 1; dr++ {
		for dc := -1; dc <= 1; dc++ {
			if dr == 0 && dc == 0 {
				continue
			}

			if n := (game.Position{Row: p.Row + dr, Col: p.Col + dc}); n.Valid() {
				ns = append(ns, n)
			}
		}
	}

	return ns
}
