# Tauri Capabilities and Permissions

Loaded via `tauri` SKILL.md routing table. Sources: v2.tauri.app/security/*, v2.tauri.app/reference/acl, `tauri-utils::acl` source.

Model in one line: a **permission** allows or denies commands and optionally carries a scope; a **permission set** groups permissions; a **capability** binds permissions to windows and webviews, optionally filtered by platform and origin. The runtime authority enforces this per IPC call.

## Layout

```
src-tauri/
  capabilities/          json, json5, or toml
    default.json
  permissions/           json or toml
    my-permission.toml
  gen/schemas/           generated: <target>-schema.json plus desktop-schema.json and mobile-schema.json
  tauri.conf.json
  build.rs
```

All files in `capabilities/` are enabled by default. **Once `app.security.capabilities` in `tauri.conf.json` is non-empty, only the listed ones are used and the rest are silently ignored.**

## Capability schema

| Key | Type | Required | Default |
|---|---|---|---|
| `identifier` | string | yes | |
| `description` | string | no | `""` |
| `permissions` | array | yes | |
| `windows` | string[] | no | `[]`, glob over window **labels** |
| `webviews` | string[] | no | `[]`, glob over webview labels |
| `platforms` | string[] or null | no | null means all |
| `remote` | `{ urls: string[] }` | no | absent |
| `local` | bool | no | `true` |
| `$schema` | string | no | IDE only, not a real field |

Minimal useful:

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "windows": ["main"],
  "permissions": ["core:default"]
}
```

Realistic:

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-user-files-write",
  "description": "Allows the main window write access to user selected files.",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "dialog:allow-open",
    { "identifier": "fs:allow-write-text-file", "allow": [{ "path": "$HOME/test.txt" }] }
  ],
  "platforms": ["macOS", "windows"]
}
```

Wiring:

```json
{ "app": { "security": { "capabilities": ["main-capability"] } } }
```

Entries may be a string reference or an inlined capability object. Mixing is allowed.

## Permission identifiers

- **Plugin, two segments**: `fs:allow-read-file`, `fs:default`, `shell:allow-execute`, `dialog:allow-open`
- **Core, three segments**: `core:window:allow-set-title`, `core:path:default`, `core:default`
- **Your own commands, bare**: `allow-home-read-extended`

`plugin:` never appears in a capability. It exists only in the internal IPC command string (`plugin:fs|read_file`). `plugin:fs:allow-read-file` is wrong.

The `tauri-plugin-` crate prefix is prepended at compile time and is never written by hand.

Identifier length cap is 116 characters.

`core:default` aggregates `core:app:default`, `core:event:default`, `core:image:default`, `core:menu:default`, `core:path:default`, `core:resources:default`, `core:tray:default`, `core:webview:default`, `core:window:default`.

A plugin's `<plugin>:default` is the safe subset, not everything. `tauri add <plugin>` writes it into your capability for you.

The `core:` prefix on core permissions was introduced between 2.0 beta and 2.0 RC. Anything written as `path:default` or `window:default` is pre-release syntax and invalid.

## Writing your own permissions

JSON or TOML. `tauri permission new` takes `--format` to pick. TOML shown here:

```toml
[[permission]]
identifier = "allow-read-config"
description = "Read files under the app config directory."
commands.allow = ["read_config"]

[[permission.scope.allow]]
path = "$APPCONFIG/*"
```

Sets:

```toml
[[set]]
identifier = "allow-home-read-extended"
description = "Non-recursive read access plus mkdir in $HOME."
permissions = ["fs:read-files", "fs:scope-home", "fs:allow-mkdir"]
```

If a command appears in both `allow` and `deny`, it is denied.

## Scopes

A permission is not a scope. `fs:default` grants no paths. Without an `allow` scope a scoped command fails at runtime with `forbidden path: <path>` even though the permission is enabled.

Object form: `allow` and `deny` are **siblings of `identifier`**, not nested under a `scope` key.

```json
"permissions": [
  "fs:default",
  { "identifier": "fs:allow-rename", "allow": [{ "path": "$HOME/**/*" }] },
  { "identifier": "fs:allow-rename", "deny":  [{ "path": "$HOME/.config/**/*" }] }
]
```

Repeat an identifier to layer allow and deny. `deny` always beats `allow`, across permissions and across capabilities.

Global scope for every command of a plugin uses `<plugin>:scope`:

```json
{ "identifier": "fs:scope", "allow": [{ "path": "$APPDATA" }, { "path": "$APPDATA/**/*" }] }
```

Scope shape is plugin specific. `fs` uses `{ "path": ... }`, `http` uses URL patterns, `shell` uses `{ name, cmd, args, sidecar }`.

### Path variables

`$APPCONFIG` `$APPDATA` `$APPLOCALDATA` `$APPCACHE` `$APPLOG` `$AUDIO` `$CACHE` `$CONFIG` `$DATA` `$LOCALDATA` `$DESKTOP` `$DOCUMENT` `$DOWNLOAD` `$EXE` `$FONT` `$HOME` `$PICTURE` `$PUBLIC` `$RUNTIME` `$TEMPLATE` `$VIDEO` `$RESOURCE` `$TEMP`

### Glob semantics

- `$APPDATA/*` is direct children. `$APPDATA/**/*` is recursive.
- `{ "path": "$HOME" }` matches the directory itself but **not its contents**. List both: `[{ "path": "$HOME" }, { "path": "$HOME/**/*" }]`.
- Prefer `**/*` over bare `**` for file oriented globs.
- **Leading dot rule.** On Unix `requireLiteralLeadingDot` defaults to `true`, so `*`, `?`, `**`, `[...]` do not match a path component starting with `.`. `$HOME/**` will never match `~/.config/app/x`. Either name the segment literally or set `requireLiteralLeadingDot: false`. Defaults `false` on Windows.
- `fs` rejects parent directory traversal outright.

### Reading scope in your own command

```rust
use tauri::ipc::CommandScope;

#[derive(Debug, serde::Deserialize)]
struct ScopeEntry { path: String }

#[tauri::command]
fn my_command(scope: CommandScope<ScopeEntry>) { /* enforce it yourself */ }
```

**Tauri delivers the scope; it does not enforce it for your commands.** You write the check. Also available: `webview.resolve_command_scope::<T>("my-plugin", "read")`.

## Window and webview targeting

- `windows` glob matches window **labels**, not titles. `*`, `admin-*`, exact names.
- Matching a window enables the capability on **all webviews of that window**, regardless of `webviews`.
- `webviews` matches webview labels regardless of whether the window matched. The runtime test is an OR of the two.
- On multiwebview windows prefer `webviews` and omit `windows` for finer control.
- **A window matching no capability has zero IPC access.**
- Windows in more than one capability merge the permissions of all of them.

Only expose window creation to higher privileged windows, since labels are the security boundary.

### Your own commands are not gated by default

By default every command registered via `invoke_handler` is callable from **all** local windows and webviews. That is why `fs:` fails while your own command works. To gate them, declare an app manifest:

```rust
// src-tauri/build.rs
fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&["your_command"])),
    )
    .unwrap();
}
```

Plugin commands are always ACL checked. Your own commands are checked once this manifest exists, **or** whenever the origin is remote.

## Platforms

`platforms` values are case sensitive and irregular:

```
"linux"   "macOS"   "windows"   "android"   "iOS"
```

`"macos"`, `"MacOS"`, `"ios"`, `"Windows"` are all invalid and **fail the build**: `Target` is a plain deserialized enum with no catch all, and capability files are parsed by `tauri-build`, so a misspelling is an `unknown variant` error at compile time.

What is silent is the legitimate case: a correctly spelled `platforms` list that does not include the current target makes the capability inert on that target by design. That is not an error and produces no warning.

```json
{
  "$schema": "../gen/schemas/mobile-schema.json",
  "identifier": "mobile-capability",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": ["nfc:allow-scan", "biometric:allow-authenticate"]
}
```

`platforms` also exists on individual permissions in TOML.

## Remote origins

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "remote-capability",
  "windows": ["main"],
  "remote": { "urls": ["https://*.mydomain.dev"] },
  "permissions": ["barcode-scanner:allow-scan"]
}
```

