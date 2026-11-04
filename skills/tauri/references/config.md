# Tauri Config and CLI

Loaded via `tauri` SKILL.md routing table. Sources: `config.schema.json` (`$id` `https://schema.tauri.app/config/2.11.5`), `tauri-utils::config`, `tauri-cli` clap definitions, v2.tauri.app/reference/config.

## Top level

The schema sets `additionalProperties: false` with exactly nine keys. **`identifier` is the only required one.**

| Key | Notes |
|---|---|
| `$schema` | pointer only |
| `productName` | pattern excludes `/ \ : * ? " < > \|`. Falls back to the Cargo package name |
| `mainBinaryName` | renames the cargo output binary. Must not include `.exe` |
| `version` | semver, **or a path to a `package.json`** whose version is read. Falls back to `Cargo.toml` |
| `identifier` | **required**, reverse DNS, `A-Za-z0-9`, `-`, `.` only. The default `com.tauri.dev` is rejected by `tauri build` |
| `app` | see below |
| `build` | see below |
| `bundle` | see below |
| `plugins` | free form map, see below |

Formats: `tauri.conf.json`, `tauri.conf.json5` (needs the `config-json5` feature on **both** `tauri-build` and `tauri`), `Tauri.toml` (needs `config-toml`). `.json` is parsed as JSON5 first, falling back to strict JSON for the error message.

## build

```
runner                 string | { cmd, cwd?, args? }
devUrl                 string
frontendDist           string dir | string url | string[]
beforeDevCommand       string | { script, cwd?, wait? }     wait defaults false
beforeBuildCommand     string | { script, cwd? }            no wait key
beforeBundleCommand    string | { script, cwd? }            no wait key
features               string[]
removeUnusedCommands   bool    false
additionalWatchFolders string[] []
```

`frontendDist` accepts a directory (embedded recursively), an external URL (nothing embedded), or an explicit array of files.

Hooks receive `TAURI_ENV_PLATFORM`, `TAURI_ENV_ARCH`, `TAURI_ENV_FAMILY`, `TAURI_ENV_PLATFORM_VERSION`, `TAURI_ENV_PLATFORM_TYPE`, `TAURI_ENV_DEBUG`.

## app

```
windows          WindowConfig[]   []
security         SecurityConfig   see permissions.md
trayIcon         TrayIconConfig   null
macOSPrivateApi  bool             false
withGlobalTauri  bool             false
enableGTKAppId   bool             false
```

- `macOSPrivateApi` is required for `transparent: true` on macOS and blocks App Store acceptance.
- `trayIcon` requires `iconPath`. `menuOnLeftClick` is deprecated and effectively dead: `showMenuOnLeftClick` is applied after it and defaults to `true`. Use `showMenuOnLeftClick`. The Rust builder method `menu_on_left_click` is a working alias, not a no-op.

### withGlobalTauri

`false` by default. When `true`, Tauri injects the IIFE build of `@tauri-apps/api` plus each installed plugin's global script as webview init scripts, giving you `window.__TAURI__.core.invoke`, `window.__TAURI__.event`, and `window.__TAURI__.<plugin>`.

Set it only for plain HTML frontends with no bundler. With a bundler, import from `@tauri-apps/api/*` and leave this off.

`window.__TAURI_INTERNALS__` is present either way. The flag governs only the friendly surface.

## WindowConfig

61 keys, none required. The ones that matter, with real defaults:

```
label               "main"          must be alphanumeric
create              true
url                 "index.html"    app relative path, external http(s) URL, or custom protocol
title               "Tauri App"
width / height      800 / 600
minWidth ...        null
resizable           true
fullscreen          false
decorations         true
transparent         false           needs macOSPrivateApi on macOS
center              false
visible             true
focus               true
dragDropEnabled     true
zoomHotkeysEnabled  false
titleBarStyle       "Visible"       PascalCase: "Visible" | "Transparent" | "Overlay"
hiddenTitle         false
devtools            null            null means enabled in debug; release also needs the devtools feature
useHttpsScheme      false
backgroundColor     null            "#fff" / "#ffffff" / "#ffffffff" or a 3 or 4 element 0-255 array
shadow              true
allowLinkPreview    true
scrollBarStyle      "default"
generalAutofillEnabled true
```

