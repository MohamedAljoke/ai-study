package game

import "fmt"

const BoardSize = 10

type Position struct {
	Row, Col int
}

func (p Position) Valid() bool {
	return p.Row >= 0 && p.Row < BoardSize && p.Col >= 0 && p.Col < BoardSize
}

func (p Position) String() string {
	return fmt.Sprintf("%c%d", 'A'+rune(p.Col), p.Row)
}
