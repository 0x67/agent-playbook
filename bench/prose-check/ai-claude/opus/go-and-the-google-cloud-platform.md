# Go and the Google Cloud Platform

Over the past few years, Go has become the default language for new backend services on our team, and Google Cloud has become where most of those services run. The pairing is not an accident. In this post we cover why the combination works well, the patterns we've standardized on, and a few sharp edges we've hit.

## Why the Pairing Works

Go was created at Google, and much of the cloud-native ecosystem is written in it. Kubernetes, the foundation of Google Kubernetes Engine (GKE), is a Go project. That shared lineage shows up in practice:

- **Fast startup, small footprint.** A Go service compiles to a single static binary that starts in milliseconds and idles on a few megabytes of memory. That matters on Cloud Run, where instances scale to zero and cold starts directly affect latency.
- **First-class client libraries.** The `cloud.google.com/go` modules cover nearly every GCP service, including Cloud Storage, Pub/Sub, Firestore, Spanner and BigQuery. They are idiomatic Go and use `context.Context` throughout.
- **Concurrency that fits the platform.** Cloud Run lets one instance serve many concurrent requests. Go's goroutine-per-request model takes advantage of that without extra machinery.

## Pattern 1: A Cloud Run-Friendly Server

Cloud Run tells your container which port to listen on through the `PORT` environment variable. When it scales an instance down, it sends `SIGTERM` and waits about 10 seconds before force-killing the process. Our services handle both:

```go
func main() {
    ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
    defer stop()

    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }

    mux := http.NewServeMux()
    mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    })

    srv := &http.Server{Addr: ":" + port, Handler: mux}
    go func() {
        if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
            log.Fatalf("listen: %v", err)
        }
    }()

    <-ctx.Done()
    shutdownCtx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
    defer cancel()
    if err := srv.Shutdown(shutdownCtx); err != nil {
        log.Printf("shutdown: %v", err)
    }
}
```

The 8-second timeout leaves headroom inside Cloud Run's grace period. During that window, in-flight requests finish and connections close cleanly.

## Pattern 2: Create Clients Once, Authenticate with ADC

GCP client libraries hold connection pools and are safe for concurrent use. Create them once at startup and share them across requests. Creating a new client per request wastes time and connections.

For authentication we rely on Application Default Credentials (ADC). Locally, developers run `gcloud auth application-default login`. In production, the libraries pick up the service account attached to the Cloud Run service or GKE workload. No key files ship in our images.

```go
storageClient, err := storage.NewClient(ctx)
if err != nil {
    log.Fatalf("storage.NewClient: %v", err)
}
defer storageClient.Close()
```

Inside handlers, we always pass `r.Context()` into client calls. If a caller disconnects or a deadline expires, the downstream API call is cancelled too, and it stops consuming quota.

## Pattern 3: Logs Cloud Logging Understands

Cloud Logging parses JSON written to stdout and recognizes special fields like `severity` and `message`. The standard library's `log/slog` gets you there with a small `ReplaceAttr` function:

```go
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
        switch a.Key {
        case slog.MessageKey:
            a.Key = "message"
        case slog.LevelKey:
            a.Key = "severity"
            if lvl, ok := a.Value.Any().(slog.Level); ok && lvl == slog.LevelWarn {
                a.Value = slog.StringValue("WARNING")
            }
        }
        return a
    },
}))
slog.SetDefault(logger)
```

Now log levels show up correctly in the Logs Explorer, and you can filter by severity without any third-party logging library.

## Pattern 4: Small, Boring Images

We build with `CGO_ENABLED=0` and ship on a distroless static base image, or skip the Dockerfile entirely with `ko`. The resulting images are small, pull quickly and contain almost nothing an attacker could use: no shell and no package manager. Smaller images also help with cold starts.

## Sharp Edges

A few lessons we learned the hard way:

- **Background work on Cloud Run.** With request-based billing, CPU is throttled once a response is sent. A goroutine that keeps working after the handler returns may stall indefinitely. Either switch to instance-based billing or hand the work off to Cloud Tasks or Pub/Sub.
- **GOMAXPROCS in containers.** Starting with Go 1.25, the runtime respects cgroup CPU limits on Linux. On older versions, Go may assume it has every core on the host. That leads to excess scheduling overhead, which `go.uber.org/automaxprocs` fixes.
- **Database connection math.** Cloud Run can scale out quickly. Fifty instances with a default unbounded `database/sql` pool can exhaust a Cloud SQL instance's connection limit. Set `SetMaxOpenConns` deliberately, based on your maximum instance count.

## Wrapping Up

Go and GCP reward simplicity: a static binary, a handful of environment variables, structured logs on stdout and credentials the platform provides for you. Most of our services follow the patterns above almost verbatim, and that consistency has made them easy to operate and easy for new engineers to pick up. If you're starting a new service on Google Cloud, Go is a strong default.
