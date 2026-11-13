#!/usr/bin/env python3
"""PreToolUse (Bash and database MCP tools) hook: ask before destructive database work and remote writes.

1. Destructive statements on any host: DROP of a database, schema, table, view, keyspace, user, or role;
   TRUNCATE; ALTER TABLE ... DROP; DELETE or UPDATE with no WHERE; MongoDB drops and match-all deletes;
   Redis FLUSHALL and FLUSHDB; dropdb, mysqladmin drop, pg_restore --clean, and bq rm.
2. Writes (INSERT, UPDATE, CREATE, GRANT, Mongo inserts and updates, and others) to a database that is not
   local. The host comes from a connection URI, -h/--host, host=, sqlcmd -S, or PGHOST. A $VAR argument is
   resolved from the environment, then from .env, .env.local, and .env.development at the repo root; one that
   does not resolve counts as not local.
3. Migration commands that drop, reset, roll back, or apply schema to a shared database.
4. Database MCP tools: a tool name that drops, deletes, resets, or applies a migration, or SQL in the
   arguments that matches 1 or 2. MCP database servers count as remote unless the name says sqlite or duckdb.

Shell SQL is scanned only when the command runs a database client, together with any .sql or .cql file the
command names. Reasons name the rule and the host, never the command, because connection strings hold
passwords. Not covered: ORM or app code, dynamic SQL, stored procedures, and env files outside the repo root.
AGENT_PLAYBOOK_DB_GUARD=off turns the hook off.
"""
import json
import os
import re
import shlex
import subprocess
import sys

MAX_FILE = 2 * 1024 * 1024
CLIENTS = {
    "psql", "pgcli", "mysql", "mariadb", "mycli", "sqlite3", "litecli", "sqlcmd", "sqlplus", "clickhouse",
    "clickhouse-client", "cqlsh", "snowsql", "duckdb", "mongosh", "mongo", "redis-cli", "valkey-cli", "bq",
    "cockroach", "usql", "dropdb", "mysqladmin", "pg_restore",
}
FILE_CLIENTS = {"sqlite3", "litecli", "duckdb"}
LOCAL_HOSTS = {"localhost", "::1", "0.0.0.0", "host.docker.internal"}

DROP = re.compile(r"\bdrop\s+(database|schema|table|materialized\s+view|view|keyspace|user|role|owned)\b", re.I)
OTHER_DESTRUCTIVE = [
    (re.compile(r"\btruncate\s+(table\s+)?[\w.\"`\[]", re.I), "TRUNCATE"),
    (re.compile(r"\balter\s+table\b[^;]*?\bdrop\b", re.I), "ALTER TABLE ... DROP"),
    (re.compile(r"\.dropDatabase\s*\(|\.drop\s*\(\s*\)"), "MongoDB drop"),
    (re.compile(r"\.(deleteMany|remove|updateMany)\s*\(\s*\{\s*\}"), "MongoDB match-all delete or update"),
    (re.compile(r"\bflush(all|db)\b", re.I), "FLUSHALL or FLUSHDB"),
]
DELETE_ALL = re.compile(r"\bdelete\s+from\s+[\w.\"`\[\]]+([^;]*)", re.I)
UPDATE_ALL = re.compile(r"\bupdate\s+[\w.\"`\[\]]+\s+set\b([^;]*)", re.I)
WHERE = re.compile(r"\bwhere\b", re.I)
WRITE = re.compile(
    r"\b(insert\s+into|update\s+[\w.\"`\[\]]+\s+set|delete\s+from|merge\s+into|upsert|replace\s+into"
    r"|create\s+(or\s+replace\s+)?(table|database|schema|index|unique\s+index|view|materialized\s+view|function"
    r"|procedure|trigger|user|role|extension|type|sequence|keyspace)|alter\s+\w+|drop\s+\w+|truncate"
    r"|grant\s|revoke\s|copy\s+[\w.\"]+\s*(\([^)]*\)\s*)?from|call\s+[\w.]+\s*\()", re.I)
MONGO_WRITE = re.compile(r"\.(insert(One|Many)?|update(One|Many)?|replaceOne|bulkWrite|delete(One|Many)"
                         r"|findOneAnd(Update|Replace|Delete)|createCollection|createIndex|renameCollection)\s*\(")

