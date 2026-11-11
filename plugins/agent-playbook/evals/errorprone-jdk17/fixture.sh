#!/bin/sh
set -e
mkdir -p src/main/java/app
cat > settings.gradle.kts <<'X'
rootProject.name = "billing"
X
cat > build.gradle.kts <<'X'
plugins {
    java
}

repositories { mavenCentral() }

java { toolchain { languageVersion = JavaLanguageVersion.of(17) } }
X
cat > src/main/java/app/Billing.java <<'X'
package app;

public final class Billing {
    public static long cents(double amount) {
        return Math.round(amount * 100);
    }
}
X
