package game

type (
	ShipType struct {
		Name string
		Size int
	}
	Ship struct {
		Type  ShipType
		Cells []Position
		Hits  int
	}
)

var Fleet = []ShipType{
	{Name: "Carrier", Size: 5},
	{Name: "Battleship", Size: 4},
	{Name: "Cruiser", Size: 3},
	{Name: "Submarine", Size: 3},
	{Name: "Destroyer", Size: 2},
}

func (s *Ship) Sunk() bool {
	return s.Hits >= s.Type.Size
}

func (s *Ship) Hit() {
	s.Hits++
}
