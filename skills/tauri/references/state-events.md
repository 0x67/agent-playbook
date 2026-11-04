# Tauri State and Events

Loaded via `tauri` SKILL.md routing table. Sources: v2.tauri.app/develop/state-management, calling-frontend, docs.rs/tauri `Manager`, `Emitter`, `Listener`, `EventTarget`.

## Managed state

State is keyed by `TypeId`. Two values of the same type cannot coexist.

```rust
use std::sync::Mutex;
use tauri::{Builder, Manager};

#[derive(Default)]
struct AppStateInner { counter: u32 }
type AppState = Mutex<AppStateInner>;

Builder::default()
    .setup(|app| { app.manage(AppState::default()); Ok(()) })
    .run(tauri::generate_context!())
    .unwrap();
```

Use the type alias as written. Do not wrap it in a second `Mutex` at the use site.

### Two `manage` functions, different failure behaviour

| Call | On duplicate type |
|---|---|
| `tauri::Builder::manage` | **panics**: `state for type '{T}' is already being managed` |
| `tauri::Manager::manage` (on `App`, `AppHandle`, windows) | **silently keeps the first value**, returns `false` |

```rust
app.manage(MyInt(0));
assert!(!app.manage(MyInt(1)));   // false, MyInt is still 0
```

To hold two values of one underlying type, newtype them:

```rust
struct PrimaryDb(Pool);
struct ReplicaDb(Pool);
```

### Reading state

| Path | Unmanaged behaviour |
|---|---|
| `Manager::state::<T>()` | **panics**: `state() called before manage() for {T}` |
| `Manager::try_state::<T>()` | returns `None` |
| `State<'_, T>` as a command parameter | **rejects the invoke**, does not panic |

Command path rejection text, unchanged across 2.x:

```
state not managed for field `{key}` on command `{name}`. You must call `.manage()` before using this command
```

A wrong `State<'_, T>` type is never a compile error. It is a runtime rejection naming the field and command.

Do not wrap state in `Arc`. Tauri does that. If a lifetime blocks moving state into a thread, clone an `AppHandle` instead; they are deliberately cheap to clone.

`Manager::unmanage` is **deprecated since 2.3.0** and unsound: previously obtained references dangle. Model removable state as `Mutex<Option<T>>` and `Option::take`.

Outside a command:

```rust
fn on_window_event(window: &tauri::Window, _event: &tauri::WindowEvent) {
    let state = window.app_handle().state::<AppState>();
    state.lock().unwrap().counter += 1;
}
```

### Mutex choice

Default to `std::sync::Mutex`, including in async commands. Tauri's docs quote Tokio's own guidance: the async mutex exists for holding a guard across await points, chiefly IO resources like a database connection.

- `std::sync::Mutex`: lock, mutate, drop the guard, no `.await` in between. Holding the guard across `.await` makes the future non `Send` and fails to compile, which is the intended guard rail.
- `tokio::sync::Mutex`: only when the guard genuinely must be held across `.await`.

Scope the guard explicitly when both are needed in one command:

```rust
#[tauri::command]
async fn bump(state: tauri::State<'_, AppState>) -> Result<u32, String> {
    let n = {
        let mut s = state.lock().map_err(|e| e.to_string())?;
        s.counter += 1;
        s.counter
    };
    do_io().await;
    Ok(n)
}
```

`std::sync::Mutex` poisons, so `.lock()` returns `Result`. `.unwrap()` in a command turns an earlier panic into a second panic on the main thread. Prefer `.map_err`, or `parking_lot::Mutex` which neither poisons nor returns `Result`.

## Events

### Emitting

```rust
pub trait Emitter<R: Runtime> {
    fn emit<S: Serialize + Clone>(&self, event: &str, payload: S) -> Result<()>;
    fn emit_str(&self, event: &str, payload: String) -> Result<()>;
    fn emit_to<I: Into<EventTarget>, S: Serialize + Clone>(&self, target: I, event: &str, payload: S) -> Result<()>;
    fn emit_str_to<I: Into<EventTarget>>(&self, target: I, event: &str, payload: String) -> Result<()>;
    fn emit_filter<S, F>(&self, event: &str, payload: S, filter: F) -> Result<()>
        where S: Serialize + Clone, F: Fn(&EventTarget) -> bool;
    fn emit_str_filter<F>(&self, event: &str, payload: String, filter: F) -> Result<()>
        where F: Fn(&EventTarget) -> bool;
}
```

Implemented on `App`, `AppHandle`, `Window`, `Webview`, `WebviewWindow`.

**`emit` is always global, whatever you call it on.** `window.emit(...)` reaches every window. Only `emit_to` and `emit_filter` scope.

The `_str` variants take pre serialized JSON. Use them to avoid re-serializing one payload in a loop.