- `remote.urls` uses the URLPattern standard. An invalid pattern **panics at build time**.
- `local` defaults to `true`. Set `"local": false` to apply the capability only to the listed remote origins.
- A remote origin with no matching remote capability is denied, always, including for your own commands.
- On Linux and Android Tauri cannot distinguish an embedded `<iframe>` from the window itself.

## CSP

`app.security` keys:

| Key | Type | Default |
|---|---|---|
| `csp` | string or object | none |
| `devCsp` | string or object | none, falls back to `csp` |
| `freezePrototype` | bool | `false` |
| `dangerousDisableAssetCspModification` | bool or string[] | `false` |
| `assetProtocol` | `{ enable, scope }` | `{ enable: false, scope: [] }` |
| `headers` | object | none |
| `pattern` | object | `{ "use": "brownfield" }` |
| `capabilities` | array | `[]`, see above |

CSP protection exists only if you set it. There is no default.

```json
"csp": {
  "default-src": "'self' customprotocol: asset:",
  "connect-src": "ipc: http://ipc.localhost",
  "img-src": "'self' asset: http://asset.localhost blob: data:",
  "style-src": "'unsafe-inline' 'self'"
}
```

What Tauri injects: local scripts are hashed, external scripts and all `<style>` elements get a per response cryptographic nonce. Elements that already carry a `nonce` attribute are skipped. At runtime the nonces and hashes are appended to `script-src` and `style-src`, and `'self'` is force added to both if absent. Delivery is a `Content-Security-Policy` response header on every platform, emitted by the `tauri://` protocol handler. The `<meta http-equiv>` injection path is v1 behaviour, reachable in v2 only for `data:` URL webviews behind the `webview-data-url` feature.

