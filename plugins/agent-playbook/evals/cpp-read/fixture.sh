#!/bin/sh
set -e
cat > ring_buffer.hpp <<'X'
#pragma once
#include <array>
#include <cstddef>
#include <optional>

template <typename T, std::size_t N>
class RingBuffer {
public:
    bool push(const T& v) {
        if (size_ > N) return false;
        data_[(head_ + size_) % N] = v;
        ++size_;
        return true;
    }
    std::optional<T> pop() {
        if (size_ == 0) return std::nullopt;
        T v = data_[head_];
        head_ = (head_ + 1) % N;
        --size_;
        return v;
    }
private:
    std::array<T, N> data_{};
    std::size_t head_ = 0;
    std::size_t size_ = 0;
};
X
