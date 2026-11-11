#!/bin/sh
set -e
mkdir -p src
cat > Cargo.toml <<'EOF'
[package]
name = "prices"
version = "0.1.0"
edition = "2024"
EOF
cat > src/lib.rs <<'EOF'
/// Parses a price such as "12.50" into integer cents.
pub fn parse_price(s: &str) -> Option<u64> {
    let (whole, frac) = s.split_once('.').unwrap_or((s, "0"));
    let whole: u64 = whole.parse().ok()?;
    let frac: u64 = frac.parse().ok()?;
    Some(whole * 100 + frac)
}
EOF
