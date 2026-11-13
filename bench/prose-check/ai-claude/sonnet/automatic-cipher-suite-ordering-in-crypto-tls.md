# Automatic cipher suite ordering in crypto/tls

If you have ever configured a TLS server, you have probably faced a deceptively simple question: in what order should the cipher suites be listed? For years, Go's `crypto/tls` package left that decision to the application developer. Starting with Go 1.17, the package takes the decision out of your hands, and in this post we explain why that is the right call and how it works.

## The problem with manual ordering

A TLS handshake begins with the client sending a list of cipher suites it supports. The server then picks one. Which side's preference wins is a server-side policy decision, and historically the `CipherSuites` field of `tls.Config` let developers dictate both the set of suites and their order.

In practice, this created three recurring problems.

**Ordering is hard to get right.** A good ordering depends on details most developers don't track: which suites provide forward secrecy, which have known weaknesses, and which perform best on a given CPU. A list that was sensible in 2014 may be harmful today.

**Hardware matters.** AES-GCM is extremely fast on processors with AES instructions, such as AES-NI on x86 or the equivalent extensions on ARM. On hardware without them, ChaCha20-Poly1305 is both faster and easier to implement without timing side channels. The best choice depends on the client's hardware as much as the server's, and a static list cannot express that.

**Stale configuration lingers.** Hand-written lists get copied between projects and rarely revisited. When a suite is found to be weak, the fix requires every application owner to notice and update their config.

## What Go does now

Go's `crypto/tls` now ignores the order of `Config.CipherSuites`. The field still controls *which* suites are enabled, but the package decides the *preference order* itself, based on a fixed set of rules.

The rules are straightforward:

1. **Prefer secure, modern suites first.** Suites with forward secrecy and authenticated encryption (AEAD) rank above those without. Suites using ECDHE with AES-GCM or ChaCha20-Poly1305 sit at the top.
2. **Prefer hardware-appropriate ciphers.** If both the server and the client have hardware AES support, AES-GCM is preferred. If either side lacks it, ChaCha20-Poly1305 moves ahead.
3. **Deprioritize legacy suites.** Anything using CBC mode, SHA-1 MACs, or RSA key exchange falls to the bottom, and some are disabled by default.

Because the package knows what it is running on, it can make the hardware decision at runtime. It also inspects the client's offered list: if the client puts ChaCha20-Poly1305 first, that is often a signal the client lacks AES acceleration, and the server can honor that preference without any configuration.

## Why not just give developers a better default list?

A better static list would help, but it would still age. Automatic ordering lets the Go team update priorities in a new release, and every application that rebuilds picks up the improvement. There is no migration guide, no config flag, and no coordinated effort across teams.

It also removes a class of mistakes. A developer who sets `PreferServerCipherSuites` and supplies a carefully hand-ordered list can accidentally force a slow cipher on mobile clients, or keep a vulnerable suite near the top. When the library owns the ordering, those mistakes aren't possible.

## What about TLS 1.3?

TLS 1.3 already simplified this problem by removing the legacy suites entirely. Only a handful of AEAD suites remain, and they are not configurable in Go. The automatic ordering described here mainly matters for TLS 1.2 and earlier, which is where most of the historical complexity lives. As TLS 1.3 adoption grows, the ordering logic matters less, but it remains important for compatibility with older clients.

## What you need to do

Most of the time, nothing. If you don't set `CipherSuites`, you get a sensible, maintained default. If you do set it, treat it as an allow-list: choose which suites are acceptable and let Go handle the rest.

A few practical recommendations:

- **Remove custom lists** unless you have a compliance requirement that demands a specific set.
- **Use the allow-list for restrictions**, such as disabling a suite your security policy forbids, not for tuning performance.
- **Keep your Go toolchain current.** The ordering improves with each release, and you only benefit if you rebuild.
- **Use `tls.CipherSuites()` and `tls.InsecureCipherSuites()`** to inspect what the package considers secure, rather than maintaining your own list.

## Takeaways

Cipher suite ordering is a problem where the right answer changes over time and depends on context the application rarely has. Moving that decision into the standard library means better defaults for everyone, fewer misconfigurations, and security updates that arrive with a routine upgrade.

The broader lesson is one we keep relearning: when a configuration option is easy to get wrong and hard to get right, the best API is often one that doesn't ask the question at all.
