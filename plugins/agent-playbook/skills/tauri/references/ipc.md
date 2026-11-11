# Tauri IPC

Loaded via `tauri` SKILL.md routing table. Sources: v2.tauri.app/develop/calling-rust, calling-frontend, docs.rs/tauri `ipc` module, `tauri-macros` command wrapper source.

Rust idioms defer to the rust skill. TypeScript idioms defer to the typescript skill. This file owns the boundary.

## Command macro

```rust
#[tauri::command]
fn greet(name: String) -> String { format!("hello {name}") }
```

Attribute arguments, exhaustive:

| Arg | Values | Default | Notes |
|---|---|---|---|
| `rename_all` | `"camelCase"` or `"snake_case"` only | `"camelCase"` | any other value is a compile error |
| `rename` | string literal | none | renames the command as seen by `invoke`. **2.11.0+** |
| `root` | crate path or `"crate"` | `::tauri` | plugin authors only |
| `async` | bare, no value | none | forces async execution of a sync fn |

## Execution context

- `fn foo()` runs **on the main thread**. Blocking here freezes the UI. Use for trivial synchronous work only.
- `async fn foo()` is spawned on the async runtime.
- `#[tauri::command(async)] fn foo()` wraps a sync body in an async block and **spawns**, not `spawn_blocking`. A CPU heavy body still occupies a runtime worker. For genuinely blocking work write `async fn` and call `tauri::async_runtime::spawn_blocking` inside.

## Async plus references

If the fn is `async` and any input contains a reference, the return type must be `Result`. The macro emits: ``async commands that contain references as inputs must return a `Result` ``.

```rust
#[tauri::command]
fn sync_ok(state: tauri::State<'_, AppState>) -> u32 { 0 }            // fine

#[tauri::command]
async fn async_ok(state: tauri::State<'_, AppState>) -> Result<u32, String> { Ok(0) }   // fine

#[tauri::command]
async fn broken(state: tauri::State<'_, AppState>) -> u32 { 0 }       // compile error
```

## Registration and visibility

```rust
tauri::Builder::default()
  .invoke_handler(tauri::generate_handler![greet, commands::open_file])
```

- **One** `generate_handler!` call. Calling `invoke_handler` twice silently discards the first; only the last survives.
- Commands defined in `lib.rs` must **not** be `pub`, or you get `error[E0255]: the name __cmd__<name> is defined multiple times`.
- Commands in submodules **must** be `pub`.
- Command names are global, not module scoped. Two `get_config` in different modules collide. On 2.11+ disambiguate with `rename = "..."` rather than renaming the Rust fn.
- The module path in `generate_handler!` is compile time only. The frontend still calls the bare name.

## Argument naming

The Rust parameter ident is converted with `to_lower_camel_case` and that becomes the JSON key.

```rust
#[tauri::command]
fn my_command(invoke_message: String) {}
```
```ts
await invoke('my_command', { invokeMessage: 'hello' })
```

Override per command:

```rust
#[tauri::command(rename_all = "snake_case")]
fn my_command(invoke_message: String) {}
```
```ts
await invoke('my_command', { invoke_message: 'hello' })
```

- There is no snake_case fallback in v2. A mismatch on a **non-optional** parameter is an `InvalidArgs` rejection at runtime, never a compile error.
- A mismatch on an `Option<T>` parameter is **silent**: the deserializer visits `None` for an absent key, so `fn cmd(some_arg: Option<String>)` called with `{ some_arg: "x" }` gets `None` and no error at all. Optional parameters hide casing bugs; check them first when a value arrives empty.
- Raw identifiers are unraw'd: `r#type` is key `type`.
- This applies only to top level command parameters. Fields inside a struct argument follow that struct's own `#[serde(rename_all)]`.

## Injected parameters

Mix freely with ordinary JSON args, any order.

| Type | Syntax |
|---|---|
| `tauri::AppHandle<R>` | `app: tauri::AppHandle` |
| `tauri::Window<R>` | `window: tauri::Window` |
| `tauri::Webview<R>` | `webview: tauri::Webview` |
| `tauri::WebviewWindow<R>` | `webview_window: tauri::WebviewWindow` |
| `tauri::State<'r, T>` | `state: tauri::State<'_, MyState>` |
| `tauri::ipc::Request<'a>` | `request: tauri::ipc::Request<'_>` |
| `tauri::ipc::Channel<T>` | `on_event: tauri::ipc::Channel<MyEvent>` |
| `tauri::ipc::CommandScope<T>` | `scope: CommandScope<MyScopeEntry>` |
| `tauri::ipc::GlobalScope<T>` | `scope: GlobalScope<MyScopeEntry>` |
| any `D: Deserialize` | ordinary arg |

Generic runtime form when the code must be runtime agnostic:

```rust
use tauri::{AppHandle, Runtime, WebviewWindow};

#[tauri::command]
async fn cmd<R: Runtime>(app: AppHandle<R>, window: WebviewWindow<R>) {}
```

There is no `PathResolver::app_dir()` in v2. Use `app_config_dir()`, `app_data_dir()`, `app_local_data_dir()`, `app_cache_dir()`, `app_log_dir()`, all returning `tauri::Result<PathBuf>`. `GlobalShortcutManager` is gone: use `tauri-plugin-global-shortcut`.

## Errors

The bound is `E: Into<InvokeError>`, satisfied in practice by `E: Serialize`. `Ok` resolves the promise, `Err` rejects it.

`thiserror::Error` gives you `Display`, not `Serialize`. Write the impl.

Default pattern, flat:

```rust
#[derive(Debug, thiserror::Error)]
enum Error {
    #[error(transparent)]
    Io(#[from] std::io::Error),
}

impl serde::Serialize for Error {
    fn serialize<S: serde::ser::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(self.to_string().as_ref())
    }
}
```

Preferred when the frontend must branch on kind. Keep `#[from]` conversions on one type and structured serialization on another:

```rust
#[derive(Debug, thiserror::Error)]
enum Error {
    #[error(transparent)]
    Io(#[from] std::io::Error),
    #[error("failed to parse as string: {0}")]
    Utf8(#[from] std::str::Utf8Error),
}

#[derive(serde::Serialize)]
#[serde(tag = "kind", content = "message")]
#[serde(rename_all = "camelCase")]
enum ErrorKind {
    Io(String),
    Utf8(String),
}

impl serde::Serialize for Error {
    fn serialize<S: serde::ser::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let message = self.to_string();
        match self {
            Self::Io(_) => ErrorKind::Io(message),
            Self::Utf8(_) => ErrorKind::Utf8(message),
        }
        .serialize(serializer)
    }
}
```

Frontend sees `{ kind: 'io' | 'utf8', message: string }`.

You cannot `#[derive(Serialize)]` on an enum holding `std::io::Error`. That is why the manual impl exists.

## Raw and large payloads

JSON encoding a `Vec<u8>` produces a number array roughly 3 to 4 times the byte size plus serde and `JSON.parse` cost on both sides. Use raw for file contents, images, HTTP bodies, anything past tens of KB.

Rust to JS:

```rust
use tauri::ipc::Response;

#[tauri::command]
fn read_file() -> Response {
    let data = std::fs::read("/path/to/file").unwrap();
    Response::new(data)
}
```

- `InvokeResponseBody::Raw` sends `application/octet-stream`; the frontend receives an **`ArrayBuffer`**, not an array. Wrap it: `new Uint8Array(await invoke<ArrayBuffer>('read_file'))`.
- `From<String>` maps to `Json`, not a JSON encoded string. `Response::new("abc".to_string())` sends raw bytes labelled `application/json` and breaks `response.json()`. For bytes always pass `Vec<u8>`.

JS to Rust:

```rust
#[tauri::command]
fn upload(request: tauri::ipc::Request) -> Result<(), Error> {
    let tauri::ipc::InvokeBody::Raw(data) = request.body() else {
        return Err(Error::RequestBodyMustBeRaw);
    };
    let Some(auth) = request.headers().get("Authorization") else {
        return Err(Error::MissingHeader("Authorization"));
    };
    Ok(())
}
```
```ts
await invoke('upload', new Uint8Array([1, 2, 3]), { headers: { Authorization: 'apikey' } })
```

- The buffer must be the **top level** arg. `invoke('upload', { file: bytes })` silently degrades to a JSON number array.
- With a raw body there are no named arguments, only `Request`. Metadata goes in `options.headers`.
- **Android does not support `InvokeBody::Raw`.** The body is always `Json` there. Pass base64 in a `String` instead, still cheaper than a number array.

## Channels

Ordered, typed streaming from one invoke back to the caller. Ordering is guaranteed by an internal index; the JS side buffers and replays out of order messages.

```rust
use tauri::ipc::Channel;

#[derive(Clone, serde::Serialize)]
#[serde(rename_all = "camelCase", rename_all_fields = "camelCase", tag = "event", content = "data")]
enum DownloadEvent<'a> {
    Started { url: &'a str, download_id: usize, content_length: usize },
    Progress { download_id: usize, chunk_length: usize },
    Finished { download_id: usize },
}

#[tauri::command]
fn download(url: String, on_event: Channel<DownloadEvent>) {
    on_event.send(DownloadEvent::Started { url: &url, download_id: 1, content_length: 1000 }).unwrap();
    for chunk_length in [15, 150, 35] {
        on_event.send(DownloadEvent::Progress { download_id: 1, chunk_length }).unwrap();
    }
    on_event.send(DownloadEvent::Finished { download_id: 1 }).unwrap();
}
```
```ts
import { invoke, Channel } from '@tauri-apps/api/core'

type DownloadEvent =
  | { event: 'started'; data: { url: string; downloadId: number; contentLength: number } }
  | { event: 'progress'; data: { downloadId: number; chunkLength: number } }
  | { event: 'finished'; data: { downloadId: number } }

const onEvent = new Channel<DownloadEvent>()
onEvent.onmessage = (message) => console.log(message.event)
await invoke('download', { url, onEvent })
```

