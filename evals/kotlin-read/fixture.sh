#!/bin/sh
set -e
mkdir -p src/main/kotlin
cat > src/main/kotlin/Retry.kt <<'X'
import kotlinx.coroutines.delay

suspend fun <T> retry(times: Int, block: suspend () -> T): T? {
    repeat(times) { attempt ->
        val result = runCatching { block() }
        if (result.isSuccess) return result.getOrNull()
        delay(100L * (attempt + 1))
    }
    return null
}
X
