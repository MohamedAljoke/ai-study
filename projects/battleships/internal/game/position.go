package game

import (
	"fmt"
	"strconv"
	"strings"
)

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

func ParsePosition(s string) (Position, error) {
	s = strings.ToUpper(strings.TrimSpace(s))
	if len(s) < 2 || s[0] < 'A' || s[0] > 'Z' {
		return Position{}, fmt.Errorf("%q: want a letter then a number, like A0", s)
	}

	row, err := strconv.Atoi(s[1:])
	if err != nil {
		return Position{}, fmt.Errorf("%q: want a letter then a number, like A0", s)
	}

	p := Position{Row: row, Col: int(s[0] - 'A')}
	if !p.Valid() {
		return Position{}, fmt.Errorf("%q: off the board", s)
	}

	return p, nil
}
