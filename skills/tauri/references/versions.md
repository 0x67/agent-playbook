# Tauri Versions

Loaded via `tauri` SKILL.md routing table. Sources: v2.tauri.app/release/tauri/all-versions, GitHub releases, docs.rs/tauri.

## Rule

- `Cargo.lock` is the ceiling, not `Cargo.toml`. `tauri = "2.7"` is a caret range and resolves to the newest 2.x, so the manifest understates what you may use. Read the lockfile.
- `@tauri-apps/api` versions independently of the `tauri` crate. Check `package.json` and `node_modules` separately.
- No API above the resolved version. `cargo check` catches it, but wasting a build cycle on a v1 idiom or a too-new method is avoidable.
- Bumping the Tauri version on someone else's project is a decision, not a chore. Ask.
- `with_webview` is the escape hatch to the platform webview. It breaks on most minors because the underlying `wry`, `windows`, `webview2-com`, `objc2` and `webkit2gtk-rs` bindings bump. Treat it as semver exempt in practice and pin hard if you use it.

## Ladder

| version | date | unlocks |
|---|---|---|
| 2.0 | 2024-10 | baseline v2: iOS and Android targets; rewritten IPC; capabilities and permissions ACL replacing the v1 allowlist; multiwebview (`Webview`, `WebviewBuilder`, `WebviewWindow`, `WebviewWindowBuilder`); split `Manager`/`Emitter`/`Listener` traits; `menu` and `tray` in core; `ipc::Channel`; `plugin::Builder`; `async_runtime`; `dpi` |
| 2.1 | 2024-11 | `app.security.headers`; window config `devtools`, `useHttpsScheme`, `windowClassname`; `Window::set_background_color`; `WebviewWindow::resolve_command_scope`; `PathResolver::home_dir()` on Android; JS `dpi` `Size`/`Position`, `setBackgroundColor`. CLI `tauri remove` |
| 2.2 | 2025-01 | `Builder::on_tray_icon_event`; `Scope::is_forbidden`; `data_store_identifier` (macOS), `extensions_path` (Linux, Windows); badging: `set_badge_count`, `set_overlay_icon` (Windows), `set_badge_label` (macOS); `TrayIconBuilder::show_menu_on_left_click`. Unmanaged state on invoke now returns an error instead of panicking |
| 2.3 | 2025-02 | `Emitter::emit_str`, `emit_str_to`, `emit_str_filter`; `ExitRequestApi` public; `background_throttling`; `navigate` takes `&self`. **`Manager::unmanage` deprecated** for a use after free unsoundness |
| 2.4 | 2025-03 | `is_always_on_top`; cookies: `Webview::cookies`, `cookies_for_url`; `disable_javascript`; `App::run_return`; `AppHandle::request_restart`; `traffic_light_position` (macOS); `Webview::reload`; `build.removeUnusedCommands`; Android content URI paths. `Channel<TSend>` drops the `TSend: Clone` bound. CLI multi `--config` merging |
| 2.5 | 2025-04 | `AppHandle::set_dock_visibility` (macOS); initialization script on all frames; `with_input_accessory_view_builder` (iOS); `allow_link_preview`; `preventOverflow`; `eval` takes `impl Into<String>`. Removed the `WebviewAttributes` re-export from `tauri-runtime`. 2.5.1 adds `data-tauri-drag-region="false"` |
| 2.6 | 2025-06 | `Monitor::work_area()` plus `PhysicalRect`/`LogicalRect`; JS `Monitor.workArea`, `setAutoResize`; `Service-Worker-Allowed` in `app.security.headers`; `x11` cargo feature, default on. `unlisten` now unregisters immediately |
| 2.7 | 2025-07 | `plugin::Builder::js_init_script_on_all_frames`; `AppHandle::plugin_boxed` and `Builder::plugin_boxed`; JS `getBundleType`. Light release |
| 2.8 | 2025-08 | `focusable` plus `Window::set_focusable`; `AppHandle::set_device_event_filter`; `on_document_title_changed`; `on_new_window`; `PluginHandle::run_mobile_plugin_async`; `set_cookie` / `delete_cookie`; `set_simple_fullscreen`; `WebviewWindow::on_webview_event`; submenu icons. CLI custom watch folders |
| 2.9 | 2025-10 | `scroll_bar_style` plus `scrollBarStyle` config; mobile exit and back button events, `app.onBackButtonPress`; Android plugin hooks `onStop`, `onDestroy`, `onRestart`, `onConfigurationChanged`; async Swift plugin methods. CLI `--no-sign`, `autoIncrementVersionCode`, `ios run` / `android run`, deep-link universal domains |
| 2.10 | 2026-02 | thin. `WebviewWindow::set_simple_fullscreen` for parity. Breaking for `with_webview` users: `webkit2gtk-rs` 2.0.2, `wry` 0.54 |
| 2.11 | 2026-04 | `PredefinedMenuItem::bring_all_to_front` (macOS); **`rename` attribute on `#[tauri::command]`**; `data-tauri-drag-region="deep"`; `general_autofill_enabled`; `eval_with_callback`; file associations on Android and iOS; `RunEvent::Opened` on Android; `Suspended`/`Resumed` on mobile; **multiple windows on Android and iOS**; `dbus` cargo feature, default on and required for Linux theme detection. CLI `uninstallerIcon`, `bundle.windows.minimumWebview2Version`, `--archive-only` for iOS |

