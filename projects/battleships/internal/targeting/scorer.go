package targeting

import "battleships/internal/game"

// Grid holds one value per cell, laid out row-major like the board itself.
type Grid [game.BoardSize][game.BoardSize]float64

// Scorer is the optional half of Strategy: a strategy that ranks every cell
// before picking one can hand that ranking out, and the UI paints it as a
// heatmap. Strategies that have no notion of a score — random, hunt, parity —
// simply do not implement it, and callers type-assert.
//
// Scores must not advance the strategy's state: it answers "what do you think
// right now", and Next stays the only thing that commits to a shot.
type Scorer interface {
	// Scores returns the current per-cell ranking normalized to 0..1 by the
	// highest scoring cell. Cells already shot at score 0.
	Scores() Grid
}

// normalize scales a raw score table into a Grid, dividing by the largest
// entry so every strategy's heatmap uses the same 0..1 range regardless of how
// it weighs things internally.
func normalize(score [cells]int, shot [cells]bool) Grid {
	high := 0
	for i := range cells {
		if !shot[i] && score[i] > high {
			high = score[i]
		}
	}

	var g Grid
	if high == 0 {
		return g
	}

	for i := range cells {
		if shot[i] {
			continue
		}
		g[i/game.BoardSize][i%game.BoardSize] = float64(score[i]) / float64(high)
	}

	return g
}