`Channel` is cheap to clone (`Arc` inside): clone it into spawned tasks. Dropping the Rust side sends an end message that unregisters the JS callback.

**`Channel<T>` sends JSON unless `T` yields `Raw`.** `Channel<&[u8]>` is a JSON number array per chunk, not a byte stream. To stream bytes:

```rust
use tauri::ipc::{Channel, InvokeResponseBody};
use tokio::io::AsyncReadExt;

#[tauri::command]
async fn load_image(path: std::path::PathBuf, reader: Channel<InvokeResponseBody>) -> Result<(), String> {
    let mut file = tokio::fs::File::open(path).await.map_err(|e| e.to_string())?;
    let mut chunk = vec![0u8; 65536];
    loop {
        let len = file.read(&mut chunk).await.map_err(|e| e.to_string())?;
        if len == 0 { break; }
        reader.send(InvokeResponseBody::Raw(chunk[..len].to_vec())).map_err(|e| e.to_string())?;
    }
    Ok(())
}
```

Slice to `len`. Sending the whole buffer pads the final chunk with stale bytes.

For a channel nested inside a JSON argument rather than a top level parameter, use `tauri::ipc::JavaScriptChannelId` and `channel_on(webview)`.

## Choosing command, channel, or event

| | Command | Channel | Event |
|---|---|---|---|
| Shape | request/response | one invoke, many ordered messages | fan out, many producers and consumers |
| Typed | yes | yes, generic both sides | no |
| Ordering | n/a | guaranteed | not guaranteed |
| Payload | JSON or raw | JSON or raw | JSON string only |
| ACL gated | yes | yes, via its command | **no** |

Default to a command. Channel when one call streams progress, log output, or bytes. Event when Rust initiates with no originating invoke: menu clicks, tray, deep links, window lifecycle. Never route privileged data over events.

`WebviewWindow::eval` is the last resort. For scripts embedding Rust data use the `serialize-to-javascript` crate rather than string formatting.

## Typing the boundary

Nothing checks that `invoke('get_user', { userId })` matches `fn get_user(user_id: u32)`. Both the command name and every argument name are unchecked strings. Pick one of these and apply it everywhere.

**Generated bindings, `tauri-specta`.** The only option that generates command and event bindings, not just types. Still RC after a long run; pin exactly.

```sh
cargo add tauri@2 specta@=2.0.0-rc.25 specta-typescript@0.0.12
cargo add tauri-specta@=2.0.0-rc.25 --features derive,typescript
```

```rust
use specta_typescript::Typescript;
use tauri_specta::{collect_commands, Builder};

#[tauri::command]
#[specta::specta]
fn hello(name: String) -> String { format!("hello {name}") }

fn main() {
    let builder = Builder::new().commands(collect_commands![hello]);

    #[cfg(debug_assertions)]
    builder.export(Typescript::default(), "../src/bindings.ts").unwrap();

    tauri::Builder::default()
        .invoke_handler(builder.invoke_handler())
        .setup(move |app| { builder.mount_events(app); Ok(()) })
        .run(tauri::generate_context!())
        .unwrap();
}
```

Every command needs the second `#[specta::specta]` attribute. Custom types need `#[derive(specta::Type)]`. Export only under `debug_assertions`. `tauri` has a `specta` cargo feature that gives `Channel` and `State` the right impls.

**Types only, `ts-rs`.** Stable, far more widely used, no Tauri awareness: no command signatures, no arg name mapping, no event typing. Derive `TS` and `#[ts(export)]`; bindings are written during `cargo test`.

**Minimum acceptable fallback.** One `src/lib/commands.ts` façade that is the only file in the codebase containing `invoke` string literals, with a hand written typed wrapper per command. Scattering `invoke('...')` through components is the thing to prevent, whichever option you choose.

## Gotchas

- Sync commands run on the main thread.
- `#[tauri::command(async)]` spawns, it does not `spawn_blocking`.
- Arg name mismatch, command name typo, wrong `State` type, and missing `.manage()` are all runtime rejections, never compile errors.
- A raw response arrives as `ArrayBuffer`.
- Raw request bodies are top level only, and unsupported on Android.
- `Channel<&[u8]>` is not a byte stream.
- `generate_handler!` exactly once.
- Published Tauri docs contain snippets that do not compile, including `event.data`, `event.id`, and `PathResolver::app_dir()`. Verify against `cargo doc` for your pinned version.
