#!/usr/bin/env python3
"""Claude Code セッション → Obsidian Markdown 同期フック"""
import json, sys, os, glob, re
from datetime import datetime
from pathlib import Path

# Obsidian vault path — set your vault path to enable sync, leave empty to disable
VAULT_DIR = ""

# ── システムタグ除去 ──────────────────────────────────────────
_SYSTEM_TAGS = re.compile(
    r"<(?:system-reminder|command-message|command-name)>.*?</(?:system-reminder|command-message|command-name)>",
    re.DOTALL,
)

# Skill 注入パターン（"Base directory for this skill:" で始まるブロック）
_SKILL_INJECTION = re.compile(
    r"^Base directory for this skill:.*",
    re.DOTALL,
)


def _strip_system_content(text: str) -> str:
    """システムタグと Skill 注入コンテンツを除去"""
    text = _SYSTEM_TAGS.sub("", text)
    text = text.strip()
    # Skill 注入判定: 残ったテキストが "Base directory for this skill:" で始まる場合
    if _SKILL_INJECTION.match(text):
        return ""
    return text


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
        cleaned = _strip_system_content(content)
        return bool(cleaned.strip())
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text = block.get("text", "")
                    cleaned = _strip_system_content(text)
                    if cleaned.strip():
                        return True
            elif isinstance(block, str):
                cleaned = _strip_system_content(block)
                if cleaned.strip():
                    return True
        return False
    return False


# ── テキスト抽出（user / assistant 共通） ─────────────────────────
def extract_text(content, *, role: str = "assistant") -> str:
    if isinstance(content, str):
        if role == "user":
            return _strip_system_content(content)
        return content.strip()

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                text = block.strip()
                if role == "user":
                    text = _strip_system_content(text)
                if text:
                    parts.append(text)
                continue
            if not isinstance(block, dict):
                continue

            t = block.get("type", "")

            if t == "text":
                text = block.get("text", "").strip()
                if role == "user":
                    text = _strip_system_content(text)
                if text:
                    parts.append(text)

            elif t == "tool_use":
                name = block.get("name", "tool")
                inp = block.get("input", {})
                # ツール呼び出しをコンパクトに表示
                summary = _format_tool_call(name, inp)
                parts.append(summary)

            elif t == "tool_result":
                # ユーザーターンでは tool_result は除外
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


def _format_tool_call(name: str, inp: dict) -> str:
    """ツール呼び出しを読みやすい1行〜数行に整形"""
    if name == "Bash":
        cmd = inp.get("command", "")
        desc = inp.get("description", "")
        label = f"🔧 `$ {cmd}`"
        if desc:
            label += f" — {desc}"
        return label

    if name == "Read":
        fp = inp.get("file_path", "")
        return f"🔧 `Read {fp}`"

    if name == "Write":
        fp = inp.get("file_path", "")
        return f"🔧 `Write {fp}`"

    if name == "Edit":
        fp = inp.get("file_path", "")
        return f"🔧 `Edit {fp}`"

    if name == "Glob":
        pattern = inp.get("pattern", "")
        path = inp.get("path", "")
        s = f"🔧 `Glob {pattern}`"
        if path:
            s += f" in `{path}`"
        return s

    if name == "Grep":
        pattern = inp.get("pattern", "")
        path = inp.get("path", "")
        s = f"🔧 `Grep {pattern}`"
        if path:
            s += f" in `{path}`"
        return s

    if name == "Agent":
        desc = inp.get("description", "")
        return f"🔧 `Agent` — {desc}"

    if name == "Skill":
        skill = inp.get("skill", "")
        args = inp.get("args", "")
        s = f"🔧 `/{skill}`"
        if args:
            s += f" {args}"
        return s

    # フォールバック
    return f"🔧 `{name}`"


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

            entry_type = entry.get("type")
            msg = entry.get("message", {})
            content_raw = msg.get("content", "")

            if entry_type == "user":
                if not _is_real_user_input(content_raw):
                    continue
                content = extract_text(content_raw, role="user")
                if content:
                    lines.append(f"### 👤 User\n{content}")

            elif entry_type == "assistant":
                content = extract_text(content_raw, role="assistant")
                if content:
                    lines.append(f"### 🤖 Claude\n{content}")

    return "\n\n---\n\n".join(lines)


def main():
    if not VAULT_DIR:
        return

    vault = Path(VAULT_DIR)
    if not vault.exists():
        return

    payload = json.loads(sys.stdin.read())
    session_id = payload.get("session_id", "")
    project_path = payload.get("cwd", os.getcwd())
    project_name = Path(project_path).name

    transcript_path = get_transcript_path(session_id)
    if not transcript_path:
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    note_path = vault / f"{date_str} {project_name}.md"

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
