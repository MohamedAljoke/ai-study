package replay

import (
	"battleships/internal/game"
	"fmt"
	"os"
	"path/filepath"
)

type Recorder struct {
	dir  string
	step int
}

func New(root, strategy string, gameIdx int) (*Recorder, error) {
	dir := filepath.Join(root, strategy, fmt.Sprintf("game-%04d", gameIdx))
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, fmt.Errorf("creating trace dir: %w", err)
	}

	return &Recorder{dir: dir}, nil
}

func (r *Recorder) Snapshot(b *game.Board, header string) error {
	if r == nil {
		return nil
	}

	name := filepath.Join(r.dir, fmt.Sprintf("step-%03d.txt", r.step))
	if err := os.WriteFile(name, []byte(header+"\n\n"+b.String()), 0o644); err != nil {
		return fmt.Errorf("writing snapshot: %w", err)
	}
	r.step++

	return nil
}