URI = re.compile(r"\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|rediss?|clickhouse|cockroachdb|sqlserver"
                 r"|jdbc:[a-z]+(?::[a-z]+)?)://(?:[^@/\s'\"]*@)?(\[[^\]]+\]|[^/:?,\s'\"]+)", re.I)
HOST_FLAG = re.compile(r"(?:^|\s)(?:-h\s*|--host[=\s]\s*|-S\s+)['\"]?([^\s'\";|&]+)")
CONNINFO_HOST = re.compile(r"\bhost\s*=\s*['\"]?([^\s'\";|&]+)")
VAR = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")
URL_VAR = re.compile(r"(URL|URI|DSN|HOST|CONN|CONNECTION|CONNECTION_STRING|CONN_STR)$", re.I)

MIGRATIONS = [
    (r"\bprisma\s+migrate\s+(reset|deploy)\b", "prisma migrate reset or deploy"),
    (r"\bprisma\s+db\s+push\b[^;&|\n]*--(accept-data-loss|force-reset)\b", "prisma db push with data loss"),
    (r"\bdrizzle-kit\s+(push|drop)\b", "drizzle-kit push or drop"),
    (r"\b(rails|rake)\s+db:(drop|reset|purge|schema:load|structure:load|migrate:reset|rollback)\b", "rails db drop, reset, load, or rollback"),
    (r"\bartisan\s+(migrate:(fresh|reset|refresh|rollback)|db:wipe)\b", "artisan migrate fresh, reset, refresh, rollback, or db:wipe"),
    (r"\bmix\s+ecto\.(drop|reset|rollback)\b", "mix ecto drop, reset, or rollback"),
    (r"\b(manage\.py|django-admin)\s+(flush|reset_db)\b|\bmanage\.py\s+migrate\s+\w+\s+zero\b", "Django flush, reset_db, or migrate to zero"),
    (r"\balembic\b[^;&|\n]*\bdowngrade\b", "alembic downgrade"),
    (r"\bflyway\b[^;&|\n]*\b(clean|undo)\b", "flyway clean or undo"),
    (r"\bliquibase\b[^;&|\n]*\b(drop-all|dropAll|rollback[\w-]*)\b", "liquibase drop-all or rollback"),
    (r"\batlas\s+schema\s+apply\b", "atlas schema apply"),
    (r"\bsupabase\s+db\s+(reset|push)\b", "supabase db reset or push"),
    (r"\bsqlx\s+database\s+(drop|reset)\b", "sqlx database drop or reset"),
    (r"\bdiesel\s+database\s+reset\b", "diesel database reset"),
    (r"\bdbmate\b[^;&|\n]*\b(drop|rollback|down)\b", "dbmate drop or rollback"),
    (r"\bgoose\b[^;&|\n]*\b(down|down-to|reset)\b", "goose down or reset"),
    (r"\bmigrate\b[^;&|\n]*\s-database\b[^;&|\n]*\b(drop|down)\b", "golang-migrate drop or down"),
    (r"\bknex\b[^;&|\n]*\bmigrate:(rollback|down)\b", "knex migrate rollback"),
    (r"\bsequelize\b[^;&|\n]*\bdb:(drop|migrate:undo(:all)?)\b", "sequelize db:drop or migrate:undo"),
    (r"\b(typeorm|mikro-orm)\b[^;&|\n]*\bschema:(drop|fresh)\b", "schema:drop"),
    (r"\bdoctrine:(schema|database):drop\b", "doctrine drop"),
]
MIGRATIONS = [(re.compile(p), label) for p, label in MIGRATIONS]
DESTRUCTIVE_TOOL = re.compile(r"(^|[_-])(drop|delete|reset|truncate|flush|purge|wipe)([_-]|$)", re.I)
APPLY_TOOL = re.compile(r"(^|[_-])(apply|migrate|migration|merge)([_-]|$)", re.I)


def emit(reasons):
    if reasons:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": " | ".join(reasons),
        }}))


def segments(cmd):
    """Split a shell line into simple commands on ; && || | and newlines."""
    return [s.strip() for s in re.split(r"&&|\|\||[;|\n]", cmd) if s.strip()]


