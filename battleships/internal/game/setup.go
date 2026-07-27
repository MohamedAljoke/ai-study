package game

func AllPositions() []Position {
	all := make([]Position, 0, BoardSize*BoardSize)
	for row := range BoardSize {
		for col := range BoardSize {
			all = append(all, Position{Row: row, Col: col})
		}
	}

	return all
}
