---
name: fix-security-alerts
description: GitHubのSecurity and qualityにあるDependabot・Code scanning・Secret scanningの検出結果を調査し、修正可能なものの対応PRを作成・更新する。セキュリティアラートや解析警告への対応を依頼されたときに使う。
---

# GitHubの検出結果から修正PRを作る

アラートと修正を対応付け、コードで直せる問題をPRにする。このスキルは検出結果の収集・切り分け・解消確認を担当する。一般的な安全性レビュー、テスト設計、Git操作の手順は既存スキルを利用する。

## 対象を確かめる

- 指定されたリポジトリ・一覧ファイルから対象を確定し、既定ブランチと閲覧権限を確認する。GitHubリポジトリでない項目や取得できない対象は、理由付きで分けて報告する。
- OverviewのEnabled／Disabledは機能の設定状態であり、アラートの有無ではない。検出結果、解析の失敗・警告、未設定の機能を区別する。Security policyやAdvisoriesの欄があるだけで修正PRを作らない。
- APIまたはUIで未解決の検出結果を収集し、ページネーション・ブランチ・ツールのフィルターによる漏れを確認する。番号／URL、種類、重要度、対象ファイル・依存、ルール／アドバイザリ、関連PRを把握する。APIの権限エラーや未対応、解析未実施を「0件」と扱わない。
- Secret scanningの取得結果には秘密値が含まれ得る。出力前に必要なメタデータだけに絞り、秘密値・該当行・生のレスポンスをチャット、ログ、PR本文へ出さない。機密情報の判断・扱いは [verify-changes](../verify-changes/SKILL.md) に従う。

## 種類ごとに対応を選ぶ

| 検出結果 | このスキルで判断すること |
| --- | --- |
| Dependabot Vulnerabilities | manifest・lockfile・実際の依存経路を照合する。既存の対応PRがあれば [review-dependabot-prs](../review-dependabot-prs/SKILL.md) へつなぎ、重複PRを作らない。新規の更新でも同スキルの更新元・互換性の判断基準を使う。修正版がない、または安全に更新できないものは未解決として残す。 |
| Dependabot Malware | 脆弱性アラートとは分けて、悪意あるパッケージ・版と導入経路を確認する。疑わしい版を調査やテストのために実行せず、削除・信頼できる版への置換を検討する。既に実行された場合の影響調査や認証情報の対応は、依存更新PRだけで解決したと扱わない。 |
| Code scanning | CodeQLに限らず、検出ツール・ルール・対象ブランチ／コミット・解析設定を確認する。指摘箇所から実際の到達経路をたどり、安全性の判断・対策は [security-review](../security-review/SKILL.md) を使う。品質上の指摘は、そのルールが指す動作・仕様との不一致を確認する。 |
| 解析の失敗・警告 | 解析不能、対象言語やファイルの欠落、権限不足など、検出の有効性に影響する原因を調べる。実際の脆弱性と件数を混ぜず、必要なら解析設定の修正PRに分ける。 |
| Secret scanning | 公開識別子・ダミー・実際の認証情報を区別する。コード上の置換と、漏えいした認証情報の無効化・再発行を分けて扱う。ファイルから削除しただけでは漏えいを解消したと扱わず、PRで対応できない作業を明示する。 |

## 修正をPRにする

1. アラートが指す版と現在のコードを照合し、原因と影響が共通するものをまとめる。既に別PRで対応中ならその不足分を調べ、修正不要なら根拠を示す。誤検知の疑いだけでコードを変えない。
2. 修正が必要なら [create-branch](../create-branch/SKILL.md) で作業を分ける。依存更新・コード修正・解析設定の変更は、別々に検証・レビューすべきものなら別PRにする。
3. 検証は [verify-changes](../verify-changes/SKILL.md)、必要な回帰テストの設計は [spec-based-testing](../spec-based-testing/SKILL.md) に従う。スキャナーの指摘が消えることと、既存の正常系・失敗時の動作が保たれることの両方を確かめる。
4. [create-pr](../create-pr/SKILL.md) でコミット・対応PRの作成または更新へ進む。PRには対象アラートの番号／URLと修正の対応、検証結果、PR外に残る作業を記載する。非公開のアラート情報を公開PRへ転記しない。

アラート修正の依頼だけでは、検出機能の有効化・有料機能の契約、鍵の失効、履歴の書き換え、アドバイザリの公開、PRのマージまで実行範囲を広げない。同じ依頼や会話ですでに許可された操作は、その範囲で進める。機能の有効化も依頼されている場合は、対象の公開範囲・契約・実行環境と料金条件を公式情報で確認し、ユーザーの費用制約を守る。

## 結果と解消状態を確認する

- PR作成時点では「修正PR作成済み」と報告する。マージも依頼されている場合は対象headとCIを確認して進め、[post-merge](../post-merge/SKILL.md) の後、対象ブランチ・コミットの解析結果とアラート状態を再取得する。
- 「コード修正済み」「再解析待ち」「GitHub上で解消確認済み」を区別する。解析設定・対象の欠落によって見かけ上アラートが消えた場合は解消としない。
- Secret scanningはコードからの削除だけでは自動クローズされない。クローズ・dismissは解消／誤検知の根拠と操作の依頼範囲に従い、件数を減らす目的では行わない。
- 対象ごとに、対応PR、解消を確認できた検出結果、未解決・未確認のものと理由を報告する。権限不足や外部作業で進めない部分を分け、独立して対応できるものは進める。

## 必要なときに参照するGitHub公式資料

- [Malwareアラートの確認](https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-dependabot-alerts/manage-malware-alerts)
- [Code scanningのブランチ・経路・解析状態の確認](https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-code-scanning-alerts/assess-alerts)
- [Secret scanningの修正とクローズ](https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-secret-scanning-alerts/resolving-alerts)
