---
name: tauri
description: >
  Tauri v2 desktop and mobile engineering: the Rust/TypeScript IPC boundary,
  commands, managed state, events, capabilities and permissions, tauri.conf.json,
  bundling and mobile targets. Use whenever the user works in a Tauri repo or asks
  anything involving src-tauri/, tauri.conf.json, capabilities/*.json, gen/schemas/,
  #[tauri::command], invoke(), @tauri-apps/api, tauri-plugin-*, tauri dev, tauri
  build, or Tauri Android/iOS. Trigger even when the user does not say "Tauri" but
  files or commands are clearly Tauri. This skill owns the boundary and the
  Tauri-specific surface only: Rust idioms defer to the rust skill, TypeScript
  idioms to the typescript skill. Specialist rules live in references/ and load
  through the routing table below.
---

# Tauri v2 engineering skill

Tauri fails at three seams: the IPC boundary between Rust and TypeScript, the permission ACL, and the version ceiling. Everything else is ordinary Rust or ordinary web. Goal: commands that are typed on both sides, capabilities that are explicit, and no API used that the pinned version does not have.

v2 only. v1 is out of scope and out of support here.

## Routing table (mandatory)

Read matching reference BEFORE writing code. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| `#[tauri::command]`, `invoke`, argument naming, command errors, raw bytes, `Channel`, `Request`/`Response`, Rust to TS type generation | `references/ipc.md` |
| `app.manage`, `State<'_, T>`, `Mutex` choice, `emit`/`emit_to`/`emit_filter`, `listen`, `EventTarget`, window vs webview targeting | `references/state-events.md` |
| `capabilities/*.json`, permission identifiers, scopes, `$HOME`/`$APPDATA` globs, CSP, `assetProtocol`, remote origins, `build.rs` `AppManifest` | `references/permissions.md` |
| `tauri.conf.json`, window config, plugin registration, bundling, updater, signing, Android/iOS targets | `references/config.md` |
| picking APIs for a given `Cargo.toml` version, MSRV, what each 2.x minor unlocks, Tauri 3 | `references/versions.md` |
| a command is denied, a path is forbidden, an asset will not load, build fails in `tauri-build`, anything that "works in dev but not release" | `references/debugging.md` |

Multiple matches: read all matched. Unsure: read `ipc.md` and `permissions.md`.

## Before writing

1. Read `src-tauri/Cargo.toml`. Note the `tauri` version. Never use an API newer than it. `references/versions.md` lists what each minor unlocks. Read `Cargo.lock` for the resolved version: `tauri = "2.7"` is a caret range and resolves to the newest 2.x, so the lockfile is the real ceiling, not the manifest.
2. Read `package.json`. `@tauri-apps/api` versions independently of the `tauri` crate. Note the package manager and the frontend framework.
3. Read `tauri.conf.json`. Note `app.security.capabilities`: if non-empty, capability files not listed there are ignored entirely.
4. List `src-tauri/capabilities/`. Note window labels in use. Labels, not titles, are the security boundary.
5. Check whether `src-tauri/build.rs` declares `AppManifest::commands`. That single call flips your own commands from unrestricted to ACL gated.
6. Never guess an API signature. `cargo doc --open`, `cargo tree -p tauri`, or read `node_modules/@tauri-apps/api`. Tauri's own published docs contain snippets that do not compile.

## Non-negotiables

- Read the version before the API. The ceiling is `Cargo.lock`, not memory.
- Sync `#[tauri::command]` runs on the main thread. Anything doing IO or real work is `async fn`. `#[tauri::command(async)]` spawns onto the async runtime, not a blocking pool: for blocking work use `tauri::async_runtime::spawn_blocking` inside an `async fn`.
- `async fn` with a reference input (`State<'_, T>`, `Request<'_>`) must return `Result`. Compiler says so; do not fight it.
- Command errors: custom error enum, `thiserror` for `Display`, plus a hand written `impl Serialize`. `thiserror` does not give you `Serialize`. `Result<_, String>` only in throwaway code.
- Command args are camelCase over the wire by default. Rust `some_arg` is JS `someArg`. Mismatch is a runtime rejection, never a compile error.
- One `generate_handler!` call. A second `invoke_handler` silently discards the first.
- Commands in `lib.rs` are not `pub`. Commands in submodules are `pub`. Names are globally unique across modules.
- Bytes go over `tauri::ipc::Response::new(Vec<u8>)` and arrive as `ArrayBuffer`. Never JSON encode a `Vec<u8>`. Raw request bodies must be the top level `invoke` arg, and do not work on Android.
- `Channel<T>` for ordered streaming from one invoke. Events for fan out. Commands for request/response. Events have no ACL: never route privileged data over them.
- `emit` is global even when called on a `Window`. Scope with `emit_to` or `emit_filter`.
- State is keyed by type. `Builder::manage` panics on a duplicate type; `Manager::manage` silently keeps the first value and returns `false`. Newtype wrap to hold two of a type. No `Arc`: Tauri wraps for you.
- `std::sync::Mutex` in state by default. `tokio::sync::Mutex` only when the guard is held across `.await`. Never hold a std guard across `.await`.
- Permission identifiers: plugin is two segment (`fs:allow-read-file`), core is three segment (`core:window:allow-set-title`), your own commands are bare. `plugin:` never appears in a capability.
- A permission is not a scope. `fs:default` grants no paths. Scoped commands need the object form with `allow`.
- `deny` always beats `allow`, across permissions and across capabilities.
- Every window label matches a capability or that window has zero IPC.
- `platforms` values are case sensitive and irregular: `"linux"`, `"windows"`, `"android"` lowercase, `"macOS"` and `"iOS"` not. A misspelling fails the build; a valid value that excludes the current target is silently inert by design.
- Debug ACL errors name the fix. Release ACL errors do not. Never diagnose a permission problem in a release build.
- Type the boundary once. Generate TS from Rust, or centralize every command name and arg name in one façade module. Never scatter hand written `invoke('name', {...})` string literals across components.
- No secrets in the frontend bundle. It ships as readable assets.
- Comments: full sentences. Delete comments that restate code. No em dash characters.

## After writing (gate, in order)

```sh
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check   # must print nothing
cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets -- -D warnings
cargo check --manifest-path src-tauri/Cargo.toml
<pm> exec tsc --noEmit                                       # frontend typecheck
cargo tauri dev                                              # or: cargo tauri build --debug
```

`cargo check` catches wrong APIs and wrong versions. `tauri-build` catches unknown permission identifiers and malformed capabilities. Neither catches a wrong window label or a missing scope: those are runtime only. Exercise every command you touched at least once in a debug build before calling it done.

`cargo tauri info` when the toolchain or platform is in question. `cargo tauri permission ls` when an identifier's exact spelling is in question. Not done until gate green. Report failures verbatim.

## Tool preference

- Symbols, references, hover: `LSP` tool (rust-analyzer) when exposed. Else `cargo doc`, `mcp__fff__grep`, `rg`.
- Crate API: `cargo doc -p tauri --open` or docs.rs pinned to the resolved version. Never guess signatures.
- JS API: read `node_modules/@tauri-apps/api/*.d.ts`. It is the installed truth.
- Permission discovery: `cargo tauri permission ls [plugin]`, and `src-tauri/gen/schemas/*.json` for what actually compiled in.
- Global rules still apply: humanizer comments, Code Simplicity Discipline, Useless Test Ban, terminology guard (`snapshot`/`expected`, never `golden`). Cross-language naming, function size, and architecture: skill `software-design`.
