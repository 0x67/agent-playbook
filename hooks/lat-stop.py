#!/usr/bin/env python3
"""SessionStart, Stop, and SessionEnd hook: run `lat hook claude Stop` only when the session changed files.

lat's own Stop hook blocks the end of a session whenever `lat check` fails or code
changed without a lat.md update, even when this session only read code. At
SessionStart this records a fingerprint of the working tree (diff against HEAD
plus untracked files). At Stop it hands over to lat's hook only if the
fingerprint changed. No lat.md/, no lat CLI: nothing happens. Not a git repo or
no fingerprint (session started before this hook): lat's hook runs as before.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

raw = sys.stdin.read()
try:
    payload = json.loads(raw)
except Exception:
    payload = {}
cwd = os.getcwd()
if not os.path.isdir(os.path.join(cwd, "lat.md")) or not shutil.which("lat"):
    sys.exit(0)

session = "".join(c for c in str(payload.get("session_id", "")) if c.isalnum() or c == "-")
marker = os.path.join(tempfile.gettempdir(), f"ai-setup-lat-stop-{session}") if session else None


def fingerprint():
    """Hash of tracked changes against HEAD and the untracked file list with sizes and mtimes."""
    h = hashlib.sha256()
    try:
        diff = subprocess.run(["git", "diff", "HEAD", "--no-ext-diff", "--binary"], cwd=cwd,
                              capture_output=True, timeout=20)
        if diff.returncode != 0:
            return None
        h.update(diff.stdout)
        untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=cwd,
                                   capture_output=True, timeout=20)
        for name in sorted(untracked.stdout.split(b"\0")):
            if name:
                st = os.stat(os.path.join(cwd, name.decode(errors="surrogateescape")))
                h.update(name + f":{st.st_size}:{st.st_mtime_ns}".encode())
    except Exception:
        return None
    return h.hexdigest()


event = payload.get("hook_event_name", "")
if event == "SessionEnd":
    if marker and os.path.exists(marker):
        os.remove(marker)
    sys.exit(0)

if event == "SessionStart":
    fp = fingerprint()
    if marker and fp:
        with open(marker, "w") as fh:
            fh.write(fp)
    sys.exit(0)

if event == "Stop":
    if marker and os.path.exists(marker):
        with open(marker) as fh:
            before = fh.read().strip()
        if fingerprint() == before:
            sys.exit(0)  # this session changed nothing; skip lat's check
    result = subprocess.run(["lat", "hook", "claude", "Stop"], input=raw, text=True, capture_output=True, cwd=cwd)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    sys.exit(result.returncode)
