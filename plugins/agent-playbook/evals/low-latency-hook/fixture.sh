#!/bin/sh
set -e
mkdir -p src
cat > Cargo.toml <<'X'
[package]
name = "feed"
version = "0.1.0"
edition = "2024"

[dependencies]
disruptor = "4.4"
crossbeam-channel = "0.5"
X
cat > src/pipeline.rs <<'X'
use disruptor::*;

#[derive(Default)]
pub struct Quote {
    pub instrument: u32,
    pub price: u64,
}

pub fn start(on_quote: impl FnMut(&Quote) + Send + 'static) -> impl Producer<Quote> {
    let mut on_quote = on_quote;
    build_single_producer(1024, Quote::default, BusySpin)
        .handle_events_with(move |q: &Quote, _seq: Sequence, _end: bool| on_quote(q))
        .build()
}
X
echo 'pub mod pipeline;' > src/lib.rs
git init -q && git add -A
