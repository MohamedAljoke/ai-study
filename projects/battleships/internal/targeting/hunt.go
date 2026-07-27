package targeting

import (
	"math/rand/v2"

	"battleships/internal/game"
)

type HuntTarget struct {
	hunt  []game.Position
	next  int
	queue []game.Position
	shot  map[game.Position]bool
}

func NewHuntTarget(rng *rand.Rand) Strategy {
	hunt := game.AllPositions()
	rng.Shuffle(len(hunt), func(i, j int) {
		hunt[i], hunt[j] = hunt[j], hunt[i]
	})

	return &HuntTarget{
		hunt: hunt,
		shot: make(map[game.Position]bool, len(hunt)),
	}
}

func (h *HuntTarget) Next() game.Position {
	for len(h.queue) > 0 {
		p := h.queue[len(h.queue)-1]
		h.queue = h.queue[:len(h.queue)-1]

		if !h.shot[p] {
			return h.take(p)
		}
	}

	for h.next < len(h.hunt) {
		p := h.hunt[h.next]
		h.next++

		if !h.shot[p] {
			return h.take(p)
		}
	}

	panic("hunt list exhausted: Next called more than once per cell")
}

func (h *HuntTarget) take(p game.Position) game.Position {
	h.shot[p] = true

	return p
}

func (h *HuntTarget) Observe(p game.Position, r game.Result) {
	if r.Sunk != nil {
		h.queue = h.queue[:0]

		return
	}

	if !r.Hit {
		return
	}

	for _, n := range neighbours(p) {
		if n.Valid() && !h.shot[n] {
			h.queue = append(h.queue, n)
		}
	}
}

func neighbours(p game.Position) [4]game.Position {
	return [4]game.Position{
		{Row: p.Row - 1, Col: p.Col},
		{Row: p.Row + 1, Col: p.Col},
		{Row: p.Row, Col: p.Col - 1},
		{Row: p.Row, Col: p.Col + 1},
	}
}
