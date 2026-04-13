#!/usr/bin/env python3
"""sync_to_obsidian.py のユニットテスト

対象: _strip_system_content, _is_real_user_input, _format_tool_call
"""
import sys
import unittest
from pathlib import Path

# テスト対象モジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))
from sync_to_obsidian import _strip_system_content, _is_real_user_input, _format_tool_call


# ══════════════════════════════════════════════════════════════
# _strip_system_content
# ══════════════════════════════════════════════════════════════
class TestStripSystemContent(unittest.TestCase):
    """正規表現ベースのタグ除去。壊れやすいため境界条件を重点的にテスト"""

    # ── 基本除去 ──

    def test_strip_system_reminder(self):
        text = "<system-reminder>some noise</system-reminder>"
        self.assertEqual(_strip_system_content(text), "")

    def test_strip_command_message(self):
        text = "<command-message>terse-mode</command-message>"
        self.assertEqual(_strip_system_content(text), "")

    def test_strip_command_name(self):
        text = "<command-name>/terse-mode</command-name>"
        self.assertEqual(_strip_system_content(text), "")

    # ── 複数タグ ──

    def test_strip_multiple_tags(self):
        text = (
            "<command-message>terse-mode</command-message>\n"
            "<command-name>/terse-mode</command-name>"
        )
        self.assertEqual(_strip_system_content(text), "")

    def test_strip_mixed_tag_types(self):
        text = (
            "<system-reminder>noise</system-reminder>"
            "<command-message>cmd</command-message>"
            "<command-name>name</command-name>"
        )
        self.assertEqual(_strip_system_content(text), "")

    # ── タグ内改行（re.DOTALL） ──

    def test_multiline_system_reminder(self):
        text = "<system-reminder>\nline1\nline2\nline3\n</system-reminder>"
        self.assertEqual(_strip_system_content(text), "")

    def test_multiline_with_markdown(self):
        text = (
            "<system-reminder>\n"
            "# Heading\n"
            "- bullet\n"
            "```code```\n"
            "</system-reminder>"
        )
        self.assertEqual(_strip_system_content(text), "")

    # ── タグ + 実テキスト混在 ──

    def test_tag_with_real_text_after(self):
        text = "<system-reminder>noise</system-reminder>\n探索して"
        self.assertEqual(_strip_system_content(text), "探索して")

    def test_tag_with_real_text_before(self):
        text = "質問です\n<system-reminder>noise</system-reminder>"
        self.assertEqual(_strip_system_content(text), "質問です")

    def test_real_text_between_tags(self):
        text = (
            "<command-message>cmd</command-message>\n"
            "これが本文\n"
            "<command-name>name</command-name>"
        )
        self.assertEqual(_strip_system_content(text), "これが本文")

    # ── Skill 注入 ──

    def test_skill_injection_removed(self):
        text = "Base directory for this skill: /path/to/skill\n\n# Skill Name\nLots of content..."
        self.assertEqual(_strip_system_content(text), "")

    def test_skill_injection_after_tag_strip(self):
        """タグ除去後に残ったテキストがSkill注入パターンの場合"""
        text = (
            "<command-message>wise</command-message>\n"
            "<command-name>/wise</command-name>\n"
            "Base directory for this skill: /path\n\n# Wise Mode\ncontent"
        )
        self.assertEqual(_strip_system_content(text), "")

    def test_non_skill_text_starting_with_base(self):
        """'Base' で始まるが Skill 注入ではないテキスト"""
        text = "Based on the analysis, we should..."
        self.assertEqual(_strip_system_content(text), "Based on the analysis, we should...")

    # ── エッジケース ──

    def test_empty_string(self):
        self.assertEqual(_strip_system_content(""), "")

    def test_whitespace_only(self):
        self.assertEqual(_strip_system_content("   \n\t  "), "")

    def test_plain_text_unchanged(self):
        text = "これは普通のユーザー入力です"
        self.assertEqual(_strip_system_content(text), text)

    def test_mismatched_tags_still_stripped(self):
        """開始と終了が異なるタグ名でも除去される（正規表現が独立マッチ）。
        システムタグ同士のクロスマッチは実害なし"""
        text = "<system-reminder>content</command-name>"
        self.assertEqual(_strip_system_content(text), "")

    def test_angle_brackets_in_normal_text(self):
        """HTML風のテキストが誤って除去されない"""
        text = "Use <div> for layout"
        self.assertEqual(_strip_system_content(text), "Use <div> for layout")

    def test_nested_tags_not_greedy(self):
        """複数タグが貪欲マッチで1つに結合されない"""
        text = (
            "<system-reminder>A</system-reminder>"
            "KEEP THIS"
            "<system-reminder>B</system-reminder>"
        )
        self.assertEqual(_strip_system_content(text), "KEEP THIS")


