#!/usr/bin/env python3
import json, sys, os, glob
from datetime import datetime
from pathlib import Path

VAULT_DIR = Path("/Documents/ObsidianVault/syc-ob-data")


def get_transcript_path(session_id: str) -> Path | None:
    pattern = str(Path.home() / ".claude/projects/**/*.jsonl")
    for f in glob.glob(pattern, recursive=True):
        if session_id in f:
            return Path(f)
    return None


# ── ユーザーメッセージが「本物のユーザー入力」か判定 ──────────────────
def _is_real_user_input(content) -> bool:
    """
    content が tool_result ブロック *だけ* で構成されている場合は
    ツール実行の返送であり、ユーザーが実際に書いた入力ではない。
    """
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                # text ブロックが 1 つでもあれば本物のユーザー入力とみなす
                if block.get("type") == "text" and block.get("text", "").strip():
                    return True
            elif isinstance(block, str) and block.strip():
                return True
        return False  # tool_result しかなかった
    return False


# ── テキスト抽出（user / assistant 共通） ─────────────────────────
def extract_text(content, *, role: str = "assistant") -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                if block.strip():
                    parts.append(block.strip())
                continue
            if not isinstance(block, dict):
                continue

            t = block.get("type", "")

            if t == "text":
                text = block.get("text", "").strip()
                if text:
                    parts.append(text)

            elif t == "tool_use":
                name = block.get("name", "tool")
                inp = json.dumps(block.get("input", {}), ensure_ascii=False, indent=2)
                parts.append(f"```tool:{name}\n{inp}\n```")

            elif t == "tool_result":
                # ユーザーターンでは tool_result は除外（ノイズ）
                if role == "user":
                    continue
                res = block.get("content", "")
                if isinstance(res, list):
                    res = "\n".join(
                        r.get("text", "") for r in res if isinstance(r, dict)
                    )
                if isinstance(res, str) and res.strip():
                    parts.append(f"```result\n{res.strip()}\n```")

        return "\n\n".join(parts)

    return ""


# ── JSONL → Markdown 変換 ─────────────────────────────────────
def jsonl_to_markdown(jsonl_path: Path) -> str:
    lines: list[str] = []

    with open(jsonl_path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue

            # ── エントリ種別の判定 ──
            # Claude Code JSONL は {"type": "user"|"assistant", "message": {...}}
            # が基本だが、まれに "system" / "summary" 等も混在する
            entry_type = entry.get("type")
            msg = entry.get("message", {})
            content_raw = msg.get("content", "")

            if entry_type == "user":
                # tool_result だけのユーザーターンは読み飛ばす
                if not _is_real_user_input(content_raw):
                    continue
                content = extract_text(content_raw, role="user")
                if content:
                    lines.append(f"### 👤 User\n{content}")

            elif entry_type == "assistant":
                content = extract_text(content_raw, role="assistant")
                if content:
                    lines.append(f"### 🤖 Claude\n{content}")

            # system / summary / result 等はスキップ

    return "\n\n---\n\n".join(lines)


def main():
    payload = json.loads(sys.stdin.read())
    session_id = payload.get("session_id", "")
    project_path = payload.get("cwd", os.getcwd())
    project_name = Path(project_path).name

    transcript_path = get_transcript_path(session_id)
    if not transcript_path:
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    note_path = VAULT_DIR / f"{date_str} {project_name}.md"

    body = jsonl_to_markdown(transcript_path)

    header = f"""---
project: {project_name}
session: {session_id[:8]}
date: {date_str}
updated: {datetime.now().strftime("%H:%M:%S")}
---

# {project_name} - {date_str}

"""
    note_path.write_text(header + body, encoding="utf-8")


if __name__ == "__main__":
    main()