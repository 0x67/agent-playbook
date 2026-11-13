# Gobs of data

Every system eventually has to answer a deceptively simple question: how do we turn what's in memory into bytes, and back again? For most of our history, the answer was JSON. It's readable, universal, and every engineer on the team already knows it. But last quarter, while chasing latency in our internal job scheduler, we found ourselves spending more CPU on `json.Marshal` than on actual scheduling. That led us to a less famous corner of the Go standard library: `encoding/gob`.

This post covers what we learned, including the good, the surprising, and where we decided gob doesn't belong.

## What gob actually is

Gob is Go's native binary serialization format. It does one job: moving Go values between Go programs. There's no schema file, no code generation step, and no struct tags to maintain. You give it a value and it handles the rest.

```go
type Snapshot struct {
    AccountID string
    Balances  map[string]int64
    UpdatedAt time.Time
}

var buf bytes.Buffer
if err := gob.NewEncoder(&buf).Encode(snap); err != nil {
    return err
}
```

Gob is a self-describing stream. The first time an encoder sees a type, it sends a description of that type. After that, values of that type are sent compactly: integers are varint-encoded and zero-valued fields are omitted entirely. The decoder matches fields by name, not position, which matters a lot (more on that below). Our title comes from Rob Pike's 2011 Go blog post introducing the package, which is still the best explanation of its design.

## Why it fit our problem

The scheduler's workers stream task results back to a coordinator over long-lived TCP connections. Both sides are written in Go, both deploy from the same repository, and nobody outside the service ever reads these messages. That's close to the ideal gob use case:

- **No schema ceremony.** Our task result types change often. With gob, the struct definition *is* the schema.
- **Smaller payloads.** Field names go over the wire once per stream, not once per message as they do with JSON.
- **Real types.** `time.Time`, `[]byte`, and maps with non-string keys round-trip without custom marshaling code or base64 detours.

After the switch, payloads shrank. Serialization dropped off the top of the coordinator's CPU profile.

## The mistake we made first

Our first implementation was actually *slower* than JSON. The culprit:

```go
// Don't do this
func send(conn net.Conn, r Result) error {
    return gob.NewEncoder(conn).Encode(r)
}
```

A fresh encoder per message re-sends the full type description with every value. Gob gets its efficiency by spreading that one-time cost across a whole stream, so the encoder needs to live as long as the connection:

```go
type sender struct {
    enc *gob.Encoder
}

func newSender(conn net.Conn) *sender {
    return &sender{enc: gob.NewEncoder(conn)}
}

func (s *sender) send(r Result) error {
    return s.enc.Encode(r)
}
```

The same rule applies on the receiving side: one decoder per stream. If you store individual gob blobs in a cache or database, each value is decoded on its own and pays the type-description cost every time. Gob's size advantage mostly disappears in that case, so benchmark before you commit.

## Schema evolution: friendly, with sharp edges

Because gob matches fields by name, it forgives some changes. If the sender adds a field, old receivers ignore it. If the sender removes a field, new receivers leave it at its zero value. That made rolling deploys painless.

The sharp edge is the same rule seen from the other side. During a cleanup, one of our engineers renamed `RetryCount` to `Attempts`, and nothing failed. The decoder saw one unknown field and one missing field, and it quietly zeroed the retry counter on half the fleet mid-deploy. Changing a field's *type* incompatibly, on the other hand, fails loudly with a decode error. We now consider that the better outcome.

Our rules now:

1. Treat exported field names on wire types as a public API. A rename requires a two-step deploy.
2. Keep wire types in their own package, separate from domain models, so refactors don't accidentally touch them.
3. Whenever an interface field is involved, register the concrete types with `gob.Register`. Do it in `init` so every binary agrees.

## Where we don't use gob

Gob is Go-only, and that's the whole trade. Anything that crosses a language boundary, is stored long-term, or needs a contract reviewed by another team still uses Protocol Buffers. Anything a human might need to read in a log or debug endpoint stays JSON.

Gob earned its place for one specific problem: Go talking to Go, inside a single deployment unit, over a stream. For that, it's hard to beat a serializer that's already in the standard library and asks nothing of you but a struct.

Sometimes the right tool has been sitting in `$GOROOT` the whole time.
