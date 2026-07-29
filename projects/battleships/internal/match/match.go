// Package match runs a two-sided game — you against a targeting strategy —
// with no I/O of its own. The CLI prints it, the web server serializes it, and
// neither owns the rules.
package match

import (
	"fmt"
	"math/rand/v2"

	"battleships/internal/game"
	"battleships/internal/placement"
	"battleships/internal/targeting"
)

type Phase string

const (
	Placing Phase = "placing"
	Playing Phase = "playing"
	Won     Phase = "won"
	Lost    Phase = "lost"
)

// Side says who fired a shot.
type Side string

const (
	You Side = "you"
	AI  Side = "ai"
)

// Event is one shot and what it did.
type Event struct {
	By   Side
	At   game.Position
	Hit  bool
	Sunk string // ship name, empty unless the shot sank one
}

type Game struct {
	Mine   game.Board
	Theirs game.Board

	Opponent string
	Phase    Phase
	Turn     int

	ai  targeting.Strategy
	rng *rand.Rand
}

// New sets up the enemy fleet and the strategy that will hunt yours. Your own
// board starts empty: the game sits in Placing until every ship is down.
func New(opponent targeting.Factory, layout placement.Factory, rng *rand.Rand) (*Game, error) {
	g := &Game{
		Opponent: opponent.Name,
		Phase:    Placing,
		ai:       opponent.New(rng),
		rng:      rng,
	}

	if err := layout.Place(&g.Theirs, game.Fleet, rng); err != nil {
		return nil, fmt.Errorf("placing the enemy fleet: %w", err)
	}

	return g, nil
}

// Remaining lists the ships you still have to place, in fleet order.
func (g *Game) Remaining() []game.ShipType {
	placed := make(map[string]bool, len(game.Fleet))
	for _, s := range g.Mine.Ships() {
		placed[s.Type.Name] = true
	}

	var left []game.ShipType
	for _, t := range game.Fleet {
		if !placed[t.Name] {
			left = append(left, t)
		}
	}

	return left
}

// PlaceMine puts one of your ships down. The last ship starts the game.
func (g *Game) PlaceMine(name string, origin game.Position, o game.Orientation) error {
	if g.Phase != Placing {
		return fmt.Errorf("cannot place ships once the game has started")
	}

	t, err := g.waiting(name)
	if err != nil {
		return err
	}

	if _, err := g.Mine.Place(t, origin, o); err != nil {
		return err
	}

	g.start()

	return nil
}

// PlaceMineRandom drops every ship you have not placed yet, the way the CLI's
// "r" shortcut does.
func (g *Game) PlaceMineRandom() error {
	if g.Phase != Placing {
		return fmt.Errorf("cannot place ships once the game has started")
	}

	left := g.Remaining()
	if len(left) == 0 {
		return nil
	}

	if err := placement.Uniform(&g.Mine, left, g.rng); err != nil {
		return err
	}

	g.start()

	return nil
}

func (g *Game) waiting(name string) (game.ShipType, error) {
	for _, t := range g.Remaining() {
		if t.Name == name {
			return t, nil
		}
	}

	return game.ShipType{}, fmt.Errorf("%q: not a ship still waiting to be placed", name)
}

func (g *Game) start() {
	if len(g.Remaining()) == 0 {
		g.Phase = Playing
		g.Turn = 1
	}
}

// Fire takes your shot and, unless it ended the game, the AI's reply. Both
// come back in one call because a turn is the pair — splitting them would only
// hand callers a half-finished turn to render.
func (g *Game) Fire(p game.Position) ([]Event, error) {
	if g.Phase != Playing {
		return nil, fmt.Errorf("no shots to take: the game is %s", g.Phase)
	}

	if !p.Valid() {
		return nil, fmt.Errorf("invalid position: %v", p)
	}
	if g.Theirs.At(p).Shot() {
		return nil, fmt.Errorf("%v: already fired at", p)
	}

	res, err := g.Theirs.Fire(p)
	if err != nil {
		return nil, err
	}

	events := []Event{event(You, p, res)}

	if g.Theirs.AllSunk() {
		g.Phase = Won

		return events, nil
	}

	q := g.ai.Next()

	res, err = g.Mine.Fire(q)
	if err != nil {
		return nil, fmt.Errorf("the %s strategy fired at %v: %w", g.Opponent, q, err)
	}
	g.ai.Observe(q, res)

	events = append(events, event(AI, q, res))

	if g.Mine.AllSunk() {
		g.Phase = Lost

		return events, nil
	}

	g.Turn++

	return events, nil
}

// Heatmap is the AI's current ranking of your board — where it believes your
// ships are. Not every strategy has an opinion worth showing, so the second
// return says whether this one does.
func (g *Game) Heatmap() (targeting.Grid, bool) {
	s, ok := g.ai.(targeting.Scorer)
	if !ok {
		return targeting.Grid{}, false
	}

	return s.Scores(), true
}

// Over reports whether the game has finished either way.
func (g *Game) Over() bool {
	return g.Phase == Won || g.Phase == Lost
}

func event(by Side, p game.Position, r game.Result) Event {
	e := Event{By: by, At: p, Hit: r.Hit}
	if r.Sunk != nil {
		e.Sunk = r.Sunk.Type.Name
	}

	return e
}
