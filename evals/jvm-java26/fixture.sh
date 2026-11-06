#!/bin/sh
set -e
mkdir -p gradle/wrapper src/main/kotlin
cat > settings.gradle.kts <<'X'
rootProject.name = "orders"
X
cat > build.gradle.kts <<'X'
plugins {
    kotlin("jvm") version "2.2.0"
    java
}

repositories { mavenCentral() }

java { toolchain { languageVersion = JavaLanguageVersion.of(24) } }
kotlin { jvmToolchain(24) }

dependencies {
    compileOnly("org.projectlombok:lombok:1.18.38")
    annotationProcessor("org.projectlombok:lombok:1.18.38")
}
X
cat > gradle/wrapper/gradle-wrapper.properties <<'X'
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.14-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
X
cat > src/main/kotlin/Main.kt <<'X'
fun main() = println("orders")
X
