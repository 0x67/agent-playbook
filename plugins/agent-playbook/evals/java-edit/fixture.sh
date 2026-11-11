#!/bin/sh
set -e
mkdir -p src/main/java/com/example
cat > settings.gradle.kts <<'X'
rootProject.name = "money"
X
cat > build.gradle.kts <<'X'
plugins { java }
java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }
X
cat > src/main/java/com/example/Money.java <<'X'
package com.example;

public record Money(long cents, String currency) {}
X
