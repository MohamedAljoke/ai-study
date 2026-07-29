package web

import (
	"crypto/rand"
	"encoding/hex"
	"sync"
	"time"

	"battleships/internal/match"
)

// session wraps one game with its own lock. Targeting strategies carry mutable
// state and an *rand.Rand, so a game is handled by one request at a time.
type session struct {
	mu   sync.Mutex
	game *match.Game
	seen time.Time
}

// store keeps games in memory, keyed by an opaque id handed to the browser in
// a cookie. Nothing is persisted: a restart loses every game in progress,
// which is the right trade for a single-player game against a local AI.
type store struct {
	mu       sync.Mutex
	sessions map[string]*session
	idle     time.Duration
}

func newStore(idle time.Duration) *store {
	if idle <= 0 {
		idle = 30 * time.Minute
	}

	return &store{sessions: make(map[string]*session), idle: idle}
}

func (s *store) add(g *match.Game) (string, *session) {
	sess := &session{game: g, seen: time.Now()}

	s.mu.Lock()
	defer s.mu.Unlock()

	id := newID()
	s.sessions[id] = sess

	return id, sess
}

// get returns the session and marks it alive, so a game being played is never
// swept out from under the player.
func (s *store) get(id string) (*session, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	sess, ok := s.sessions[id]
	if ok {
		sess.seen = time.Now()
	}

	return sess, ok
}

func (s *store) drop(id string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	delete(s.sessions, id)
}

// sweep evicts games nobody has touched in a while. Without it the map only
// ever grows, which is a problem the moment this runs somewhere with a memory
// limit rather than on a laptop.
func (s *store) sweep(now time.Time) int {
	s.mu.Lock()
	defer s.mu.Unlock()

	dropped := 0
	for id, sess := range s.sessions {
		if now.Sub(sess.seen) > s.idle {
			delete(s.sessions, id)
			dropped++
		}
	}

	return dropped
}

func (s *store) janitor(stop <-chan struct{}) {
	tick := time.NewTicker(min(s.idle, time.Minute))
	defer tick.Stop()

	for {
		select {
		case now := <-tick.C:
			s.sweep(now)
		case <-stop:
			return
		}
	}
}

func (s *store) len() int {
	s.mu.Lock()
	defer s.mu.Unlock()

	return len(s.sessions)
}

func newID() string {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		panic("crypto/rand failed: " + err.Error())
	}

	return hex.EncodeToString(b[:])
}
