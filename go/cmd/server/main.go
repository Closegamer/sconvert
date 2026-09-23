package main

import (
	"context"
	"embed"
	"io/fs"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"

	"sconvert/internal/stats"
	"sconvert/internal/web"
)

//go:embed all:static
var staticFS embed.FS

func main() {
	addr := ":8080"
	if v := os.Getenv("ADDR"); v != "" {
		addr = v
	}

	staticSub, err := fs.Sub(staticFS, "static")
	if err != nil {
		log.Fatalf("static assets: %v", err)
	}

	store := stats.New(newPgPool())

	mux := http.NewServeMux()
	mux.Handle("GET /static/", http.StripPrefix("/static/", http.FileServerFS(staticSub)))
	mux.HandleFunc("GET /healthz", handleHealthz)
	mux.HandleFunc("GET /{$}", web.HomeHandler(store))
	mux.HandleFunc("GET /units", web.UnitsHandler(store))
	mux.HandleFunc("POST /api/stats/hit", web.StatsHitHandler(store))

	registerAdmin(mux, store)

	log.Printf("sconvert-go listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatal(err)
	}
}

// registerAdmin mounts the stats dashboard only if ADMIN_PATH is set — no
// env var, no route, so it's off by default rather than reachable at a
// guessable default path. ADMIN_PATH itself must never be committed to
// source control (this is a public repo); set it in the server's .env.
// The path alone is not real security (referrers/logs/history can leak
// it), so Basic Auth (ADMIN_USER/ADMIN_PASSWORD) is required in addition.
func registerAdmin(mux *http.ServeMux, store *stats.Store) {
	path := os.Getenv("ADMIN_PATH")
	if path == "" {
		return
	}
	user := os.Getenv("ADMIN_USER")
	pass := os.Getenv("ADMIN_PASSWORD")
	if user == "" || pass == "" {
		log.Printf("admin: ADMIN_PATH is set but ADMIN_USER/ADMIN_PASSWORD are missing — admin route disabled")
		return
	}
	route := "GET /" + path
	mux.HandleFunc(route, web.BasicAuth(user, pass, web.AdminStatsHandler(store)))
	log.Printf("admin: stats dashboard mounted (path length %d)", len(path))
}

// newPgPool never fails hard: if DATABASE_URL is unset/unreachable the
// stats store degrades to a no-op (popularity ranking falls back to the
// default category order, /api/stats/hit becomes a silent no-op — see
// stats.Store).
func newPgPool() *pgxpool.Pool {
	url := os.Getenv("DATABASE_URL")
	if url == "" {
		url = "postgres://sconvert:sconvert@db:5432/sconvert"
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		log.Printf("postgres: invalid DATABASE_URL, stats disabled: %v", err)
		return nil
	}
	if err := pool.Ping(ctx); err != nil {
		log.Printf("postgres: unreachable at startup, stats disabled until it recovers: %v", err)
	}
	return pool
}

func handleHealthz(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("ok"))
}