Latest stable at the time of writing: `tauri` 2.11.5, 2026-07-01. Ecosystem at that point: `tauri-cli` and `@tauri-apps/cli` 2.11.4, `@tauri-apps/api` 2.11.1, `tauri-build` 2.6.3, `wry` 0.55, `tao` 0.35.

If the pinned version is newer than this table, read the changelog rather than assuming. This table ends where its sources did.

## Deprecations

- `Manager::unmanage`, deprecated 2.3.0, unsound. Model removable state as `Mutex<Option<T>>`.
- `TrayIconBuilder::menu_on_left_click` and the `menuOnLeftClick` config key, deprecated 2.2.0. The **Rust method still works**: it is an alias that calls the same inner setter, so do not delete a live `.menu_on_left_click(false)` call. The **config key** is effectively dead, because `showMenuOnLeftClick` is applied after it and defaults to `true`. Prefer `show_menu_on_left_click` / `showMenuOnLeftClick` in new code.
- `nsis.minimumWebview2Version`, superseded by `bundle.windows.minimumWebview2Version` in 2.11.

Signature relaxations that are source compatible, not breaking: `navigate` to `&self` (2.3); `eval` and `Builder::invoke_system` to `impl Into<String>` / `AsRef<str>` (2.5); `js_init_script` to `impl Into<String>` (2.7); `AppHandle::remove_plugin` to `&str` (2.8); `Channel<TSend>` dropping `Clone` (2.4).

Two default-on cargo features hide platform capability if disabled: `x11` (2.6) and `dbus` (2.11, required for Linux theme detection).

## MSRV

Declared `rust-version` is **1.77.2** and has not moved across the whole shipped 2.x line. 2.0.0 briefly required 1.78; 2.0.1 reverted to 1.77.2 to keep Windows 7 support, and that revert still stands. There is no per minor MSRV bump policy in 2.x.

The declared MSRV understates the effective one: `tauri-cli`'s dependency tree already requires a higher toolchain on Windows. If you are pinning a toolchain, test it rather than trusting 1.77.2.

## Tauri 3

The 3.0 milestone is open with no due date and nearly every item labelled breaking. The forcing function is Linux GTK: GTK3 is unmaintained and has a known unsoundness in glib, so the migration to GTK4 and WebKitGTK 6.0 cascades through the crate graph. Other milestone items include dropping Windows 7 support, which is exactly what pinned MSRV at 1.77.2, `schemars` 1.x, `WebviewUrl` navigation changes, removal of v1 compatibility code, and cleanup of top level exports.

`tauri 3.0.0-alpha.0` and `alpha.1` are published on crates.io (September 2026), with `@tauri-apps/api` and `@tauri-apps/cli` alphas on the npm `next` tag. **`max_stable_version` is still 2.11.5**, so do not write production code against them. Note the v3 alphas declare `rust-version = 1.95`, a large jump from 2.x's 1.77.2. Do not assume a v2 API survives into v3 without checking.