WebAssembly frontends need `'wasm-unsafe-eval'` in `script-src`.

`dangerousDisableAssetCspModification` takes `true` to disable all injection, or an array of directive names Tauri may not touch. Only `script-src` and `style-src` are ever modified, so those are the only meaningful entries. Disabling this removes XSS protection.

### assetProtocol

```json
"assetProtocol": {
  "enable": true,
  "scope": { "allow": ["$APPCACHE/**/*"], "deny": ["$APPCACHE/**/secrets/**"], "requireLiteralLeadingDot": false }
}
```

The array form is allow only. `requireLiteralLeadingDot` is settable only in the object form. Resolved asset paths are absolute, so `["*/**"]` typically matches nothing: use `$VAR` prefixes or a leading `/`. You must also allow `asset:` and `http://asset.localhost` in `img-src` or `default-src`.

Asset protocol denials go to the **Rust log**, not the webview:

```
asset protocol not configured to allow the path: {path}
```

The webview only sees a failed resource load. Check the terminal.

## CLI

| Command | Use |
|---|---|
| `tauri add <plugin>` | adds crate, JS package, `.plugin(...)` init, and the default permission |
| `tauri permission ls [plugin]` | discover exact identifier spellings |
| `tauri permission new <id>` | create a permission file |
| `tauri permission add <id> [capability]` | add a permission to a capability |
| `tauri permission rm <id>` | remove it and its references; `<plugin>:*` removes all |
| `tauri capability new <id>` | create a capability file |

Set `"$schema": "../gen/schemas/desktop-schema.json"` in every capability file. It gives autocomplete over the permissions your app actually has and catches typos before build.

## Gotchas

- `plugin:` never appears in a capability.
- Core permissions are three segment, plugin permissions are two.
- `fs:default` grants no paths. Permission is not scope.
- `{ "path": "$HOME" }` does not cover `$HOME/**/*`.
- `allow` and `deny` are siblings of `identifier`, not nested in a `scope` object.
- A non-empty `app.security.capabilities` silently ignores unlisted files.
- `deny` always wins.
- `"macOS"` and `"iOS"` are case sensitive and irregular.
- Your own commands are ungated from local origins until `AppManifest::commands` exists.
- A window whose label matches no capability has zero IPC.
- Unix hidden-path globbing silently breaks `$HOME/**` against dotfiles.
- Tauri delivers scope to your commands but does not enforce it.
