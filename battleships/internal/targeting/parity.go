package targeting

import (
	"math/rand/v2"
	"slices"

	"battleships/internal/game"
)

type Parity struct {
	hunt  []game.Position
	next  int
	shot  map[game.Position]bool
	hits  []game.Position
	queue []game.Position
}

func NewParity(rng *rand.Rand) Strategy {
	all := game.AllPositions()

	hunt := make([]game.Position, 0, len(all))
	for _, p := range all {
		if (p.Row+p.Col)%2 == 0 {
			hunt = append(hunt, p)
		}
	}
	rng.Shuffle(len(hunt), func(i, j int) { hunt[i], hunt[j] = hunt[j], hunt[i] })

	odd := make([]game.Position, 0, len(all)/2)
	for _, p := range all {
		if (p.Row+p.Col)%2 != 0 {
			odd = append(odd, p)
		}
	}
	rng.Shuffle(len(odd), func(i, j int) { odd[i], odd[j] = odd[j], odd[i] })

	return &Parity{
		hunt: append(hunt, odd...),
		shot: make(map[game.Position]bool, len(all)),
	}
}

func (p *Parity) Next() game.Position {
	for len(p.queue) > 0 {
		c := p.queue[len(p.queue)-1]
		p.queue = p.queue[:len(p.queue)-1]

		if !p.shot[c] {
			return p.take(c)
		}
	}

	for p.next < len(p.hunt) {
		c := p.hunt[p.next]
		p.next++

		if !p.shot[c] {
			return p.take(c)
		}
	}

	panic("hunt list exhausted: Next called more than once per cell")
}

func (p *Parity) take(c game.Position) game.Position {
	p.shot[c] = true

	return c
}

func (p *Parity) Observe(c game.Position, r game.Result) {
	if r.Sunk != nil {
		p.hits = remove(p.hits, r.Sunk.Cells)
		p.rebuild()

		return
	}

	if !r.Hit {
		return
	}

	p.hits = append(p.hits, c)
	p.rebuild()
}

func (p *Parity) rebuild() {
	p.queue = p.queue[:0]
	if len(p.hits) == 0 {
		return
	}

	last := p.hits[len(p.hits)-1]

	sameRow, sameCol := false, false
	for _, h := range p.hits[:len(p.hits)-1] {
		if h.Row == last.Row {
			sameRow = true
		}
		if h.Col == last.Col {
			sameCol = true
		}
	}

	switch {
	case sameRow:
		p.push(ends(p.hits, last, true))
	case sameCol:
		p.push(ends(p.hits, last, false))
	default:
		p.push(neighbours(last))
	}
}

func (p *Parity) push(cs [4]game.Position) {
	for _, c := range cs {
		if c.Valid() && !p.shot[c] {
			p.queue = append(p.queue, c)
		}
	}
}

func ends(hits []game.Position, last game.Position, horizontal bool) [4]game.Position {
	lo, hi := last, last
	for _, h := range hits {
		if horizontal && h.Row == last.Row {
			lo.Col = min(lo.Col, h.Col)
			hi.Col = max(hi.Col, h.Col)
		}
		if !horizontal && h.Col == last.Col {
			lo.Row = min(lo.Row, h.Row)
			hi.Row = max(hi.Row, h.Row)
		}
	}

	off := game.Position{Row: -1, Col: -1}
	if horizontal {
		return [4]game.Position{
			{Row: lo.Row, Col: lo.Col - 1},
			{Row: hi.Row, Col: hi.Col + 1},
			off, off,
		}
	}

	return [4]game.Position{
		{Row: lo.Row - 1, Col: lo.Col},
		{Row: hi.Row + 1, Col: hi.Col},
		off, off,
	}
}

func remove(hits []game.Position, sunk []game.Position) []game.Position {
	kept := hits[:0]
	for _, h := range hits {
		if !slices.Contains(sunk, h) {
			kept = append(kept, h)
		}
	}

	return kept
}
