package web

import (
	"battleships/internal/game"
	"battleships/internal/match"
	"battleships/internal/placement"
	"battleships/internal/targeting"
)

// Cell states as the browser sees them. "sunk" is not a game.Cell — it is a
// hit that finished a ship, split out here so the UI can colour it differently
// without knowing which cells belong to which ship.
const (
	cellEmpty = "empty"
	cellShip  = "ship"
	cellHit   = "hit"
	cellMiss  = "miss"
	cellSunk  = "sunk"
)

type position struct {
	Row int `json:"row"`
	Col int `json:"col"`
}

type shipSpec struct {
	Name string `json:"name"`
	Size int    `json:"size"`
}

type shipView struct {
	Name  string     `json:"name"`
	Size  int        `json:"size"`
	Hits  int        `json:"hits"`
	Sunk  bool       `json:"sunk"`
	Cells []position `json:"cells,omitempty"`
}

type boardView struct {
	Cells [game.BoardSize][game.BoardSize]string `json:"cells"`
	Ships []shipView                             `json:"ships"`
}

type stateView struct {
	Opponent  string     `json:"opponent"`
	Phase     string     `json:"phase"`
	Turn      int        `json:"turn"`
	Over      bool       `json:"over"`
	Scorable  bool       `json:"scorable"`
	Remaining []shipSpec `json:"remaining"`
	Mine      boardView  `json:"mine"`
	Theirs    boardView  `json:"theirs"`
}

type eventView struct {
	By   string `json:"by"`
	At   string `json:"at"`
	Row  int    `json:"row"`
	Col  int    `json:"col"`
	Hit  bool   `json:"hit"`
	Sunk string `json:"sunk,omitempty"`
}

type gameCreatedView struct {
	ID    string    `json:"id"`
	State stateView `json:"state"`
}

type turnView struct {
	State  stateView   `json:"state"`
	Events []eventView `json:"events"`
}

type configView struct {
	BoardSize int        `json:"boardSize"`
	Fleet     []shipSpec `json:"fleet"`
	Opponents []string   `json:"opponents"`
	Layouts   []string   `json:"layouts"`
}

type heatmapView struct {
	Scorable bool           `json:"scorable"`
	Cells    targeting.Grid `json:"cells"`
}

type stepView struct {
	By   int    `json:"by"`
	At   string `json:"at"`
	Row  int    `json:"row"`
	Col  int    `json:"col"`
	Hit  bool   `json:"hit"`
	Sunk string `json:"sunk,omitempty"`
}

type raceView struct {
	Names  [2]string    `json:"names"`
	Boards [2]boardView `json:"boards"`
	Steps  []stepView   `json:"steps"`
	Winner int          `json:"winner"`
	Shots  [2]int       `json:"shots"`
}

func config() configView {
	c := configView{BoardSize: game.BoardSize}

	for _, t := range game.Fleet {
		c.Fleet = append(c.Fleet, shipSpec{Name: t.Name, Size: t.Size})
	}
	for _, f := range targeting.All {
		c.Opponents = append(c.Opponents, f.Name)
	}
	for _, f := range placement.All {
		c.Layouts = append(c.Layouts, f.Name)
	}

	return c
}

func state(g *match.Game) stateView {
	_, scorable := g.Heatmap()

	v := stateView{
		Opponent: g.Opponent,
		Phase:    string(g.Phase),
		Turn:     g.Turn,
		Over:     g.Over(),
		Scorable: scorable,
		Mine:     board(&g.Mine, true),
		// Fog lifts only once the game is decided — until then the enemy fleet
		// is stripped server-side, so it is not sitting in the network tab.
		Theirs: board(&g.Theirs, g.Over()),
	}

	for _, t := range g.Remaining() {
		v.Remaining = append(v.Remaining, shipSpec{Name: t.Name, Size: t.Size})
	}

	return v
}

// board renders one grid. With reveal false, unhit ship cells read as empty
// water and afloat ships give away nothing but their name and size — the same
// fog game.Board.Render(false) draws for the CLI.
func board(b *game.Board, reveal bool) boardView {
	var v boardView

	sunk := make(map[game.Position]bool)
	for _, s := range b.Ships() {
		if !s.Sunk() {
			continue
		}
		for _, p := range s.Cells {
			sunk[p] = true
		}
	}

	for _, p := range game.AllPositions() {
		v.Cells[p.Row][p.Col] = cell(b.At(p), sunk[p], reveal)
	}

	for _, s := range b.Ships() {
		view := shipView{Name: s.Type.Name, Size: s.Type.Size, Sunk: s.Sunk()}
		if reveal || s.Sunk() {
			view.Hits = s.Hits
			view.Cells = positions(s.Cells)
		}
		v.Ships = append(v.Ships, view)
	}

	return v
}

func cell(c game.Cell, sunk, reveal bool) string {
	switch {
	case c == game.CellHit && sunk:
		return cellSunk
	case c == game.CellHit:
		return cellHit
	case c == game.CellMiss:
		return cellMiss
	case c == game.CellShip && reveal:
		return cellShip
	default:
		return cellEmpty
	}
}

func positions(ps []game.Position) []position {
	out := make([]position, 0, len(ps))
	for _, p := range ps {
		out = append(out, position{Row: p.Row, Col: p.Col})
	}

	return out
}

func events(es []match.Event) []eventView {
	out := make([]eventView, 0, len(es))
	for _, e := range es {
		out = append(out, eventView{
			By:   string(e.By),
			At:   e.At.String(),
			Row:  e.At.Row,
			Col:  e.At.Col,
			Hit:  e.Hit,
			Sunk: e.Sunk,
		})
	}

	return out
}

func race(r *match.Race) raceView {
	v := raceView{Names: r.Names, Winner: r.Winner, Shots: r.Shots}

	for i := range r.Boards {
		v.Boards[i] = board(&r.Boards[i], true)
	}

	for _, s := range r.Steps {
		v.Steps = append(v.Steps, stepView{
			By:   s.By,
			At:   s.At.String(),
			Row:  s.At.Row,
			Col:  s.At.Col,
			Hit:  s.Hit,
			Sunk: s.Sunk,
		})
	}

	return v
}
