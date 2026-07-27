package game

type Cell uint8

const (
	CellEmpty Cell = iota
	CellShip
	CellHit
	CellMiss
)

func (c Cell) Rune() rune {
	switch c {
	case CellShip:
		return 'S'
	case CellHit:
		return 'X'
	case CellMiss:
		return 'M'
	default:
		return '.'
	}
}

func (c Cell) String() string { return string(c.Rune()) }

func (c Cell) Shot() bool { return c == CellHit || c == CellMiss }
