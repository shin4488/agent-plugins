---
name: pin-github-actions
description: GitHub Actionsの外部uses参照をフルcommit SHAとバージョンコメントに固定・検証する。Actionの追加、参照の固定、固定済みActionの更新を依頼されたときに使う。
---

# GitHub Actionsの参照を固定する

実行するコードをフルcommit SHAで固定し、対応バージョンをコメントに残す。SHAの解決と検証には [pinact](https://github.com/suzuki-shunsuke/pinact) を使う。

## 手順

1. 変更対象のworkflow・composite action・再利用workflowを確認する。ローカルの `./...` 参照はSHA固定の対象外。
2. 指定されたバージョンの範囲を確認する。メジャー指定からどの版に解決されたかも確認する。
3. pinactが利用可能なら、対象ファイルを指定して固定する。

```bash
pinact run <対象のworkflowまたはaction.yml>
pinact run --check <対象のworkflowまたはaction.yml>
```

4. 差分でSHA・バージョンコメント・対象範囲を確認する。同じActionに異なる版を使う場合は、その理由を確認する。
5. リポジトリのDependabot設定に、更新対象のworkflow・composite actionが含まれているか確認する。設定変更が必要なら依頼範囲に合わせて対応する。

## 制約

- `pinact run --update` はバージョン更新を依頼された場合に使う。固定だけの依頼で全Actionを更新しない。
- ツールがなければリポジトリの導入方法を確認する。SHAを記憶で書いたり、未検証の値で代用しない。
- SHA固定だけで供給元の安全性が保証されるわけではない。更新PR全体の判断は `review-dependabot-prs`、CIの権限設計は `security-review` が担当する。