def words(seg):
    try:
        return shlex.split(seg)
    except ValueError:
        return seg.split()


# ---------------------------------------------------------------- statements

def strip_comments(text, line_comments):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"--[^\n]*", " ", text) if line_comments else text


def destructive_hits(text):
    hits = [" ".join(m.group(0).split()).upper() for m in DROP.finditer(text)]
    hits += [label for pat, label in OTHER_DESTRUCTIVE if pat.search(text)]
    if any(not WHERE.search(m.group(1)) for m in DELETE_ALL.finditer(text)):
        hits.append("DELETE without WHERE")
    if any(not WHERE.search(m.group(1)) for m in UPDATE_ALL.finditer(text)):
        hits.append("UPDATE without WHERE")
    return list(dict.fromkeys(hits))


def write_hits(text):
    hits = [m.group(0).split()[0].upper() for m in WRITE.finditer(text)]
    hits += [m.group(1) for m in MONGO_WRITE.finditer(text)]
    return list(dict.fromkeys(hits))


def tool_hits(segs):
    hits = []
    for seg in segs:
        w = [os.path.basename(x) for x in words(seg)]
        if "dropdb" in w:
            hits.append("dropdb")
        if "mysqladmin" in w and "drop" in w[w.index("mysqladmin"):]:
            hits.append("mysqladmin drop")
        if "pg_restore" in w and any(x == "--clean" or re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", x) for x in w):
            hits.append("pg_restore --clean")
        if "bq" in w and w[w.index("bq") + 1:w.index("bq") + 2] == ["rm"]:
            hits.append("bq rm")
    return hits


# ---------------------------------------------------------------- targets

def repo_root(cwd):
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True,
                           timeout=5, stdin=subprocess.DEVNULL)
        return r.stdout.strip() if r.returncode == 0 else cwd
    except (OSError, subprocess.TimeoutExpired):
        return cwd


def resolve_var(name, cwd):
    if name in os.environ:
        return os.environ[name]
    root = repo_root(cwd)
    for env_file in (".env", ".env.local", ".env.development"):
        try:
            with open(os.path.join(root, env_file), encoding="utf-8") as fh:
                for line in fh:
                    m = re.match(rf"^\s*(?:export\s+)?{re.escape(name)}\s*=\s*(.*?)\s*$", line)
                    if m:
                        return m.group(1).strip("'\"")
        except OSError:
            continue
    return None


def is_local(host):
    h = host.strip("[]").lower()
    return (h in LOCAL_HOSTS or h.endswith(".localhost") or h.startswith(("127.", "/", ".", "~"))
            or ("." not in h and ":" not in h))


def host_target(raw):
    """(host, local) for a host token, with any scheme prefix, port, or SQL Server instance removed."""
    h = raw.strip("'\"")
    h = re.sub(r"^(tcp|np|lpc):", "", h, flags=re.I)
    h = re.split(r"[,\\]", h)[0]
    if not h.startswith("[") and h.count(":") == 1:
        h = h.split(":")[0]
    return h, is_local(h)


def var_target(name, cwd):
    """(label, local) for a $VAR that names a database, or None when the variable is not about a host."""
    value = resolve_var(name, cwd)
    if value is None:
        return (f"${name} (not set)", False) if URL_VAR.search(name) else None
    if m := URI.search(value):
        return host_target(m.group(1))
    if m := CONNINFO_HOST.search(value):
        return host_target(m.group(1))
    if name.upper().endswith("HOST"):
        return host_target(value)
    return None


def targets(cmd, client_segs, cwd):
    """(host, local) for each database host the command names. Empty means the client's local default."""
    out = [host_target(m.group(1)) for m in URI.finditer(cmd)]
    for seg, names in client_segs:
        if names and names <= FILE_CLIENTS:
            continue
        tokens = [m.group(1) for m in HOST_FLAG.finditer(seg)] + [m.group(1) for m in CONNINFO_HOST.finditer(seg)]
        for tok in tokens:
            v = VAR.fullmatch(tok)
            out.append(var_target(v.group(1), cwd) if v else host_target(tok))
        for m in VAR.finditer(seg):
            out.append(var_target(m.group(1), cwd))
        if re.search(r"\bwrangler\s+d1\s+execute\b", seg) and "--remote" in seg:
            out.append(("Cloudflare D1 (--remote)", False))
        if re.search(r"\bturso\s+db\s+shell\b", seg):
            out.append(("Turso", False))
        if re.search(r"\bprisma\s+db\s+execute\b", seg) and not URI.search(seg):
            out.append(("the Prisma datasource (not resolved)", False))
        if "psql" in names and not out and os.environ.get("PGHOST"):
            out.append(host_target(os.environ["PGHOST"]))
    return list(dict.fromkeys(t for t in out if t))


