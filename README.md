# Wise: Software Architect Mode for Claude Code

本プロジェクトは、Claude Code を単なるコーダーから「**シニア・ソフトウェア・アーキテクト**」へと昇華させるためのカスタムスキル（`wise`）です。
場当たり的な修正を禁止し、TDD（テスト駆動開発）と厳格な設計プロセスを強制します。

## 1. 導入手順 (Setup)

Claude Code セッションの開始時に、必ず以下の手順でスキルを認識させてください。

1. **ファイルの配置**: `SKILL.md`、`PATTERNS.md`、`CHECKLISTS.md` をプロジェクトのルートディレクトリに配置します。
2. **スキルのアクティベート**: 最初に以下の指示を Claude Code に与えます。
   > `SKILL.md` に定義された `/wise` スキルを読み込み、今後の指示に対してアーキテクトとして振る舞ってください。
3. [cite_start]**設定の確認**: `.gitignore` と `settings.local.json` が適切に読み込まれていることを確認してください [cite: 1]。

## 2. 使い方 (Usage)

`/wise` コマンドの後に、**「解決したい課題」または「実装したい機能の要件」**を記述します。

### 基本的なコマンド形式
```bash
/wise [コンテキスト/課題/Issue番号]
```

### 利用例
* **複雑な機能の実装**:
  `/wise 新規ユーザー登録フローを TDD で実装し、PATTERNS.md のバリデーション規則を適用して。`
* **バグ修正と調査**:
  `/wise 決済処理で発生している Race Condition を特定し、TOCTOU 防止策を講じて。`
* **リファクタリング**:
  `/wise 既存の認証モジュールを SOLID 原則に基づいて 3 ファイル以上に分割・再構成して。`

## 3. Wise モードの 8 フェーズ (The Process)

`/wise` が実行されると、エージェントは以下のステップを自動的に開始します。

1. **Phase 1: Understanding & Planning**: タスクの複雑度を評価し、`TodoWrite` で計画を作成します。
2. **Phase 2: Codebase Exploration**: `grep` 等を駆使し、既存のパターンや影響範囲を徹底調査します。
3. **Phase 3: TDD (RED→GREEN→REFACTOR)**: 実装前に必ず失敗するテストを書き、最小限の実装でパスさせます。
4. **Phase 4: Implementation**: マジックナンバーを排除し、プロジェクトの規約に沿ったコードを書きます。
5. **Phase 5: Test Suite Verification**: 変更範囲に応じた適切なテストスイートを実行し、デグレを防ぎます。
6. **Phase 6: Documentation**: 変更に伴うドキュメントや GitHub Issue を更新します。
7. **Phase 7: Pre-Commit Review**: 自己批判的なチェックリストに基づき、エッジケースを再検証します。
8. **Phase 8: PR Readiness**: 最終的な `git diff` を確認し、クリーンな Pull Request を準備します。

## 4. 構成ファイルの詳細

* **`SKILL.md`**: アーキテクトとしての行動規範と 8 つのフェーズの定義。
* **`PATTERNS.md`**: 競合状態の防止や強力なテストアサーションなどの設計パターン集。
* **`CHECKLISTS.md`**: 実装前、TDD、コミット前に確認すべき品質管理項目。
* **`settings.local.json`**: AI に許可する Bash 操作（`git`, `gh`, `grep`等）の権限設定。