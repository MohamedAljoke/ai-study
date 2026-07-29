package main

import (
	"flag"
	"log"
	"net/http"
	"strings"
	"time"

	"battleships/internal/web"
)

func main() {
	addr := flag.String("addr", ":8080", "HTTP listen address")
	idle := flag.Duration("idle", 30*time.Minute, "idle session lifetime")
	flag.Parse()

	srv, err := web.New(*idle)
	if err != nil {
		log.Fatal(err)
	}
	defer srv.Close()

	shown := *addr
	if strings.HasPrefix(shown, ":") {
		shown = "localhost" + shown
	}
	log.Printf("serving battleships on http://%s", shown)
	log.Fatal(http.ListenAndServe(*addr, srv))
}