# ---------------------------------------------------------------- tools

def client_segments(segs):
    found = []
    for seg in segs:
        names = {os.path.basename(w) for w in words(seg)} & CLIENTS
        if names or re.search(r"\b(prisma\s+db\s+execute|wrangler\s+d1\s+execute|turso\s+db\s+shell)\b", seg):
            found.append((seg, names))
    return found


def sql_files(segs, cwd):
    texts = []
    for seg in segs:
        for w in words(seg):
            path = w.split("=", 1)[-1]
            if not re.search(r"\.(sql|cql)$", path, re.I):
                continue
            try:
                with open(os.path.join(cwd, os.path.expanduser(path)), encoding="utf-8", errors="replace") as fh:
                    texts.append(strip_comments(fh.read(MAX_FILE), line_comments=True))
            except OSError:
                continue
    return texts


def shell_reasons(cmd, cwd):
    reasons = []
    hits = [label for pat, label in MIGRATIONS if pat.search(cmd)]
    if hits:
        reasons.append(f"Database migration that drops, resets, rolls back, or applies schema ({', '.join(hits)}). "
                       "Confirm which database it targets first.")

    segs = segments(cmd)
    client_segs = client_segments(segs)
    if not client_segs:
        return reasons

    text = "\n".join([strip_comments(cmd, line_comments=False)] + sql_files(segs, cwd))
    via = ", ".join(f"`{n}`" for n in sorted({n for _, names in client_segs for n in names})) or "a database tool"
    found = targets(cmd, client_segs, cwd)
    remote = [host for host, local in found if not local]
    where = f" on {', '.join(f'`{h}`' for h, _ in found)}" if found else ""

    destructive = destructive_hits(text) + tool_hits(segs)
    if destructive:
        reasons.append(f"Destructive database command ({', '.join(destructive)}) via {via}{where}. "
                       "Confirm the database and that a backup exists.")
    elif remote and (writes := write_hits(text)):
        reasons.append(f"Database write ({', '.join(writes)}) via {via} to a host that is not local: "
                       f"{', '.join(f'`{h}`' for h in remote)}. Writes to shared databases need the user's go-ahead.")
    return reasons


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)


def mcp_reasons(name, tool_input):
    parts = name.split("__", 2)
    if len(parts) < 3:
        return []
    server, tool = parts[1], parts[2]

    reasons = []
    if DESTRUCTIVE_TOOL.search(tool):
        reasons.append(f"Database MCP tool `{tool}` on `{server}` deletes or resets data.")
    elif APPLY_TOOL.search(tool):
        reasons.append(f"Database MCP tool `{tool}` on `{server}` applies a schema change.")

    text = strip_comments("\n".join(strings(tool_input)), line_comments=True)
    if destructive := destructive_hits(text):
        reasons.append(f"Destructive statement ({', '.join(destructive)}) in `{tool}` on `{server}`. "
                       "Confirm the database and that a backup exists.")
    elif not reasons and not re.search(r"sqlite|duckdb", server, re.I) and (writes := write_hits(text)):
        reasons.append(f"Database write ({', '.join(writes)}) through `{tool}` on `{server}`, which counts as a "
                       "remote database. Writes to shared databases need the user's go-ahead.")
    return reasons


def main():
    if os.environ.get("AGENT_PLAYBOOK_DB_GUARD", "").lower() in ("off", "0", "false"):
        return
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    if tool == "Bash":
        emit(shell_reasons(tool_input.get("command", ""), data.get("cwd") or os.getcwd()))
    elif tool.startswith("mcp__"):
        emit(mcp_reasons(tool, tool_input))


if __name__ == "__main__":
    main()
