# Security in Code

Loaded via `services` SKILL.md routing table. Sources: OWASP Top 10; OWASP API Security Top 10 (2023); OWASP Cheat Sheet Series (Input Validation, SQL Injection Prevention, Password Storage, Server-Side Request Forgery Prevention, Deserialization, Mass Assignment); MITRE CWE.

AGENTS.md covers the supply chain: dependencies, secrets in commits, untrusted clones. This page covers the code itself. In Claude Code, `/security-review` reviews a finished change.

## Input at the boundary

- Parse every input into typed values at the edge (`software-design` `references/functions.md`): type, length, range, format, allowed values. A value that fails gets a `4xx` naming the field, with no internals echoed back.
- Accept known formats from an allowlist. Denylists of bad characters miss encodings.
- Bind request bodies to a request type that has only the fields a caller may set. Binding straight onto an entity lets a caller set `role` or `balance` (mass assignment).
- Limit sizes: request body, upload, page size, item count, string length, and the nesting depth of JSON.

## Injection

- SQL: bind parameters on every query, through the driver or the query builder. An identifier that must vary (a sort column) comes from an allowlist map, never from the string the caller sent.
- Shell: run the program with an argument list (`exec.Command(name, args...)`, `subprocess.run([...])` without `shell=True`). A command string built from input is injectable.
- File paths: resolve the path, then check that it stays under the allowed directory. Reject `..` and absolute paths from callers.
- HTML: keep the template engine's auto-escaping on, and pass user-supplied HTML through a sanitizer.
- Deserialization: untrusted data never reaches a native object deserializer (Python `pickle`, `yaml.load` with an unsafe loader, Java `ObjectInputStream`, JSON with polymorphic type info). Parse it into plain data types (`yaml.safe_load`, a typed JSON decoder).

## Authentication and authorization

- Authorize in the use case, for each operation and each object (can this user read order 42?), because a logged-in check or a URL pattern alone leaves every other user's objects open. OWASP's API Security Top 10 (2023) ranks broken object level authorization first.
- Take the actor from the verified session or token. A `user_id` in the request body is input, and the caller can change it.
- Deny by default: a new endpoint refuses every caller until a rule allows some.
- Admin and internal endpoints authenticate too; being on the internal network grants nothing.

## Secrets and cryptography

- Passwords: Argon2id, scrypt, or bcrypt through a maintained library, with the parameters in the OWASP Password Storage Cheat Sheet. A fast hash (MD5, SHA-1, SHA-256) or an unsalted one is broken for passwords.
- Tokens, unguessable ids, and nonces come from a CSPRNG (Python `secrets`, Go `crypto/rand`, Java `SecureRandom`). General-purpose generators (`random`, `math/rand`) are predictable.
- Compare secrets, tokens, and signatures in constant time: `hmac.compare_digest`, Go `subtle.ConstantTimeCompare`, Java `MessageDigest.isEqual`.
- No home-made cryptography. Use the high-level API of the platform or a maintained library, such as an AEAD cipher (AES-GCM) through it.
- Runtime secrets and logging: `operability.md`.

## Webhooks and outbound requests

- Verify a webhook's signature before parsing it: an HMAC over the raw body with the shared secret, compared in constant time, plus a timestamp check that rejects old deliveries (replays). Then deduplicate it (`resilience.md`).
- A URL that comes from a caller (an avatar fetch, a webhook target, an import) is a server-side request forgery risk. Allow only listed schemes and hosts, block private, loopback, and link-local addresses (the cloud metadata service answers at `169.254.169.254`) after DNS resolution, and do not follow redirects to them.

## Errors and responses

- Callers get an error code and a safe message; stack traces, SQL, internal hostnames, and library versions go only to the logs.
- Rate limit login, password reset, and other credential endpoints per account and per source address.
- CORS allows an explicit list of origins. Reflecting the request's `Origin` while allowing credentials opens the API to any site. CSRF protection stays on for browser endpoints that authenticate with cookies.

## Testing

- Per endpoint: a second user tries to read and change the first user's object and is refused.
- Hostile input in every parsed field (quotes, `../`, very long strings, deep JSON) returns a `4xx` and leaves stored data unchanged.