# ══════════════════════════════════════════════════════════════
# _is_real_user_input
# ══════════════════════════════════════════════════════════════
class TestIsRealUserInput(unittest.TestCase):
    """フィルタ漏れ = Obsidian にゴミが出力される。False negative/positive 両方テスト"""

    # ── str 入力 ──

    def test_plain_text_is_real(self):
        self.assertTrue(_is_real_user_input("探索して"))

    def test_empty_string_not_real(self):
        self.assertFalse(_is_real_user_input(""))

    def test_whitespace_only_not_real(self):
        self.assertFalse(_is_real_user_input("   \n  "))

    def test_system_tag_only_not_real(self):
        self.assertFalse(
            _is_real_user_input("<system-reminder>noise</system-reminder>")
        )

    def test_command_tags_only_not_real(self):
        text = (
            "<command-message>terse-mode</command-message>\n"
            "<command-name>/terse-mode</command-name>"
        )
        self.assertFalse(_is_real_user_input(text))

    def test_tag_plus_real_text_is_real(self):
        text = "<system-reminder>noise</system-reminder>\n質問です"
        self.assertTrue(_is_real_user_input(text))

    def test_skill_injection_not_real(self):
        text = "Base directory for this skill: /path\n\n# Skill\ncontent"
        self.assertFalse(_is_real_user_input(text))

    # ── list 入力: text ブロック ──

    def test_list_with_text_block_is_real(self):
        content = [{"type": "text", "text": "探索して"}]
        self.assertTrue(_is_real_user_input(content))

    def test_list_with_empty_text_block_not_real(self):
        content = [{"type": "text", "text": ""}]
        self.assertFalse(_is_real_user_input(content))

    def test_list_with_tag_only_text_not_real(self):
        content = [{"type": "text", "text": "<system-reminder>x</system-reminder>"}]
        self.assertFalse(_is_real_user_input(content))

    # ── list 入力: tool_result ブロック ──

    def test_list_tool_result_only_not_real(self):
        content = [
            {
                "type": "tool_result",
                "tool_use_id": "abc",
                "content": "result data",
            }
        ]
        self.assertFalse(_is_real_user_input(content))

    def test_list_tool_result_plus_tag_text_not_real(self):
        content = [
            {"type": "tool_result", "tool_use_id": "abc", "content": "data"},
            {"type": "text", "text": "<system-reminder>x</system-reminder>"},
        ]
        self.assertFalse(_is_real_user_input(content))

    def test_list_tool_result_plus_real_text_is_real(self):
        content = [
            {"type": "tool_result", "tool_use_id": "abc", "content": "data"},
            {"type": "text", "text": "実際のユーザー入力"},
        ]
        self.assertTrue(_is_real_user_input(content))

    # ── list 入力: str 要素 ──

    def test_list_with_plain_string_is_real(self):
        content = ["普通のテキスト"]
        self.assertTrue(_is_real_user_input(content))

    def test_list_with_tag_string_not_real(self):
        content = ["<system-reminder>noise</system-reminder>"]
        self.assertFalse(_is_real_user_input(content))

    # ── エッジケース ──

    def test_empty_list_not_real(self):
        self.assertFalse(_is_real_user_input([]))

    def test_none_not_real(self):
        self.assertFalse(_is_real_user_input(None))

    def test_int_not_real(self):
        self.assertFalse(_is_real_user_input(42))

    def test_dict_not_real(self):
        """list でも str でもない dict → False"""
        self.assertFalse(_is_real_user_input({"type": "text", "text": "hello"}))

    def test_list_with_unknown_block_type_not_real(self):
        content = [{"type": "image", "source": "data:..."}]
        self.assertFalse(_is_real_user_input(content))


