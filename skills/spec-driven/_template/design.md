# <Spec Name>: Design

| Field        | Value                                  |
| ------------ | -------------------------------------- |
| Status       | Draft                                  |
| Requirements | REQ-A1..A<n>, REQ-B1..B<n>, ...        |

## 1. Architecture

```
<ASCII diagram of the data/control flow, components,
boundaries between subsystems, where the change lands>
```

Brief prose: <2-3 sentences naming the change touchpoints>.

## 2. <Workstream A> design

### 2.1 Current shape

```rust
// existing signature or relevant snippet from code (quoted, not paraphrased)
```

### 2.2 New shape

```rust
// proposed signature or snippet
```

### 2.3 Rationale

<why this shape; what alternatives were considered; tradeoffs. Approach trial ran: winner, one-line reason, link to `trial.md`. Considered and skipped: `No trial: <reason>`>

## 3. <Workstream B> design

(same structure as §2)

## 4. Error strategy

| Path                                  | Error                | Behavior                                  |
| ------------------------------------- | -------------------- | ----------------------------------------- |
| `path::function` fails on X           | `ErrorKind::X`       | <propagate/retry/log/skip>                |
| ...                                   | ...                  | ...                                       |

## 5. Files in scope

| File                                  | Action                                  |
| ------------------------------------- | --------------------------------------- |
| `path/to/file.rs`                     | <new | extend | rewrite | delete>      |
| ...                                   | ...                                     |

## 6. Risks

| Risk                                  | Mitigation                              |
| ------------------------------------- | --------------------------------------- |
| <risk statement>                      | <how it is countered>                   |

## 7. Validation mapping

| REQ    | Validation                                                       |
| ------ | ---------------------------------------------------------------- |
| A1     | <unit / integration / regression command + assertion>            |
| A2     | ...                                                              |
| B1     | ...                                                              |

## 8. Future extensions (out of scope)

- <follow-up item tracked elsewhere>

## Source verification

- `path/to/file.rs:LINE`: <claim quoted from code>
- `path/to/other.rs:LINE`: <claim quoted from code>
- ...
