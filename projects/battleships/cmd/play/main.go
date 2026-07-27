package main

import (
	"bufio"
	"fmt"
	"io"
	"log"
	"math/rand/v2"
	"os"
	"strconv"
	"strings"

	"battleships/internal/game"
	"battleships/internal/placement"
	"battleships/internal/targeting"
)

func main() {
	in := bufio.NewScanner(os.Stdin)
	rng := rand.New(rand.NewPCG(rand.Uint64(), rand.Uint64()))

	f, err := chooseOpponent(in)
	if err != nil {
		log.Fatal(err)
	}

	var mine, theirs game.Board
	if err := placeFleet(in, &mine, rng); err != nil {
		log.Fatal(err)
	}
	if err := placement.Uniform(&theirs, game.Fleet, rng); err != nil {
		log.Fatal(err)
	}

	if err := run(in, f.New(rng), &mine, &theirs); err != nil {
		log.Fatal(err)
	}
}

func chooseOpponent(in *bufio.Scanner) (targeting.Factory, error) {
	fmt.Println("Choose your opponent:")
	for i, f := range targeting.All {
		fmt.Printf("  %d) %s\n", i+1, f.Name)
	}

	for {
		line, err := prompt(in, "> ")
		if err != nil {
			return targeting.Factory{}, err
		}

		for _, f := range targeting.All {
			if strings.EqualFold(line, f.Name) {
				return f, nil
			}
		}
		if n, err := strconv.Atoi(line); err == nil && n >= 1 && n <= len(targeting.All) {
			return targeting.All[n-1], nil
		}

		fmt.Println("no such opponent")
	}
}

func placeFleet(in *bufio.Scanner, b *game.Board, rng *rand.Rand) error {
	fmt.Println("\nPlace your fleet: an origin and an orientation, like \"A0 h\".")
	fmt.Println("Enter \"r\" to place everything still waiting at random.")

	for i, t := range game.Fleet {
		for {
			fmt.Printf("\n%s\n", b)

			line, err := prompt(in, "%s (%d) > ", t.Name, t.Size)
			if err != nil {
				return err
			}
			if strings.EqualFold(line, "r") {
				return placement.Uniform(b, game.Fleet[i:], rng)
			}

			origin, o, err := parsePlacement(line)
			if err == nil {
				_, err = b.Place(t, origin, o)
			}
			if err != nil {
				fmt.Println(err)

				continue
			}

			break
		}
	}

	return nil
}

func parsePlacement(line string) (game.Position, game.Orientation, error) {
	fields := strings.Fields(line)
	if len(fields) != 2 {
		return game.Position{}, "", fmt.Errorf("%q: want a position and an orientation, like \"A0 h\"", line)
	}

	origin, err := game.ParsePosition(fields[0])
	if err != nil {
		return game.Position{}, "", err
	}

	o, err := game.ParseOrientation(fields[1])
	if err != nil {
		return game.Position{}, "", err
	}

	return origin, o, nil
}

func run(in *bufio.Scanner, ai targeting.Strategy, mine, theirs *game.Board) error {
	for turn := 1; ; turn++ {
		fmt.Printf("\n%s", boards(mine, theirs))

		p, err := askShot(in, theirs)
		if err != nil {
			return err
		}

		res, err := theirs.Fire(p)
		if err != nil {
			return err
		}
		fmt.Printf("You fire at %v: %s\n", p, describe(res))

		if theirs.AllSunk() {
			fmt.Printf("\n%s\nYou win on turn %d.\n", boards(mine, theirs), turn)

			return nil
		}

		q := ai.Next()

		res, err = mine.Fire(q)
		if err != nil {
			return err
		}
		ai.Observe(q, res)
		fmt.Printf("They fire at %v: %s\n", q, describe(res))

		if mine.AllSunk() {
			fmt.Printf("\n%s\nYou lose on turn %d.\n", boards(mine, theirs), turn)

			return nil
		}
	}
}

func askShot(in *bufio.Scanner, theirs *game.Board) (game.Position, error) {
	for {
		line, err := prompt(in, "your shot > ")
		if err != nil {
			return game.Position{}, err
		}

		p, err := game.ParsePosition(line)
		if err != nil {
			fmt.Println(err)

			continue
		}
		if theirs.At(p).Shot() {
			fmt.Printf("%v: already fired at\n", p)

			continue
		}

		return p, nil
	}
}

// boards draws both grids side by side: yours with the ships showing, theirs
// under fog, so the only thing you learn about their fleet is what you shot.
func boards(mine, theirs *game.Board) string {
	left := strings.Split(strings.TrimRight(mine.Render(true), "\n"), "\n")
	right := strings.Split(strings.TrimRight(theirs.Render(false), "\n"), "\n")
	width := len(left[0])

	var sb strings.Builder
	fmt.Fprintf(&sb, "%-*s   %s\n", width, "YOUR FLEET", "ENEMY WATERS")
	for i := range left {
		fmt.Fprintf(&sb, "%-*s   %s\n", width, left[i], right[i])
	}

	return sb.String()
}

func describe(r game.Result) string {
	switch {
	case r.Sunk != nil:
		return "hit, sank the " + r.Sunk.Type.Name
	case r.Hit:
		return "hit"
	default:
		return "miss"
	}
}

func prompt(in *bufio.Scanner, format string, args ...any) (string, error) {
	fmt.Printf(format, args...)

	if !in.Scan() {
		if err := in.Err(); err != nil {
			return "", err
		}

		return "", io.EOF
	}

	return strings.TrimSpace(in.Text()), nil
}
