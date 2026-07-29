// Package web serves the browser front end and the JSON API behind it. The
// server is authoritative: it owns both boards and the strategy instance, and
// the browser only ever asks it to do things and redraws the answer.
package web

import (
	"embed"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"log"
	"math/rand/v2"
	"net/http"
	"strings"
	"time"

	"battleships/internal/game"
	"battleships/internal/match"
	"battleships/internal/placement"
	"battleships/internal/targeting"
)

//go:embed static
var assets embed.FS

const (
	cookieName = "battleships_session"
	maxBody    = 1 << 16
)

type Server struct {
	mux   *http.ServeMux
	store *store
	stop  chan struct{}
}

// New wires the routes. idle is how long an untouched game survives before the
// janitor collects it.
func New(idle time.Duration) (*Server, error) {
	static, err := fs.Sub(assets, "static")
	if err != nil {
		return nil, fmt.Errorf("reading embedded assets: %w", err)
	}

	s := &Server{
		mux:   http.NewServeMux(),
		store: newStore(idle),
		stop:  make(chan struct{}),
	}

	s.mux.Handle("GET /static/", http.StripPrefix("/static/", http.FileServerFS(static)))
	s.mux.HandleFunc("GET /{$}", s.index)
	s.mux.HandleFunc("GET /api/config", s.config)
	s.mux.HandleFunc("POST /api/game", s.newGame)
	s.mux.HandleFunc("GET /api/game", s.showGame)
	s.mux.HandleFunc("GET /api/game/{id}", s.showGame)
	s.mux.HandleFunc("POST /api/game/fire", s.fire)
	s.mux.HandleFunc("POST /api/game/{id}/fire", s.fire)
	s.mux.HandleFunc("GET /api/game/heatmap", s.heatmap)
	s.mux.HandleFunc("GET /api/game/{id}/heatmap", s.heatmap)
	s.mux.HandleFunc("POST /api/watch", s.watch)

	go s.store.janitor(s.stop)

	return s, nil
}

func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	s.mux.ServeHTTP(w, r)
}

// Close stops the janitor. Games are in memory only, so there is nothing else
// to wind down.
func (s *Server) Close() error {
	close(s.stop)

	return nil
}

