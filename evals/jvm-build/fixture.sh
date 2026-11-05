#!/bin/sh
set -e
cat > settings.gradle.kts <<'X'
rootProject.name = "money"
X
cat > build.gradle.kts <<'X'
plugins { java }
repositories { mavenCentral() }
java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }
X
