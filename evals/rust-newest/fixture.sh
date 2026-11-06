#!/bin/sh
set -e
mkdir -p src
cat > Cargo.toml <<'X'
[package]
name = "wire"
version = "0.1.0"
edition = "2024"
rust-version = "1.99"
X
cat > rust-toolchain.toml <<'X'
[toolchain]
channel = "1.99"
X
cat > src/lib.rs <<'X'
/// Decodes a payload from the wire, replacing invalid UTF-8 with U+FFFD.
pub fn decode(bytes: Vec<u8>) -> String {
    String::from_utf8_lossy(&bytes).into_owned()
}
X
