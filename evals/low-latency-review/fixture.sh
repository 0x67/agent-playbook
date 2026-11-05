#!/bin/sh
set -e
mkdir -p src
cat > Cargo.toml <<'X'
[package]
name = "feed"
version = "0.1.0"
edition = "2024"

[dependencies]
crossbeam-channel = "0.5"
log = "0.4"
X
cat > src/feed.rs <<'X'
use crossbeam_channel::{unbounded, Receiver, Sender};
use std::net::UdpSocket;

pub struct Tick {
    pub symbol: String,
    pub price: u64,
    pub qty: u64,
}

pub fn channel() -> (Sender<Tick>, Receiver<Tick>) {
    unbounded()
}

pub fn run(sock: UdpSocket, tx: Sender<Tick>) -> std::io::Result<()> {
    let mut buf = [0u8; 2048];
    loop {
        let (n, _) = sock.recv_from(&mut buf)?;
        let frame = buf[..n].to_vec();
        log::info!("got frame {:?}", frame);
        let tick = decode(&frame);
        tx.send(tick).unwrap();
    }
}

fn decode(b: &[u8]) -> Tick {
    let symbol = String::from_utf8_lossy(&b[0..8]).trim().to_string();
    let price = u64::from_be_bytes(b[8..16].try_into().unwrap());
    let qty = u64::from_be_bytes(b[16..24].try_into().unwrap());
    Tick { symbol, price, qty }
}
X
echo 'pub mod feed;' > src/lib.rs
git init -q && git add -A
