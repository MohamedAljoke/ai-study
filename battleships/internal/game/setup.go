package game

import (
	"fmt"
	"math/rand/v2"
)

const maxPlacementAttempts = 1000

func PlaceFleet(b *Board, fleet []ShipType, rng *rand.Rand) error {
	for _, t := range fleet {
		if err := placeRandom(b, t, rng); err != nil {
			return err
		}
	}
	return nil
}

func placeRandom(b *Board, t ShipType, rng *rand.Rand) error {
	for range maxPlacementAttempts {
		origin := Position{Row: rng.IntN(BoardSize), Col: rng.IntN(BoardSize)}
		o := orientations[rng.IntN(len(orientations))]

		if _, err := b.Place(t, origin, o); err == nil {
			return nil
		}
	}
	return fmt.Errorf("placing %s: no legal position found in %d attempts", t.Name, maxPlacementAttempts)
}

func AllPositions() []Position {
	all := make([]Position, 0, BoardSize*BoardSize)
	for row := range BoardSize {
		for col := range BoardSize {
			all = append(all, Position{Row: row, Col: col})
		}
	}
	return all
}
