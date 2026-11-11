#!/bin/sh
# PreToolUse (Read|Edit|Write|Bash) hook. The first edit of Go, Rust, C/C++, Java, Kotlin, or JVM build
# code per session, or the first cargo/go/cmake/gradle/mvn command, injects a reminder to load the
# matching skill and run its post-write gate. Reads get no language reminder: in benchmarks the skills
# changed no review answer and added about 70% to cost. The one exception is a Rust repo whose
# Cargo.toml has a latency crate, where the first read already points at the low-latency skill.
input=$(cat)
tool=$(printf '%s' "$input" | jq -r '.tool_name // empty')

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
case "$tool" in
  Read|Edit|Write)
    path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
    [ -n "$path" ] && lang=$(lang_of_path "$path")
    ;;
  Bash)
    cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
    case " $cmd " in
      *[\ \;\&\|\(]cargo\ *) lang=rust ;;
      *[\ \;\&\|\(]go\ build*|*[\ \;\&\|\(]go\ test*|*[\ \;\&\|\(]go\ run*|*[\ \;\&\|\(]go\ vet*|*[\ \;\&\|\(]go\ mod*|*[\ \;\&\|\(]go\ install*|*[\ \;\&\|\(]go\ generate*|*[\ \;\&\|\(]go\ get*|*[\ \;\&\|\(]go\ work*|*[\ \;\&\|\(]go\ tool*) lang=golang ;;
      *[\ \;\&\|\(]cmake\ *|*[\ \;\&\|\(]ctest\ *) lang=cpp ;;
      *gradlew\ *|*[\ \;\&\|\(]gradle\ *|*mvnw\ *|*[\ \;\&\|\(]mvn\ *) lang=jvm ;;
    esac
    ;;
esac
[ -z "$lang" ] && exit 0

sid=$(printf '%s' "$input" | jq -r '.session_id // "nosession"')
event=$(printf '%s' "$input" | jq -r '.hook_event_name // "PreToolUse"')
skills="$(cd "$(dirname "$0")/../skills" && pwd)"

latency=""
if [ "$lang" = rust ]; then
  lowlat_marker="${TMPDIR:-/tmp}/claude-skill-reminder-lowlat-$sid"
  if [ ! -e "$lowlat_marker" ]; then
    # direct dependencies only (Cargo.toml, not Cargo.lock), so a transitive bytes or crossbeam does not count;
    # the skill loads only when a latency crate is present, the shared crates then add their pages
    deps=$(git ls-files -- 'Cargo.toml' '*/Cargo.toml' 2>/dev/null | head -400 | tr '\n' '\0' |
      xargs -0 grep -hoE '^[[:space:]]*(disruptor|io-uring|rtrb|core_affinity|hdrhistogram|zerocopy|crossbeam[a-z-]*|bytes|criterion|loom)[[:space:]]*=' 2>/dev/null |
      sed -E 's/^[[:space:]]*//; s/[[:space:]]*=$//' | sort -u)
    if printf '%s\n' "$deps" | grep -qxE 'disruptor|io-uring|rtrb|core_affinity|hdrhistogram|zerocopy'; then
      pages=$(printf '%s\n' "$deps" | sed -E 's/^crossbeam.*|^rtrb$/crossbeam/; s/^(bytes|zerocopy)$/bytes-zerocopy/; s/^(criterion|hdrhistogram|loom)$/measure/; s/^core_affinity$/pinning/' |
        sort -u | sed 's|.*|references/rust/&.md|' | tr '\n' ' ' | sed 's/ $//')
      latency="Latency crates in this repo ($(printf '%s' "$deps" | tr '\n' ' ' | sed 's/ $//')): before reviewing or editing this code, load skill agent-playbook:low-latency ($skills/low-latency/SKILL.md) and read $pages."
      : > "$lowlat_marker"
    fi
  fi
fi

if [ "$tool" = Read ]; then
  [ -z "$latency" ] && exit 0
  printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}\n' "$event" "$latency"
  exit 0
fi

marker="${TMPDIR:-/tmp}/claude-skill-reminder-$lang-$sid"
if [ -e "$marker" ]; then
  [ -z "$latency" ] && exit 0
  printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}\n' "$event" "$latency"
  exit 0
fi
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
  java|kotlin) extra=" Builds, tests, frameworks, and navigation: also skill agent-playbook:jvm." ;;
esac
[ -n "$latency" ] && extra="$extra $latency"
printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s code is being changed or built. If skill `agent-playbook:%s` is not loaded this session: invoke it now (Skill tool, name agent-playbook:%s), read %s/%s/SKILL.md routing table, and Read the matching references/*.md before editing further. After the edit, run its post-write gate (%s) before reporting done.%s"}}\n' "$event" "$lang" "$lang" "$lang" "$skills" "$lang" "$gate" "$extra"
