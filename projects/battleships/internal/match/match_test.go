package match

import (
	"math/rand/v2"
	"testing"

	"battleships/internal/game"
	"battleships/internal/placement"
	"battleships/internal/targeting"
)

func newGame(t *testing.T) *Game {
	t.Helper()

	g, err := New(targeting.All[0], placement.All[0], rand.New(rand.NewPCG(1, 2)))
	if err != nil {
		t.Fatal(err)
	}

	return g
}

func TestPlacingBlocksFiring(t *testing.T) {
	g := newGame(t)

	if g.Phase != Placing {
		t.Fatalf("phase = %s, want %s", g.Phase, Placing)
	}
	if _, err := g.Fire(game.Position{}); err == nil {
		t.Fatal("fired a shot while still placing")
	}
}

func TestPlaceMineRandomStartsTheGame(t *testing.T) {
	g := newGame(t)

	if err := g.PlaceMineRandom(); err != nil {
		t.Fatal(err)
	}

	if g.Phase != Playing {
		t.Fatalf("phase = %s, want %s", g.Phase, Playing)
	}
	if len(g.Remaining()) != 0 {
		t.Fatalf("%d ships still waiting after a random placement", len(g.Remaining()))
	}
	if g.Turn != 1 {
		t.Fatalf("turn = %d, want 1", g.Turn)
	}
}

func TestPlaceMineOneByOne(t *testing.T) {
	g := newGame(t)

	for row, tp := range game.Fleet {
		if err := g.PlaceMine(tp.Name, game.Position{Row: row}, game.Horizontal); err != nil {
			t.Fatalf("placing %s: %v", tp.Name, err)
		}
	}

	if g.Phase != Playing {
		t.Fatalf("phase = %s, want %s", g.Phase, Playing)
	}
	if err := g.PlaceMine(game.Fleet[0].Name, game.Position{Row: 9}, game.Horizontal); err == nil {
		t.Fatal("placed a ship that was already down")
	}
}

func TestFireRejectsRepeats(t *testing.T) {
	g := newGame(t)
	if err := g.PlaceMineRandom(); err != nil {
		t.Fatal(err)
	}

	p := game.Position{Row: 4, Col: 4}
	if _, err := g.Fire(p); err != nil {
		t.Fatal(err)
	}
	if _, err := g.Fire(p); err == nil {
		t.Fatalf("%v: fired twice at the same cell", p)
	}
	if _, err := g.Fire(game.Position{Row: -1}); err == nil {
		t.Fatal("fired off the board")
	}
}

// A game must always end, and only one side may win.
func TestGamePlaysToAnEnding(t *testing.T) {
	for _, f := range targeting.All {
		t.Run(f.Name, func(t *testing.T) {
			rng := rand.New(rand.NewPCG(7, 11))

			g, err := New(f, placement.All[0], rng)
			if err != nil {
				t.Fatal(err)
			}
			if err := g.PlaceMineRandom(); err != nil {
				t.Fatal(err)
			}

			for _, p := range game.AllPositions() {
				if g.Over() {
					break
				}
				if _, err := g.Fire(p); err != nil {
					t.Fatal(err)
				}
			}

			if !g.Over() {
				t.Fatal("board exhausted without an ending")
			}
			if g.Phase == Won && !g.Theirs.AllSunk() {
				t.Fatal("won without sinking the enemy fleet")
			}
			if g.Phase == Lost && !g.Mine.AllSunk() {
				t.Fatal("lost with ships still afloat")
			}
		})
	}
}

func TestHeatmapOnlyForScorers(t *testing.T) {
	for _, f := range targeting.All {
		g, err := New(f, placement.All[0], rand.New(rand.NewPCG(3, 4)))
		if err != nil {
			t.Fatal(err)
		}

		grid, ok := g.Heatmap()
		_, want := f.New(rand.New(rand.NewPCG(3, 4))).(targeting.Scorer)
		if ok != want {
			t.Fatalf("%s: heatmap available = %v, want %v", f.Name, ok, want)
		}
		if !ok {
			continue
		}

		for _, p := range game.AllPositions() {
			if v := grid[p.Row][p.Col]; v < 0 || v > 1 {
				t.Fatalf("%s: score at %v is %v, want 0..1", f.Name, p, v)
			}
		}
	}
}

func TestRunIsReproducible(t *testing.T) {
	a, b := targeting.All[len(targeting.All)-1], targeting.All[0]

	first, err := Run(a, b, placement.All[0], 99)
	if err != nil {
		t.Fatal(err)
	}
	second, err := Run(a, b, placement.All[0], 99)
	if err != nil {
		t.Fatal(err)
	}

	if first.Winner < 0 {
		t.Fatal("race ended with no winner")
	}
	if first.Shots != second.Shots || len(first.Steps) != len(second.Steps) {
		t.Fatalf("same seed gave different races: %v vs %v", first.Shots, second.Shots)
	}

	for i, s := range first.Steps {
		if s != second.Steps[i] {
			t.Fatalf("step %d: %v vs %v", i, s, second.Steps[i])
		}
	}

	if !first.Boards[1-first.Winner].AllSunk() {
		t.Fatal("the loser's fleet is not sunk")
	}
}