# ══════════════════════════════════════════════════════════════
# _format_tool_call
# ══════════════════════════════════════════════════════════════
class TestFormatToolCall(unittest.TestCase):
    """ツール種別ごとの分岐。出力形式の正確性とクラッシュ耐性"""

    # ── Bash ──

    def test_bash_basic(self):
        result = _format_tool_call("Bash", {"command": "ls -la"})
        self.assertIn("$ ls -la", result)
        self.assertIn("🔧", result)

    def test_bash_with_description(self):
        result = _format_tool_call("Bash", {"command": "ls", "description": "List files"})
        self.assertIn("$ ls", result)
        self.assertIn("List files", result)

    def test_bash_empty_command(self):
        result = _format_tool_call("Bash", {"command": ""})
        self.assertIn("🔧", result)
        # クラッシュしない

    def test_bash_no_command_key(self):
        result = _format_tool_call("Bash", {})
        self.assertIn("🔧", result)

    # ── Read / Write / Edit ──

    def test_read(self):
        result = _format_tool_call("Read", {"file_path": "/tmp/test.py"})
        self.assertIn("Read", result)
        self.assertIn("/tmp/test.py", result)

    def test_write(self):
        result = _format_tool_call("Write", {"file_path": "/tmp/out.py"})
        self.assertIn("Write", result)
        self.assertIn("/tmp/out.py", result)

    def test_edit(self):
        result = _format_tool_call("Edit", {"file_path": "/tmp/edit.py"})
        self.assertIn("Edit", result)
        self.assertIn("/tmp/edit.py", result)

    def test_read_empty_path(self):
        result = _format_tool_call("Read", {"file_path": ""})
        self.assertIn("Read", result)

    def test_read_no_path_key(self):
        result = _format_tool_call("Read", {})
        self.assertIn("Read", result)

    # ── Glob ──

    def test_glob_basic(self):
        result = _format_tool_call("Glob", {"pattern": "**/*.py"})
        self.assertIn("Glob", result)
        self.assertIn("**/*.py", result)

    def test_glob_with_path(self):
        result = _format_tool_call("Glob", {"pattern": "*.md", "path": "/src"})
        self.assertIn("*.md", result)
        self.assertIn("/src", result)

    def test_glob_without_path(self):
        result = _format_tool_call("Glob", {"pattern": "*.md"})
        self.assertIn("*.md", result)
        self.assertNotIn(" in ", result)

    # ── Grep ──

    def test_grep_basic(self):
        result = _format_tool_call("Grep", {"pattern": "TODO"})
        self.assertIn("Grep", result)
        self.assertIn("TODO", result)

    def test_grep_with_path(self):
        result = _format_tool_call("Grep", {"pattern": "def foo", "path": "/src"})
        self.assertIn("def foo", result)
        self.assertIn("/src", result)

    def test_grep_without_path(self):
        result = _format_tool_call("Grep", {"pattern": "error"})
        self.assertNotIn(" in ", result)

    # ── Agent ──

    def test_agent(self):
        result = _format_tool_call("Agent", {"description": "Search codebase"})
        self.assertIn("Agent", result)
        self.assertIn("Search codebase", result)

    def test_agent_empty_description(self):
        result = _format_tool_call("Agent", {"description": ""})
        self.assertIn("Agent", result)

    # ── Skill ──

    def test_skill_basic(self):
        result = _format_tool_call("Skill", {"skill": "commit"})
        self.assertIn("/commit", result)

    def test_skill_with_args(self):
        result = _format_tool_call("Skill", {"skill": "terse-mode", "args": "ultra"})
        self.assertIn("/terse-mode", result)
        self.assertIn("ultra", result)

    def test_skill_without_args(self):
        result = _format_tool_call("Skill", {"skill": "commit", "args": ""})
        # args が空なので余計なスペースだけが付く等の問題がないか
        self.assertIn("/commit", result)

    # ── フォールバック ──

    def test_unknown_tool(self):
        result = _format_tool_call("CustomTool", {"key": "value"})
        self.assertIn("CustomTool", result)
        self.assertIn("🔧", result)

    def test_unknown_tool_empty_input(self):
        result = _format_tool_call("Something", {})
        self.assertIn("Something", result)

    # ── 全ツールで str が返る ──

    def test_all_return_str(self):
        tools = [
            ("Bash", {"command": "echo hi"}),
            ("Read", {"file_path": "/f"}),
            ("Write", {"file_path": "/f"}),
            ("Edit", {"file_path": "/f"}),
            ("Glob", {"pattern": "*"}),
            ("Grep", {"pattern": "x"}),
            ("Agent", {"description": "d"}),
            ("Skill", {"skill": "s"}),
            ("Unknown", {}),
        ]
        for name, inp in tools:
            with self.subTest(tool=name):
                result = _format_tool_call(name, inp)
                self.assertIsInstance(result, str)
                self.assertTrue(len(result) > 0)


# ══════════════════════════════════════════════════════════════
# main — VAULT_DIR 早期リターン
# ══════════════════════════════════════════════════════════════
class TestMainEarlyReturn(unittest.TestCase):
    """VAULT_DIR が空 or 存在しないパスなら何もせず終了"""

    def test_empty_vault_dir_returns_immediately(self):
        """VAULT_DIR 空 → stdin を読まず即リターン"""
        import sync_to_obsidian as mod
        original = mod.VAULT_DIR
        try:
            mod.VAULT_DIR = ""
            # stdin が空でもエラーにならない = stdin.read() に到達していない
            mod.main()
        finally:
            mod.VAULT_DIR = original

    def test_nonexistent_vault_dir_returns_immediately(self):
        """VAULT_DIR が存在しないパス → stdin を読まず即リターン"""
        import sync_to_obsidian as mod
        original = mod.VAULT_DIR
        try:
            mod.VAULT_DIR = "/nonexistent/path/that/does/not/exist"
            mod.main()
        finally:
            mod.VAULT_DIR = original


if __name__ == "__main__":
    unittest.main()
