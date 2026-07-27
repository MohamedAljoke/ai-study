package game

import (
	"fmt"
	"slices"
	"strings"
)

type (
	Orientation string

	Board struct {
		grid  [BoardSize][BoardSize]Cell
		ships []*Ship
	}

	Result struct {
		Hit  bool
		Sunk *Ship
	}
)

const (
	Horizontal Orientation = "horizontal"
	Vertical   Orientation = "vertical"
)

func (b *Board) At(p Position) Cell {
	if !p.Valid() {
		return CellEmpty
	}
	return b.grid[p.Row][p.Col]
}

func (b *Board) Ships() []*Ship {
	return b.ships
}

func (b *Board) String() string {
	return b.Render(true)
}

func (b *Board) Render(revealShips bool) string {
	var sb strings.Builder

	sb.WriteString("  ")
	for col := range BoardSize {
		fmt.Fprintf(&sb, "%c ", 'A'+rune(col))
	}
	sb.WriteByte('\n')

	for row := range BoardSize {
		fmt.Fprintf(&sb, "%d ", row)
		for col := range BoardSize {
			c := b.grid[row][col]
			if c == CellShip && !revealShips {
				c = CellEmpty
			}
			fmt.Fprintf(&sb, "%c ", c.Rune())
		}
		sb.WriteByte('\n')
	}

	return sb.String()
}

func (b *Board) CanPlace(t ShipType, origin Position, o Orientation) error {
	if !o.Valid() {
		return fmt.Errorf("invalid orientation: %v", o)
	}

	for _, p := range Span(origin, t.Size, o) {
		if !p.Valid() {
			return fmt.Errorf("%s at %v %v: runs off the board", t.Name, origin, o)
		}
		if b.grid[p.Row][p.Col] != CellEmpty {
			return fmt.Errorf("%s at %v %v: overlaps another ship at %v", t.Name, origin, o, p)
		}
	}

	return nil
}

func (b *Board) Place(t ShipType, origin Position, o Orientation) (*Ship, error) {
	if err := b.CanPlace(t, origin, o); err != nil {
		return nil, err
	}

	cells := Span(origin, t.Size, o)
	for _, p := range cells {
		b.grid[p.Row][p.Col] = CellShip
	}

	ship := &Ship{Type: t, Cells: cells}
	b.ships = append(b.ships, ship)

	return ship, nil
}

// Span returns the cells a ship of the given size covers from origin.
func Span(origin Position, size int, o Orientation) []Position {
	cells := make([]Position, size)
	for i := range cells {
		if o == Horizontal {
			cells[i] = Position{Row: origin.Row, Col: origin.Col + i}
		} else {
			cells[i] = Position{Row: origin.Row + i, Col: origin.Col}
		}
	}

	return cells
}

func (b *Board) Fire(position Position) (Result, error) {
	if !position.Valid() {
		return Result{}, fmt.Errorf("invalid position: %v", position)
	}

	if b.grid[position.Row][position.Col].Shot() {
		return Result{}, fmt.Errorf("position already fired at: %v", position)
	}

	if b.grid[position.Row][position.Col] != CellShip {
		b.grid[position.Row][position.Col] = CellMiss
		return Result{Hit: false}, nil
	}

	b.grid[position.Row][position.Col] = CellHit
	ship := b.shipAt(position)
	ship.Hit()

	res := Result{Hit: true}
	if ship.Sunk() {
		res.Sunk = ship
	}

	return res, nil
}

func (b *Board) shipAt(p Position) *Ship {
	for _, ship := range b.ships {
		if slices.Contains(ship.Cells, p) {
			return ship
		}
	}

	return nil
}

func (b *Board) AllSunk() bool {
	if len(b.ships) == 0 {
		return false
	}

	for _, ship := range b.ships {
		if !ship.Sunk() {
			return false
		}
	}

	return true
}

func (o Orientation) Valid() bool {
	return o == Horizontal || o == Vertical
}

func ParseOrientation(s string) (Orientation, error) {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "h", string(Horizontal):
		return Horizontal, nil
	case "v", string(Vertical):
		return Vertical, nil
	}

	return "", fmt.Errorf("%q: want h or v", s)
}