`label` is the security boundary. Capabilities glob over labels, not titles.

## bundle

```
active                 false        tauri build bundles only when active or --bundles was passed
targets                "all"        or one BundleType, or an array
createUpdaterArtifacts false        or the string "v1Compatible" for v1 migration only
icon                   []
resources              string[] of paths/globs, or an object map source -> target
externalBin            string[]     resolved as name-{target-triple}{.exe}
fileAssociations, publisher, homepage, copyright, license, licenseFile, category,
shortDescription, longDescription, useLocalToolsDir
windows / linux / macOS / iOS / android      note the casing
```

`BundleType` has exactly seven values, all lowercase: `deb`, `rpm`, `appimage`, `msi`, `nsis`, `app`, `dmg`. There is no `updater` target in v2 config and no mobile target: mobile artifacts come from `tauri android build` and `tauri ios build`.

Per platform highlights:

- `windows`: `certificateThumbprint`, `digestAlgorithm`, `timestampUrl`, `tsp`, `allowDowngrades` (default true), `minimumWebview2Version`, `signCommand`, `wix`, `nsis`. `webviewInstallMode` is a tagged object, default `{ "type": "downloadBootstrapper", "silent": true }`; other types are `skip`, `embedBootstrapper`, `offlineInstaller`, `fixedRuntime`.
- `macOS`: `frameworks`, `files`, `bundleVersion`, `bundleName`, `minimumSystemVersion` (default `"10.13"`), `signingIdentity`, `hardenedRuntime` (default true), `entitlements`, `providerShortName`, `infoPlist`, `dmg`. An `Info.plist` next to the config file is merged automatically.
- `linux`: `appimage`, `deb`, `rpm` sub-objects with `depends`, `files`, install and remove scripts; `rpm` adds `release`, `epoch`, `compression`.
- `iOS`: `template`, `frameworks`, `developmentTeam` (or `APPLE_DEVELOPMENT_TEAM`), `bundleVersion`, `minimumSystemVersion` (default `"14.0"`), `infoPlist`.
- `android`: `minSdkVersion` (default 24), `versionCode`, `autoIncrementVersionCode`, `debugApplicationIdSuffix`.

## Platform config files and --config

| Target | JSON | JSON5 | TOML |
|---|---|---|---|
| macOS | `tauri.macos.conf.json` | `tauri.macos.conf.json5` | `Tauri.macos.toml` |
| Windows | `tauri.windows.conf.json` | `.json5` | `Tauri.windows.toml` |
| Linux | `tauri.linux.conf.json` | `.json5` | `Tauri.linux.toml` |
| Android | `tauri.android.conf.json` | `.json5` | `Tauri.android.toml` |
| iOS | `tauri.ios.conf.json` | `.json5` | `Tauri.ios.toml` |

Merge order: base config, then the platform file for the current target, then all `--config` values folded left to right. `--config` always wins.

Semantics are **RFC 7396 JSON Merge Patch**: deep and key by key for objects, **arrays replaced wholesale, never concatenated**. This bites on `app.windows`: a platform file listing one window replaces all of them, and unspecified fields of that window fall back to **schema defaults**, not to the base file's values.

An explicit `null` deletes a key, in a platform file or a `--config` file. The one exception is between multiple `--config` values folded with each other, where `null` does not delete.

`--config` parsing: a string starting with `{` is inline JSON, anything else is a file path dispatched by extension.

```sh
tauri build -c ./tauri.beta.conf.json -c '{"productName":"MyApp Beta","identifier":"com.example.beta"}'
```

## plugins

Free form map, unvalidated by the core schema. Each plugin deserializes its own sub-object. The key is the plugin's registered kebab-case name, matching the crate suffix: `updater`, `deep-link`, `single-instance`, `window-state`, `cli`, `fs`, `shell`.

