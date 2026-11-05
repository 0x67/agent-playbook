#!/bin/sh
# PreToolUse hook (Edit|Write). First Go, Rust, C/C++, Java, Kotlin, or JVM build file touched per session:
# inject reminder to load matching skill and follow its routing table.
input=$(cat)
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
case "$path" in
  *.go|*/go.mod|go.mod|*/go.work|go.work) lang=golang ;;
  *.rs|*/Cargo.toml|Cargo.toml|*/Cargo.lock|Cargo.lock|*/rust-toolchain.toml|rust-toolchain.toml|*/build.rs) lang=rust ;;
  *.c|*.h|*.cc|*.cpp|*.cxx|*.c++|*.hh|*.hpp|*.hxx|*.ipp|*.ixx|*.cppm|*/CMakeLists.txt|CMakeLists.txt|*.cmake|*/CMakePresets.json|CMakePresets.json) lang=cpp ;;
  *.gradle.kts|*/build.gradle|build.gradle|*/settings.gradle|settings.gradle|*/pom.xml|pom.xml|*/gradle.properties|gradle.properties|*/libs.versions.toml|libs.versions.toml) lang=jvm ;;
  *.java) lang=java ;;
  *.kt|*.kts) lang=kotlin ;;
  *) exit 0 ;;
esac
sid=$(printf '%s' "$input" | jq -r '.session_id // "nosession"')
marker="${TMPDIR:-/tmp}/claude-skill-reminder-$lang-$sid"
[ -e "$marker" ] && exit 0
: > "$marker"
case "$lang" in
  golang) gate="gofmt -l, go vet, go build, go test -race, staticcheck" ;;
  rust) gate="cargo fmt --all --check, cargo clippy --workspace --all-targets --all-features -- -D warnings, cargo nextest run --workspace --all-features, cargo test --doc" ;;
  cpp) gate="clang-format --dry-run --Werror, cmake --build, ctest, clang-tidy -p <build dir>, asan preset build + ctest" ;;
  java|jvm) gate="./gradlew spotlessCheck, targeted ./gradlew test --tests, ./gradlew build (Maven: ./mvnw spotless:check, ./mvnw verify)" ;;
  kotlin) gate="./gradlew spotlessCheck or ktlintCheck, detekt when configured, targeted ./gradlew test --tests, ./gradlew build (Maven: ./mvnw verify)" ;;
esac
extra=""
case "$lang" in
  java|kotlin) extra=" Builds, tests, frameworks, and navigation: also skill ai-setup:jvm." ;;
esac
skills="$(cd "$(dirname "$0")/../skills" && pwd)"
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s file touched. If skill `ai-setup:%s` not loaded this session: invoke it now (Skill tool, name ai-setup:%s), read %s/%s/SKILL.md routing table, and Read the matching references/*.md before editing. Run its post-write gate (%s) before reporting done.%s"}}\n' "$lang" "$lang" "$lang" "$skills" "$lang" "$gate" "$extra"
