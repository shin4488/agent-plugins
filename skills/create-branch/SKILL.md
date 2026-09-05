---
name: create-branch
description: PRに向けて作業ブランチを作成する。変更を始めるときや、別の作業を独立したPRに分けるときに使う。
---

# 作業ブランチを作る

レビューで一つの目的を説明できる単位でブランチを分ける。名前・基点は対象リポジトリの規約と依頼に従う。

## 手順

1. `git status --short --branch` と差分を確認する。既存の変更や作業中のブランチを、今回の作業と無関係に移動・破棄しない。
2. remoteと既定ブランチを確認する。`main` に固定せず、`git remote show <remote>` やGitHubのリポジトリ情報を使う。依頼された基点や依存PRがあれば優先する。
3. `git fetch -p <remote>` で基点を更新する。
4. 内容を表す名前でブランチを作る。

```bash
git switch -c <作業ブランチ> <remote>/<基点ブランチ>
```

5. 現在のブランチと基点を確認し、作業を続ける。

## 名前の例

規約がなければ `<type>/<短い英語の内容>` を使う。

| 変更 | 例 |
| --- | --- |
| 機能追加 | `feat/export-csv` |
| 修正 | `fix/date-validation` |
| 開発環境 | `chore/shared-agent-plugin` |

同名ブランチが既にある場合は、その内容を確認する。削除・リセットして使い直さない。コミットは `commit`、PR作成は `create-pr` が担当する。