```json
{
  "bundle": { "createUpdaterArtifacts": true },
  "plugins": {
    "updater": {
      "endpoints": ["https://releases.example.com/{{target}}/{{arch}}/{{current_version}}"],
      "pubkey": "<contents of myapp.key.pub>",
      "windows": { "installMode": "passive", "installerArgs": [] }
    }
  }
}
```

`pubkey` is the only required updater field. `endpoints` must be https or the release build fails. Template vars are `{{target}}`, `{{arch}}`, `{{current_version}}`. `windows.installMode` is `passive` (default), `basicUi`, or `quiet`.

## Plugins in Rust

```rust
tauri::Builder::default()
    .plugin(tauri_plugin_fs::init())
    .plugin(tauri_plugin_dialog::init())
```

`tauri add <plugin>` does the crate, the npm package, the `.plugin(...)` line and the default permission in one step. Prefer it over hand wiring. A plugin present in the ACL but never registered passes the permission check and then fails at dispatch.

## CLI

| Command | Purpose |
|---|---|
| `init` | scaffold `src-tauri/` in an existing directory |
| `dev` | run with file watching |
| `build` | release build plus bundles |
| `bundle` | bundle an already built app, runs `beforeBundleCommand` |
| `android` / `ios` | `init`, `dev`, `build`, `run`. `ios` exists only on macOS |
| `info` | environment, versions, config. `--interactive` |
| `add` / `remove` | plugin wiring |
| `plugin` | plugin authoring scaffolds |
| `icon` | generate platform icons from one source image |
| `signer` | `generate` an updater keypair, `sign` a file |
| `permission` / `capability` | ACL management, see permissions.md |
| `inspect` | `wix-upgrade-code` prints the derived MSI upgrade code |
| `migrate` | v1 to v2, out of scope here |
| `completions` | shell completions |

`dev` flags: `-f/--features`, `-t/--target`, `-c/--config`, `--release`, `--no-watch`, `--additional-watch-folders`, `--no-dev-server`, `--no-dev-server-wait`, `--port`, `-e/--exit-on-panic`. **There is no `--debug` on `dev`**; dev is debug by default and `--release` is the opposite switch.

`build` flags: `-d/--debug`, `-t/--target <rust triple>`, `-b/--bundles <formats>`, `--no-bundle`, `-f/--features`, `-c/--config`, `--ci`, `--no-sign`, `--skip-stapling`, `--ignore-version-mismatches`.

`--target` is the **Rust target triple**. The flag that picks bundle formats is `-b/--bundles`.

## Mobile

`tauri android init` generates `src-tauri/gen/android`, a full Gradle project. `tauri ios init` generates `src-tauri/gen/apple`, an XcodeGen project customizable via `bundle.iOS.template`.

The scaffolded `src-tauri/.gitignore` contains only `/target/` and `/gen/schemas`, so **`gen/android` and `gen/apple` are intended to be committed**. They hold hand edited native files: `AndroidManifest.xml`, `Info.plist`, Kotlin and Swift sources, `build.gradle.kts`. Regenerable with `<platform> init` only if you have made no edits. Keep `keystore.properties` out of source control.

Dev on a physical device or with `--host` sets `TAURI_DEV_HOST` and rewrites `devUrl` to a network address, so **your frontend dev server must listen on `0.0.0.0`**.

`tauri android build`: `--apk`, `--aab`, `--split-per-abi`, `-t/--target <abi...>`. With neither `--apk` nor `--aab`, both are produced.
`tauri ios build`: `--export-method <app-store-connect|release-testing|debugging>`, `--build-number`, `--no-sign`, `--archive-only`.

## Updater

Crate `tauri-plugin-updater`, package `@tauri-apps/plugin-updater`. A plugin in v2, not core as in v1. Usually paired with `tauri-plugin-process` for `relaunch()`.

```sh
tauri signer generate -w ~/.tauri/myapp.key
```

Writes `myapp.key` and `myapp.key.pub`. The **contents** of the `.pub` file go in `plugins.updater.pubkey`.

Build time signing uses env vars, never committed: `TAURI_SIGNING_PRIVATE_KEY` (path or raw content), `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`.

Add `updater:default` to a capability.
