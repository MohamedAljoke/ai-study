package targeting

import (
	"math/rand/v2"

	"battleships/internal/game"
)

const (
	cells     = game.BoardSize * game.BoardSize
	hitWeight = 16
)

var _ Scorer = (*Density)(nil)

type Density struct {
	rng *rand.Rand

	shot [cells]bool
	miss [cells]bool
	dead [cells]bool
	hit  [cells]bool

	afloat []int
	score  [cells]int
}

func NewDensity(rng *rand.Rand) Strategy {
	afloat := make([]int, 0, len(game.Fleet))
	for _, t := range game.Fleet {
		afloat = append(afloat, t.Size)
	}

	return &Density{rng: rng, afloat: afloat}
}

func (d *Density) Next() game.Position {
	d.rescore()

	best, tied := -1, 0
	for i := range cells {
		if d.shot[i] || d.score[i] == 0 {
			continue
		}

		switch {
		case best < 0 || d.score[i] > d.score[best]:
			best, tied = i, 1
		case d.score[i] == d.score[best]:
			tied++
			if d.rng.IntN(tied) == 0 {
				best = i
			}
		}
	}

	if best < 0 {
		best = d.anyUnshot()
	}

	d.shot[best] = true

	return game.Position{Row: best / game.BoardSize, Col: best % game.BoardSize}
}

// Scores exposes the same table Next picks its argmax from. rescore rebuilds
// it from the observations alone, so asking costs a recount but changes
// nothing the strategy will do next.
func (d *Density) Scores() Grid {
	d.rescore()

	return normalize(d.score, d.shot)
}

func (d *Density) rescore() {
	d.score = [cells]int{}

	for _, size := range d.afloat {
		for row := range game.BoardSize {
			for col := range game.BoardSize {
				d.count(row, col, size, game.Horizontal)
				d.count(row, col, size, game.Vertical)
			}
		}
	}
}

func (d *Density) count(row, col, size int, o game.Orientation) {
	if o == game.Horizontal && col+size > game.BoardSize {
		return
	}
	if o == game.Vertical && row+size > game.BoardSize {
		return
	}

	weight, hits := 1, 0
	for i := range size {
		c := offset(row, col, i, o)
		if d.miss[c] || d.dead[c] {
			return
		}
		if d.hit[c] {
			hits++
		}
	}

	for range hits {
		weight *= hitWeight
	}

	for i := range size {
		if c := offset(row, col, i, o); !d.shot[c] {
			d.score[c] += weight
		}
	}
}

func (d *Density) Observe(p game.Position, r game.Result) {
	c := index(p)
	d.shot[c] = true

	switch {
	case r.Sunk != nil:
		for _, s := range r.Sunk.Cells {
			i := index(s)
			d.hit[i] = false
			d.dead[i] = true
		}
		d.afloat = sink(d.afloat, r.Sunk.Type.Size)
	case r.Hit:
		d.hit[c] = true
	default:
		d.miss[c] = true
	}
}

func (d *Density) anyUnshot() int {
	for i := range cells {
		if !d.shot[i] {
			return i
		}
	}

	panic("board exhausted: Next called more than once per cell")
}

func sink(afloat []int, size int) []int {
	for i, s := range afloat {
		if s == size {
			return append(afloat[:i], afloat[i+1:]...)
		}
	}

	return afloat
}

func index(p game.Position) int {
	return p.Row*game.BoardSize + p.Col
}

func offset(row, col, i int, o game.Orientation) int {
	if o == game.Horizontal {
		return row*game.BoardSize + col + i
	}

	return (row+i)*game.BoardSize + col
}
