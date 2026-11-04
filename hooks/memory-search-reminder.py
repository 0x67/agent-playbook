import json
import sys


def main() -> None:
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    message = (
        "Memory/search protocol reminder: check the native auto memory index "
        "(MEMORY.md) before planning, implementation, review, or investigation. "
        "Search order: lat for architecture, Semble for semantic code search, "
        "fff for exact/file search, rust-analyzer for Rust symbols. If preferred "
        "tool is missing, fails, or lacks needed capability, use regular tools "
        "and state reason."
    )
    print(json.dumps({"continue": True, "systemMessage": message}))


if __name__ == "__main__":
    main()
