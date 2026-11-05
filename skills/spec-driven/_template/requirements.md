# <Spec Name>: Requirements

| Field      | Value                       |
| ---------- | --------------------------- |
| Status     | Draft                       |
| Supersedes | <prior spec slug or `none`> |

Workstreams (if multi-stream):

- **A**: <workstream A short title>
- **B**: <workstream B short title>
- ...

---

## A: <workstream A title>

### REQ-A1: <short title>

**Where** <trigger or condition>,
**the system shall** <observable behavior>,
**so that** <user-visible outcome>.

Files:
- `path/to/file.rs::SymbolOrFn`

Severity: **High**

### REQ-A2: <short title>

**Where** ...,
**the system shall** ...,
**so that** ....

Files:
- `path/to/file.rs::SymbolOrFn`

Severity: **Medium**

---

## B: <workstream B title>

### REQ-B1: <short title>

**Where** ...,
**the system shall** ...,
**so that** ....

Files:
- `path/to/file.rs::SymbolOrFn`

Severity: **High**

---

## Non-goals

- <explicitly out-of-scope item>
- <another out-of-scope item>

## Notes

- All REQ ids stable. Append-only. Never renumber.
- Severity values: `Critical | High | Medium | Low`.
- Every REQ must trace forward to at least one TASK-* and one AC-*.
