# Automatic cipher suite ordering in crypto/tls

For years, configuring TLS meant copying a long list of cipher suite names from a blog post, a compliance checklist, or a generator site and pasting it into the server config. These lists aged badly. Each new attack meant someone had to update them by hand, and most never got updated. Go's `crypto/tls` package now takes a different approach: since Go 1.17, it decides cipher suite order for you.

This post explains what changed, how the ordering works, and what it means for your services.

## What ordering actually controls

During a TLS 1.0–1.2 handshake, the client sends a list of cipher suites it supports. The server picks one. The suite determines the key exchange (ECDHE or static RSA), the bulk cipher (AES-GCM, ChaCha20-Poly1305, AES-CBC, 3DES), and the MAC.

When both sides support several suites, something has to break the tie. Historically you had two options:

- **Client preference**: honor the client's order.
- **Server preference**: honor the server's order. In Go this was `Config.PreferServerCipherSuites`.

Either way, *somebody* had to maintain an ordered list, and that list encoded security judgments that went stale.

## What changed

Starting in Go 1.17:

- `Config.PreferServerCipherSuites` is ignored and deprecated.
- `Config.CipherSuites` still controls **which** TLS 1.0–1.2 suites are enabled, but its **order** is ignored.
- `crypto/tls` applies a built-in preference order that takes hardware capabilities into account.

TLS 1.3 suites were already not configurable, and they follow the same automatic logic.

## How Go ranks suites

The built-in order follows a few rules, roughly in priority:

1. **AEADs beat CBC.** AES-GCM and ChaCha20-Poly1305 come before any CBC-mode suite, because CBC constructions have a long history of padding-oracle and timing attacks.
2. **Forward secrecy beats static RSA.** ECDHE key exchange comes before RSA key exchange, so a leaked private key doesn't expose past traffic.
3. **AES-128 beats AES-256.** Both are secure for the foreseeable future, and AES-128 is faster. The extra margin from AES-256 doesn't justify the cost as a default.
4. **Within CBC, SHA-1 beats SHA-256.** This looks backwards, but Go's CBC-SHA256 implementation lacks the Lucky13 countermeasures that the SHA-1 variants have. HMAC-SHA1 is not broken in this setting.
5. **Legacy suites go last.** 3DES sits at the bottom of the list. Later releases go further: Go 1.22 dropped RSA key exchange suites from the default set, and Go 1.23 dropped 3DES. Both can be re-enabled with a GODEBUG setting if you really need them.

## AES-GCM or ChaCha20?

The most interesting rule concerns the two modern AEADs. AES-GCM is extremely fast on hardware with AES instructions, such as AES-NI on amd64 or the ARMv8 crypto extensions. Without that hardware it is slow, and it is hard to implement in constant time. ChaCha20-Poly1305 is fast and safe in pure software.

The right choice therefore depends on the hardware at **both** ends:

- If the local machine lacks AES hardware, Go prefers ChaCha20-Poly1305.
- On a server, Go also looks at the client's list. If the client puts ChaCha20-Poly1305 ahead of AES-GCM, it is probably a device without AES acceleration, such as an older phone, so the server picks ChaCha20 even if the server itself has AES-NI.

A fixed, hand-written list can't make this decision per connection. The automatic ordering does it on every handshake.

## What to do with your config

In most cases, the right move is to delete code. This kind of configuration is now unnecessary:

```go
cfg := &tls.Config{
    PreferServerCipherSuites: true, // ignored since Go 1.17
    CipherSuites: []uint16{          // order ignored
        tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
        tls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,
        tls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
    },
}
```

It can usually become:

```go
cfg := &tls.Config{
    MinVersion: tls.VersionTLS12,
}
```

If a compliance requirement forces you to restrict the enabled set, keep `CipherSuites`, and be aware that only membership matters. The `tls.CipherSuites()` and `tls.InsecureCipherSuites()` functions are useful for auditing what is available and what is flagged as unsafe.

Setting `MinVersion` to TLS 1.2 or 1.3 usually has a bigger security effect than tuning individual suites.

## Why this is the right trade-off

Taking away a knob can feel uncomfortable, but this one mostly produced misconfigurations. Hand-maintained lists drifted, got copied between services, and encoded advice that was years out of date. Moving the ordering into the standard library means:

- **Security fixes ship with Go upgrades.** When the recommended order changes, you get the new order by updating your toolchain, with no audit across every repository.
- **Decisions are made per connection.** Hardware-aware selection can't be expressed in a static list.
- **There is less to review.** A TLS config with no cipher suite list has nothing to get wrong.

If you still have cipher suite lists in Go services, take a few minutes to remove them. You'll end up with less code, and your services will negotiate suites that suit the hardware at both ends of each connection.
