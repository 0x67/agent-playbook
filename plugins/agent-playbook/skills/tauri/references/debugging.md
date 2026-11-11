# Tauri Debugging

Loaded via `tauri` SKILL.md routing table. Sources: `tauri` webview IPC handler and `authority.rs` source, plugin error enums, v2.tauri.app/security/runtime-authority.

Read this when something builds and then does not work. Most Tauri runtime failures are one of five things.

## Rule zero

**Debug builds name the fix. Release builds do not.** The detailed ACL diagnostics are behind `#[cfg(debug_assertions)]`. Never diagnose a permission problem against a release build; you get one useless line.

## 1. Command denied by the ACL

The runtime authority rejects before your function body runs. It arrives as a **rejected Promise from `invoke`**, a plain string, not an `Error`. It is not a Rust panic, nothing is written to the Rust log, and the process keeps running. If unhandled it shows in the webview devtools console as an uncaught promise error.

Release build, the whole message:

```
Command plugin:fs|read_text_file not allowed by ACL
```

Debug build, five shapes. `command_pretty_name` is `<plugin>.<command>` with a dot, or the bare name for app commands.

**Plugin not in the ACL at all.** The plugin is not in `Cargo.toml` or not registered.
```
unknown-plugin.my-command not allowed. Plugin not found
```

**Plugin known, command not in any permission.** Wrong command name or wrong plugin.
```
myplugin.unknown-command not allowed. Command not found
```

**Allowed somewhere, not here.** The common forgotten window label. Compare against the `allowed on:` line.
```
myplugin.my-command not allowed on window "other-window", webview "any-webview", URL: local

allowed on: [windows: "main-*", URL: local]

referenced by: capability: maincap, permission: allow-command
```
If nothing matched at all the middle line reads `command not allowed on any window/webview/URL context`.

**No capability grants it on this origin.** The most actionable one: it names the permissions to add.
```
<cmd> not allowed on origin [<origin>]. Please create a capability that has this origin on the context field.

Found matches for: - context: [local], referenced by: capability: maincap, permission: allow-command

Permissions associated with this command: fs:allow-read-text-file, fs:default
```

**Explicitly denied.** A `deny` permission matched. Follow the `referenced by:` line to find it.
```
<cmd> explicitly denied on origin <origin>

referenced by: capability: maincap, permission: deny-command
```

## 2. Permission granted, scope missing

Different error, very common. The permission is enabled and the command still fails. In a **debug** build a scope miss reads:

```
forbidden path: /home/user/notes.txt, maybe it is not allowed on the scope for `allow-read-text-file` permission in your capability file
```

The **bare** form, with no trailing clause, is the release build message for the same thing, and in a debug build means something different: an explicit `deny` matched.

```
forbidden path: /home/user/notes.txt
```

`fs:default` grants no paths. Switch to the object form:

```json
{ "identifier": "fs:allow-exists", "allow": [{ "path": "$HOME" }, { "path": "$HOME/**/*" }] }
```

Other `fs` errors in the same family: `invalid glob pattern: {0}`, `URL is not a valid path`, `Unsafe PathBuf: {0}`.

If the path is a dotfile and the glob looks correct, it is the leading dot rule. See permissions.md.

## 3. Asset will not load

Asset protocol denials go to the **Rust log**, not the webview. The webview only shows a failed resource load.

```
asset protocol not configured to allow the path: {path}
asset protocol path "{path}" is not valid: {e}
```

Check the terminal. Then check that `assetProtocol.enable` is true, that the path is in `assetProtocol.scope`, and that your CSP allows `asset:` and `http://asset.localhost`.

## 4. Invoke rejected for a non-ACL reason

- Argument name mismatch: `InvalidArgs`. Rust `some_arg` is JS `someArg` unless the command sets `rename_all = "snake_case"`.
- Missing managed state: ``state not managed for field `{key}` on command `{name}`. You must call `.manage()` before using this command``.
- Command name typo in `invoke`: the command is simply not found.

None of these are compile errors. All are runtime.

## 5. Builds in dev, breaks in release

- ACL diagnostics vanish, per rule zero.
- `devtools` is null by default, meaning debug only. Release also needs the `devtools` cargo feature.
- `devUrl` is not used; `frontendDist` is. A path that worked against the dev server may not exist in the embedded bundle.
- Updater endpoints must be https in release; dev only warns.
- Release uses the platform config file merged over the base. Check for a `tauri.<platform>.conf.json` replacing an array you expected to keep. Merge patch replaces arrays wholesale.

## What the build catches, and what it does not

Caught by `tauri-build`, fails `cargo build`:

| Error | Message |
|---|---|
| unknown permission | `unknown permission {permission} for {key}` |
| unknown plugin ACL | `unknown ACL for {key}, expected one of {available}` |
| bad set member | `permission {permission} not found from set {set}` |
| duplicate capability | ``capability with identifier `{identifier}` already exists`` |
| malformed files | `unknown permission format`, `unknown capability format` |
| bad remote URL | panic: `invalid URL pattern for remote URL {url}: {e}` |
| misspelled `platforms` value | `unknown variant` from the capability deserializer |

So a typo'd permission identifier is the good case: it fails the build.

**Not caught, runtime only:**

- Window or webview label mismatch. Labels are strings; nothing validates them against windows you actually create.
- Missing scope on a scoped command.
- A window created at runtime whose label matches no capability.
- A remote origin not covered by any `remote.urls`.
- A plugin in the ACL but never registered in Rust. The permission check passes and dispatch fails.

## Ordered checklist

1. Run a debug build. Read which of the five ACL shapes you got.
2. Check the window **label**, not the title: `getCurrentWindow().label` in JS. Match it against every capability's `windows` and `webviews` globs. Remember that matching `windows` enables all webviews of that window.
3. Confirm the capability is loaded. A non-empty `app.security.capabilities` silently ignores unlisted files in `capabilities/`.
4. Check `platforms`. A misspelling would have failed the build, so if it built, the value is valid and simply does not include the current target. That is silent by design.
5. Distinguish denial from scope. `not allowed` is a capability problem. `forbidden path:` with a trailing `maybe it is not allowed on the scope for ...` clause is a missing scope; the bare form in a debug build is an explicit `deny`.
6. Inspect what actually compiled in: `src-tauri/gen/schemas/acl-manifests.json` and `capabilities.json`.
7. For your own commands, remember they are ungated from local origins unless `build.rs` declares `AppManifest::commands`. If your own command is denied, either that manifest exists or the call came from a remote origin.
8. Log the rejection: `invoke('cmd').catch(e => console.error(e))`. The string is the whole diagnostic.
9. `cargo tauri permission ls [plugin]` for exact identifier spellings.

## Doc snippets that do not compile

Published Tauri docs contain examples that fail to build. Verify against `cargo doc` for your pinned version rather than copying:

- `event.data` and `event.id` as fields. They are private. Use `event.payload()` and `event.id()`.
- `PathResolver::app_dir()`. Does not exist in v2; use `app_config_dir()`, `app_data_dir()`, `app_local_data_dir()`, `app_cache_dir()`, `app_log_dir()`.
- `tauri::GlobalShortcutManager`. Removed in v2; use `tauri-plugin-global-shortcut`.
- `Channel<&[u8]>` presented as a byte stream. It sends JSON number arrays. See ipc.md.