```rust
use tauri::{AppHandle, Emitter, EventTarget};

app.emit("download-progress", 50).unwrap();
app.emit_to("login", "login-result", result).unwrap();

app.emit_filter("open-file", path, |target| match target {
    EventTarget::WebviewWindow { label } => label == "main" || label == "file-viewer",
    _ => false,
}).unwrap();
```

### Listening in Rust

```rust
use tauri::Listener;

app.listen("download-started", |event| {
    if let Ok(p) = serde_json::from_str::<DownloadStarted>(event.payload()) { /* ... */ }
});

let handle = app.handle().clone();
app.listen("status-changed", move |event| {
    if event.payload() == "\"ready\"" { handle.unlisten(event.id()); }
});
```

- `Event` fields are private. Use `event.payload()` and `event.id()`. Published docs show `event.data` and `event.id` as fields; those snippets do not compile.
- The payload is always a JSON string. A Rust `String` payload arrives quoted. Always `serde_json::from_str`.
- `listen`, `once`, `listen_any`, `once_any` **panic** if the event name contains anything outside alphanumeric, `-`, `/`, `:`, `_`.

Which target a receiver registers under:

| Receiver | Registers as |
|---|---|
| `App` / `AppHandle` | `EventTarget::App` |
| `Window<R>` | `EventTarget::Window { label }` |
| `Webview<R>` | `EventTarget::Webview { label }` |
| `WebviewWindow<R>` | `EventTarget::WebviewWindow { label }` |
| any, via `listen_any` | `EventTarget::Any` |

### EventTarget matching

```rust
pub enum EventTarget {
    Any,
    AnyLabel { label: String },
    App,
    Window { label: String },
    Webview { label: String },
    WebviewWindow { label: String },
}
```

A **string target means `AnyLabel`**, not `WebviewWindow`. `emit_to("main", ...)` is `AnyLabel { label: "main" }`. Same on the JS side.

| emit_to target / listener registered as | `App` | `Window{L}` | `Webview{L}` | `WebviewWindow{L}` | `AnyLabel{L}` | `Any` |
|---|---|---|---|---|---|---|
| `AnyLabel{L}` | no | yes | yes | yes | yes | yes |
| `Window{L}` | no | yes | no | no | yes | yes |
| `Webview{L}` | no | no | yes | no | yes | yes |
| `WebviewWindow{L}` | no | no | no | yes | yes | yes |
| `App` | yes | no | no | no | no | yes |
| `Any` | yes | yes | yes | yes | yes | yes |

**`EventTarget::Any` listeners receive everything and bypass `emit_filter` entirely.** The filter closure is never consulted for them. A filter cannot exclude an `Any` listener.

Consequences:

- `app.listen(...)` registers as `App` and does **not** receive `emit_to("main", ...)`. Use `listen_any` for a Rust side catch all.
- `emit_to(EventTarget::WebviewWindow { label }, ...)` is stricter than `emit_to(label, ...)`: it skips `Window` and `Webview` registered listeners.
- Listeners are cleaned up automatically when their window or webview closes.
- Frontend and Rust share one bus in both directions.

### Frontend

```ts
import { listen, once, emit, emitTo, TauriEvent } from '@tauri-apps/api/event'

const unlisten = await listen<number>('download-progress', (e) => setProgress(e.payload))
unlisten()
```

- The free `listen()` defaults to `{ kind: 'Any' }`, so it is already a catch all. `getCurrentWebviewWindow().listen(...)` scopes to that window's label.
- `listen` returns a **Promise**. `const unlisten = listen(...); unlisten()` does not clean up; it calls a Promise. Always `await`.
- Listeners are unregistered on page reload and navigation, **but not on SPA router navigation**. Unlisten on unmount.

```tsx
useEffect(() => {
  const unlisten = listen<number>('download-progress', (e) => setProgress(e.payload))
  return () => { unlisten.then((fn) => fn()) }
}, [])
```

Built in events are on the `TauriEvent` enum: `tauri://resize`, `tauri://move`, `tauri://close-requested`, `tauri://destroyed`, `tauri://focus`, `tauri://blur`, `tauri://scale-change`, `tauri://theme-changed`, `tauri://window-created`, `tauri://webview-created`, `tauri://drag-enter`, `tauri://drag-over`, `tauri://drag-drop`, `tauri://drag-leave`, plus `tauri://suspended` and `tauri://resumed` on mobile.

## Gotchas

- `Builder::manage` panics on a duplicate type; `Manager::manage` silently no-ops.
- State is keyed by type. Newtype to hold two of one type.
- Missing `.manage()` rejects the invoke with a message naming the field and command; it does not panic.
- `Manager::unmanage` is deprecated and unsound.
- `emit` on a `Window` is still global.
- `EventTarget::Any` listeners bypass all filters.
- `app.listen` is not a catch all. `listen_any` is.
- Event payloads are JSON strings in Rust. Always parse.
- Event names are restricted; violations panic.
- Events have no ACL gating. Commands do.
