# <Spec Name>: Tasks

| Field        | Value                                  |
| ------------ | -------------------------------------- |
| Status       | Draft                                  |
| Requirements | REQ-A1..A<n>, REQ-B1..B<n>, ...        |
| Base commit  | <`git rev-parse --short HEAD` when written> |

## Dependency graph

```
TASK-A1 ──┐
          ▼
       TASK-A2 ──► TASK-A3
                       │
                       ▼
TASK-B1 ──────────► TASK-B2
```

## Milestones

- **M1: <name>** (TASK-A1, A2): <brief outcome>
- **M2: <name>** (TASK-A3): <brief outcome>
- **M3: <name>** (TASK-B1, B2): <brief outcome>

---

## TASK-A1: <short title>

**Status**: TODO (TODO | DONE | BLOCKED (<reason>) | RETIRED (<reason>))
**Requirements**: REQ-A1, REQ-A2
**Files**:
- `path/to/file.rs` (extend | new | rewrite)

**Scope**:
- <bullet list of concrete edits>
- <reference symbols by `Module::Symbol` form>

**Off-limits**: <files or paths the task must not touch>

**Expected outcome**: <observable post-condition>

**Validation**:
- `cargo test -p crate-name test_name`
- <other commands or assertions>

**Dependencies**: none.

---

## TASK-A2: <short title>

**Status**: TODO
**Requirements**: REQ-A3
**Files**:
- `path/to/other.rs`

**Scope**:
- ...

**Expected outcome**: ...

**Validation**:
- ...

**Dependencies**: TASK-A1.

---

## Parallelizable groups

- **Group α**: TASK-A1 (independent)
- **Group β**: TASK-A2, TASK-B1 (after α; mutually independent)
- **Group γ**: TASK-A3, TASK-B2 (after β)

Tasks in the same group are safe to dispatch in parallel only if they
touch disjoint files, schemas, and generated artifacts. Otherwise serial.
