# <Spec Name>: Validation

| Field        | Value                                  |
| ------------ | -------------------------------------- |
| Status       | Draft                                  |
| Requirements | REQ-A1..A<n>, REQ-B1..B<n>, ...        |

## Validation ladder

### Level 1: Compile

```bash
cargo check -p <crate>
cargo check --workspace
```

Zero warnings in changed crates.

### Level 2: Unit tests

```bash
cargo test -p <crate>
```

| Test                                            | REQ        | Validates                                   |
| ----------------------------------------------- | ---------- | ------------------------------------------- |
| `<module>::<test_name>`                         | A1         | <one-line behavior>                         |
| `<module>::<test_name>`                         | A2, B1     | <one-line behavior>                         |

### Level 3: Integration tests

```bash
cargo test -p <crate> -- --ignored
```

| Test                                            | REQ        | Validates                                   |
| ----------------------------------------------- | ---------- | ------------------------------------------- |
| `<test_name>`                                   | B1         | <end-to-end behavior over fixture>          |

### Level 4: Manual / E2E

```bash
# <description>
<exact command>
# expected: <observable result>
```

## Acceptance criteria

| ID     | Criterion                                                  | REQ        | Verify                                      |
| ------ | ---------------------------------------------------------- | ---------- | ------------------------------------------- |
| AC-A1  | <observable post-condition>                                | A1         | <command or test name>                      |
| AC-A2  | <observable post-condition>                                | A2         | <command or test name>                      |
| AC-B1  | <observable post-condition>                                | B1         | <command or test name>                      |

## Regression guard

- <list of behaviors that must NOT change>
- <existing tests that must still pass>
- <bench numbers within ±N% of baseline>
- `cargo clippy --workspace -- -D warnings` exit 0
- `lat check` exit 0 (if workspace uses lat.md)

## Out-of-scope follow-up

- <follow-up tracked separately>
