# Go and the Google Cloud Platform

When we started moving our backend services to Google Cloud Platform (GCP), Go was already the language most of our teams reached for. What surprised us was how well the two fit together. Over the past few years we've run Go on Cloud Run, GKE, and Cloud Functions, and the combination has consistently made our systems simpler, cheaper, and easier to operate. This post covers what's worked well, what hasn't, and the practices we'd recommend to teams starting out.

## Why Go fits the cloud so well

Go's strengths line up neatly with what cloud-native workloads need.

**Small, static binaries.** A Go service compiles to a single binary with no runtime to install. Paired with a `scratch` or distroless base image, our container images are often under 20 MB. Smaller images mean faster pulls, faster deploys, and a smaller attack surface.

**Fast startup.** On Cloud Run, cold starts matter. Go services typically begin accepting requests in tens of milliseconds, which lets us scale to zero without users noticing. Compare that with JVM-based services that we've had to keep warm with minimum instances.

**Predictable resource use.** Go's garbage collector and goroutine scheduler give us low, steady memory footprints. We routinely run services in 256 MB containers with headroom to spare, which directly reduces our bill.

**Concurrency as a default.** Fan-out calls to Pub/Sub, Spanner, and Cloud Storage are natural with goroutines and `errgroup`. We rarely need to reach for an external framework to do concurrent work well.

## The client libraries

Google maintains first-class Go client libraries under `cloud.google.com/go`. They're idiomatic, context-aware, and cover nearly every service we use: Pub/Sub, Cloud Storage, Spanner, Firestore, BigQuery, and Secret Manager.

A few habits have saved us trouble:

- **Create clients once.** Clients are safe for concurrent use and hold connection pools. Build them at startup and share them, rather than constructing one per request.
- **Always pass a `context.Context`.** Deadlines and cancellation propagate through the libraries, so a canceled inbound request stops downstream work too.
- **Rely on Application Default Credentials.** Locally we use `gcloud auth application-default login`; in production the attached service account is picked up automatically. No key files in the repo or the image.

```go
ctx := context.Background()
client, err := pubsub.NewClient(ctx, projectID)
if err != nil {
    log.Fatalf("pubsub client: %v", err)
}
defer client.Close()
```

## Running Go on Cloud Run

Cloud Run has become our default for stateless HTTP and gRPC services. The contract is simple: listen on the port in the `PORT` environment variable and handle `SIGTERM` gracefully.

```go
srv := &http.Server{Addr: ":" + port, Handler: mux}
go func() { _ = srv.ListenAndServe() }()

<-ctx.Done() // canceled via signal.NotifyContext on SIGTERM
shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()
_ = srv.Shutdown(shutdownCtx)
```

Graceful shutdown is worth the few extra lines. Without it, in-flight requests get dropped during revisions and scale-down events.

We also tune concurrency per instance. Go handles many simultaneous requests well, so raising Cloud Run's concurrency setting from the default often cuts instance counts significantly. We load test to find the point where latency starts to degrade, then set it just below that.

## Observability

Cloud Logging parses structured JSON on stdout, so we use `log/slog` with a JSON handler and map field names to what GCP expects (`severity`, `message`, and the trace field). That gives us correlated logs and traces with almost no setup. For tracing and metrics, OpenTelemetry with the Google Cloud exporters has worked well and keeps us vendor-neutral in application code.

We also use Cloud Profiler's Go agent in production. Continuous profiling has caught several allocation hot spots that never showed up in tests.

## Where we hit friction

It hasn't all been smooth. A few lessons:

- **CPU throttling.** On Cloud Run, CPU is throttled outside of request handling by default. Background goroutines can stall unless you configure CPU to be always allocated.
- **Container awareness.** Set `GOMEMLIMIT` relative to your container's memory limit so the garbage collector responds before the instance is killed for running out of memory.
- **Dependency weight.** The Google Cloud libraries pull in a sizable dependency tree. Build times and binary sizes grow, so we use build caching and keep an eye on what each service imports.

## Recommendations

If you're starting a Go project on GCP, we'd suggest:

1. Begin with Cloud Run and move to GKE only when you need its control.
2. Use Application Default Credentials and dedicated service accounts per service.
3. Emit structured logs from day one.
4. Handle shutdown signals and set `GOMEMLIMIT`.
5. Load test to tune concurrency before guessing.

Go's simplicity and GCP's managed services complement each other well. The result is services that are easy to reason about, inexpensive to run, and quick to ship. We expect to keep building this way for the foreseeable future.
