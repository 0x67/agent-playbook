#!/bin/sh
# PreToolUse (Read|Edit|Write|Bash) and PostToolUse (Grep|Glob|Bash) hook. First Go, Rust, C/C++, Java,
# Kotlin, or JVM build code seen per session: inject a reminder to load the matching skill and follow
# its routing table. Sources, in order: the file being read or edited, a cargo/go/cmake/gradle/mvn
# command, then file paths in search or shell output.
input=$(cat)
event=$(printf '%s' "$input" | jq -r '.hook_event_name // "PreToolUse"')

lang_of_path() {
  case "$1" in
    *.go|*/go.mod|go.mod|*/go.work|go.work) echo golang ;;
    *.rs|*/Cargo.toml|Cargo.toml|*/Cargo.lock|Cargo.lock|*/rust-toolchain.toml|rust-toolchain.toml|*/build.rs) echo rust ;;
    *.c|*.h|*.cc|*.cpp|*.cxx|*.c++|*.hh|*.hpp|*.hxx|*.ipp|*.ixx|*.cppm|*/CMakeLists.txt|CMakeLists.txt|*.cmake|*/CMakePresets.json|CMakePresets.json) echo cpp ;;
    *.gradle.kts|*/build.gradle|build.gradle|*/settings.gradle|settings.gradle|*/pom.xml|pom.xml|*/gradle.properties|gradle.properties|*/libs.versions.toml|libs.versions.toml) echo jvm ;;
    *.java) echo java ;;
    *.kt|*.kts) echo kotlin ;;
  esac
}

lang=""
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[ -n "$path" ] && lang=$(lang_of_path "$path")

if [ -z "$lang" ] && [ "$event" = "PreToolUse" ]; then
  cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
  case " $cmd " in
    *[\ \;\&\|\(]cargo\ *) lang=rust ;;
    *[\ \;\&\|\(]go\ build*|*[\ \;\&\|\(]go\ test*|*[\ \;\&\|\(]go\ run*|*[\ \;\&\|\(]go\ vet*|*[\ \;\&\|\(]go\ mod*|*[\ \;\&\|\(]go\ install*|*[\ \;\&\|\(]go\ generate*|*[\ \;\&\|\(]go\ get*|*[\ \;\&\|\(]go\ work*|*[\ \;\&\|\(]go\ tool*) lang=golang ;;
    *[\ \;\&\|\(]cmake\ *|*[\ \;\&\|\(]ctest\ *) lang=cpp ;;
    *gradlew\ *|*[\ \;\&\|\(]gradle\ *|*mvnw\ *|*[\ \;\&\|\(]mvn\ *) lang=jvm ;;
  esac
fi

if [ -z "$lang" ] && [ "$event" = "PostToolUse" ]; then
  # first source path in the tool output; a path needs a slash, which skips bare names such as docs.rs
  for p in $(printf '%s' "$input" | jq -r '.tool_response | tostring' \
      | grep -oE '[A-Za-z0-9_.-]*/[A-Za-z0-9_./-]*\.(rs|go|java|kts?|c|h|cc|cpp|cxx|hh|hpp|hxx|ipp|ixx|cppm)\b' \
      | grep -v '^//' | head -20); do
    lang=$(lang_of_path "$p")
    [ -n "$lang" ] && break
  done
fi

[ -z "$lang" ] && exit 0
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
printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s code in play. If skill `ai-setup:%s` not loaded this session: invoke it now (Skill tool, name ai-setup:%s), read %s/%s/SKILL.md routing table, and Read the matching references/*.md before reading further or editing. After any edit, run its post-write gate (%s) before reporting done.%s"}}\n' "$event" "$lang" "$lang" "$lang" "$skills" "$lang" "$gate" "$extra"