func (s *Server) index(w http.ResponseWriter, r *http.Request) {
	page, err := assets.ReadFile("static/index.html")
	if err != nil {
		fail(w, http.StatusInternalServerError, err)

		return
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Write(page)
}

func (s *Server) config(w http.ResponseWriter, r *http.Request) {
	send(w, http.StatusOK, config())
}

type newGameRequest struct {
	Opponent string `json:"opponent"`
	Layout   string `json:"layout"`
	Ships    []struct {
		Name        string `json:"name"`
		Row         int    `json:"row"`
		Col         int    `json:"col"`
		Orientation string `json:"orientation"`
	} `json:"ships"`
	Random bool `json:"random"`
}

func (s *Server) newGame(w http.ResponseWriter, r *http.Request) {
	var req newGameRequest
	if err := decode(r, &req); err != nil {
		fail(w, http.StatusBadRequest, err)

		return
	}

	opponent, err := opponentNamed(req.Opponent)
	if err != nil {
		fail(w, http.StatusBadRequest, err)

		return
	}

	layout, err := layoutNamed(req.Layout)
	if err != nil {
		fail(w, http.StatusBadRequest, err)

		return
	}

	g, err := match.New(opponent, layout, newRNG())
	if err != nil {
		fail(w, http.StatusInternalServerError, err)

		return
	}

	// Every placement the browser sends is re-checked here through
	// game.Board.Place, so the drag preview is a convenience and never the
	// thing deciding whether a layout is legal.
	for _, sh := range req.Ships {
		o, err := game.ParseOrientation(sh.Orientation)
		if err != nil {
			fail(w, http.StatusBadRequest, err)

			return
		}
		if err := g.PlaceMine(sh.Name, game.Position{Row: sh.Row, Col: sh.Col}, o); err != nil {
			fail(w, http.StatusBadRequest, err)

			return
		}
	}

	if req.Random {
		if err := g.PlaceMineRandom(); err != nil {
			fail(w, http.StatusInternalServerError, err)

			return
		}
	}

	if len(g.Remaining()) > 0 {
		fail(w, http.StatusBadRequest, fmt.Errorf("%d ships were not placed", len(g.Remaining())))

		return
	}

	id, _ := s.store.add(g)
	http.SetCookie(w, &http.Cookie{
		Name:     cookieName,
		Value:    id,
		Path:     "/",
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})

	send(w, http.StatusOK, gameCreatedView{ID: id, State: state(g)})
}

func (s *Server) showGame(w http.ResponseWriter, r *http.Request) {
	sess, ok := s.current(w, r)
	if !ok {
		return
	}

	sess.mu.Lock()
	defer sess.mu.Unlock()

	send(w, http.StatusOK, state(sess.game))
}

func (s *Server) fire(w http.ResponseWriter, r *http.Request) {
	var shot position
	if err := decode(r, &shot); err != nil {
		fail(w, http.StatusBadRequest, err)

		return
	}

	sess, ok := s.current(w, r)
	if !ok {
		return
	}

	sess.mu.Lock()
	defer sess.mu.Unlock()

	es, err := sess.game.Fire(game.Position{Row: shot.Row, Col: shot.Col})
	if err != nil {
		fail(w, http.StatusBadRequest, err)

		return
	}

	send(w, http.StatusOK, turnView{State: state(sess.game), Events: events(es)})
}

func (s *Server) heatmap(w http.ResponseWriter, r *http.Request) {
	sess, ok := s.current(w, r)
	if !ok {
		return
	}

	sess.mu.Lock()
	defer sess.mu.Unlock()

	// Only ever the AI's read on your own board. Scoring the enemy board would
	// hand the player the answer.
	cells, scorable := sess.game.Heatmap()

	send(w, http.StatusOK, heatmapView{Scorable: scorable, Cells: cells})
}

type watchRequest struct {
	A      string `json:"a"`
	B      string `json:"b"`
	Layout string `json:"layout"`
	Seed   uint64 `json:"seed"`
}

func (s *Server) watch(w http.ResponseWriter, r *http.Request) {
	var req watchRequest
	if err := decode(r, &req); err != nil {
		fail(w, http.StatusBadRequest, err)

		return
	}

	a, err := opponentNamed(req.A)
	if err != nil {
		fail(w, http.StatusBadRequest, err)

		return
	}

	b, err := opponentNamed(req.B)
	if err != nil {
		fail(w, http.StatusBadRequest, err)

		return
	}

	layout, err := layoutNamed(req.Layout)
	if err != nil {
		fail(w, http.StatusBadRequest, err)

		return
	}

	// The whole race is played here and shipped in one response. A finished
	// game is a couple of hundred steps, and having it all client-side is what
	// lets the scrubber run backwards.
	result, err := match.Run(a, b, layout, req.Seed)
	if err != nil {
		fail(w, http.StatusInternalServerError, err)

		return
	}

	send(w, http.StatusOK, race(result))
}

// current resolves the session cookie, answering 404 and clearing the cookie
// when the game is gone so the browser can say "expired" instead of showing a
// bare error.
func (s *Server) current(w http.ResponseWriter, r *http.Request) (*session, bool) {
	id := r.PathValue("id")
	if id == "" {
		c, err := r.Cookie(cookieName)
		if err != nil {
			fail(w, http.StatusNotFound, errors.New("no game in progress"))

			return nil, false
		}
		id = c.Value
	}

	sess, ok := s.store.get(id)
	if !ok {
		http.SetCookie(w, &http.Cookie{Name: cookieName, Path: "/", MaxAge: -1})
		fail(w, http.StatusNotFound, errors.New("your game expired"))

		return nil, false
	}

	return sess, true
}

func opponentNamed(name string) (targeting.Factory, error) {
	for _, f := range targeting.All {
		if strings.EqualFold(name, f.Name) {
			return f, nil
		}
	}

	return targeting.Factory{}, fmt.Errorf("%q: no such opponent", name)
}

func layoutNamed(name string) (placement.Factory, error) {
	if name == "" {
		return placement.All[0], nil
	}

	for _, f := range placement.All {
		if strings.EqualFold(name, f.Name) {
			return f, nil
		}
	}

	return placement.Factory{}, fmt.Errorf("%q: no such layout", name)
}

func newRNG() *rand.Rand {
	return rand.New(rand.NewPCG(rand.Uint64(), rand.Uint64()))
}

func decode(r *http.Request, v any) error {
	dec := json.NewDecoder(http.MaxBytesReader(nil, r.Body, maxBody))
	dec.DisallowUnknownFields()

	if err := dec.Decode(v); err != nil {
		return fmt.Errorf("reading the request: %w", err)
	}

	return nil
}

func send(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)

	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("writing response: %v", err)
	}
}

func fail(w http.ResponseWriter, code int, err error) {
	send(w, code, map[string]string{"error": err.Error()})
}
