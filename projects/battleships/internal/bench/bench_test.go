package bench

import (
	"flag"
	"fmt"
	"io"
	"os"
	"testing"
	"text/tabwriter"

	"battleships/internal/placement"
	"battleships/internal/replay"
	"battleships/internal/targeting"
)

var (
	games      = flag.Int("games", 2000, "games per pairing in TestMatrix")
	trace      = flag.Bool("traces", false, "write board-by-board traces to ./traces")
	traceGames = flag.Int("traces.games", 3, "games to trace per pairing")
)

const traceDir = "traces"

type row struct {
	placement, strategy string
	st                  stats
}

var rows []row

func TestMain(m *testing.M) {
	code := m.Run()
	table(os.Stdout)
	os.Exit(code)
}

func record(p, s string, st stats) {
	for i := range rows {
		if rows[i].placement == p && rows[i].strategy == s {
			rows[i].st = st

			return
		}
	}

	rows = append(rows, row{placement: p, strategy: s, st: st})
}

func table(out io.Writer) {
	if len(rows) == 0 {
		return
	}

	w := tabwriter.NewWriter(out, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "\nplacement\tstrategy\tavg\tbest\tworst\tgames")

	prev := ""
	for _, r := range rows {
		if prev != "" && r.placement != prev {
			fmt.Fprintln(w, "\t\t\t\t\t")
		}
		prev = r.placement

		fmt.Fprintf(w, "%s\t%s\t%.1f\t%d\t%d\t%d\n",
			r.placement, r.strategy, r.st.average(), r.st.best, r.st.worst, r.st.played)
	}

	w.Flush()
}

func collect(p placement.Factory, s targeting.Factory, n int) (stats, error) {
	var st stats

	for g := range n {
		shots, err := Play(p, s, g, nil)
		if err != nil {
			return st, fmt.Errorf("%s/%s game %d: %w", p.Name, s.Name, g, err)
		}
		st.record(shots)
	}

	return st, nil
}

func TestMatrix(t *testing.T) {
	if testing.Short() {
		t.Skip("matrix plays every pairing; drop -short to run it")
	}

	for _, p := range placement.All {
		for _, s := range targeting.All {
			st, err := collect(p, s, *games)
			if err != nil {
				t.Fatal(err)
			}
			record(p.Name, s.Name, st)
		}
	}
}

func BenchmarkMatrix(b *testing.B) {
	for _, p := range placement.All {
		for _, s := range targeting.All {
			b.Run(p.Name+"/"+s.Name, func(b *testing.B) {
				var st stats

				for g := 0; b.Loop(); g++ {
					shots, err := Play(p, s, g, nil)
					if err != nil {
						b.Fatal(err)
					}
					st.record(shots)
				}

				b.ReportMetric(st.average(), "shots/game")
				record(p.Name, s.Name, st)
			})
		}
	}
}

func TestTraces(t *testing.T) {
	if !*trace {
		t.Skip("pass -traces to write traces")
	}

	if err := os.RemoveAll(traceDir); err != nil {
		t.Fatal(err)
	}

	for _, p := range placement.All {
		for _, s := range targeting.All {
			for g := range *traceGames {
				rec, err := replay.New(traceDir, p.Name+"-"+s.Name, g)
				if err != nil {
					t.Fatal(err)
				}
				if _, err := Play(p, s, g, rec); err != nil {
					t.Fatalf("%s/%s game %d: %v", p.Name, s.Name, g, err)
				}
			}
		}
	}
}
