# Dependabot修正と未解消項目（2026-09-08）

## 結果と件数の意味

管理対象15リポジトリで make dependabot を実行した結果、5リポジトリにVULNERABILITYが875件あり、MALWAREは全リポジトリで0件でした。
以下は取得した各アラートの脆弱バージョン範囲と、修正ブランチのロックファイルの全バージョンを突き合わせた結果です。**GitHub側で閉鎖済みという意味ではありません。マージ後の再解析と再集計が必要です。**

| リポジトリ | 検出時 | 対象範囲から外れた件数 | 残存 |
| --- | ---: | ---: | ---: |
| algorithm-visualizer | 27 | 27 | 0 |
| BaseballGame | 90 | 72 | 18 |
| dev-log | 209 | 182 | 27 |
| learning-transformer | 4 | 4 | 0 |
| no1-company-share | 545 | 478 | 67 |

Functionsの重複したyarn.lockは、デプロイで使用するpackage-lock.jsonへ統一しました。旧Yarnアラートも新npmロックの実際のバージョンで再評価しており、ファイル削除だけを解消と数えていません。監査コマンドは依存経路単位の重複や新規アラートも含むため、この表とは件数が一致しません。

## 実施した検証と、仕様・表示を保証できない範囲

| リポジトリ | 検証結果 | 未確認・条件 |
| --- | --- | --- |
| algorithm-visualizer | Docker Node 20でtypecheck/lint/format/15テスト/build成功。yarn audit 0件。CSSは変更前とバイト一致。PR CI成功 | ComposeのDebian Release期限切れを回避して同じ公式Nodeイメージの分離コンテナを利用。全端末の画面比較ではない |
| learning-transformer | Node 24で15テスト成功。両公開パスでbuild成功。npm audit 0件。全22ページのHTMLはアセットハッシュ以外一致。ブラウザで136要素の位置・寸法・色一致、数式・Mermaid・検索確認。PR CI成功 | VitePress 1にVite 6.4.3をoverride。今後のVitePress更新時にoverrideの要否を確認 |
| BaseballGame | 本番gulpビルドと11テスト（得点境界、乱数、当たり判定、配信ファイル）を実行 | 変更前はNode Sassと旧WebpackのNode互換性でビルド不可。Firebase認証・保存、実ブラウザのゲーム操作、旧Sassとの全CSS比較は未確認。表示・操作の完全同一性を保証できないためDraft PR |
| dev-log | lint、既存4スイート24テスト、本番SSGビルド成功。Bootstrap/React/React Bootstrap/React Icons/Sassは元の版を維持 | 変更前の分離ビルドは旧LMDBのbuffer boundsエラーで完了できず、全記事の変更前後画像比較は未完了。表示の完全同一性を保証できないためDraft PR |
| no1-company-share | Nuxt build、UI/API入力/認証ヘッダー/エラー表示の20テスト成功。FunctionsはNode 22コンテナで型チェックと3契約テスト成功。Firebase CLI起動確認 | 実Firebase認証・DBへの投稿/保存、全画面の表示比較、本番Functionsデプロイは未実施。Vue/Vuetifyの同系列更新を含むため表示の完全同一性は未保証。Draft PR |

no1-company-shareの全体lintは既存の生成済みfirebase-auth-sw.jsにあるrequire-await/prefer-constエラーと開発用コントローラのconsole警告が残ります。変更したテスト・Axiosプラグイン・Jest設定は個別ESLintを実行しました。Functionsには既存の未使用_context警告が残ります。

BaseballGameの批判的チェックでは、既存のgetRandomNumber(3, 3)が乱数を1 - Number.EPSILONにした極端な丸め境界で4を返すことを確認しました。依存更新前からの実装にある問題で、今回の「挙動を変えない」条件に従ってロジックは変更していません。追加テストは実用的な両端代表値（0/0.999999）、同じ上下限、得点境界などを確認します。この既存不具合を含め、全入力で問題がないとは保証できません。

開発ツールの意図した変更: BaseballGameのlintは既存ESLintの公式APIで実行し、エラーをビルド失敗として返すようにしました。Functionsはサポート終了したNode 16指定からNode 22へ変更し、第1世代の毎日0時・Asia/Tokyo・既存PUT先をテストで維持しています。実環境でのランタイム移行検証は別途必要です。

## なぜ残るのか、将来の解消条件

### BaseballGame

- Firebase 8の名前空間APIに認証・Firestore実装が依存しています。修正対象はFirebase 10.9以降とprotobufjs 7以降で、SDK内部依存だけのメジャー強制置換は互換性を保証できません。公式compat APIへの移行かmodular APIへの移行を行い、ログイン/ゲスト/保存/ランキングをFirebase Emulator等で同じ入力と結果で比較できれば解消を進められます。対応ブラウザの変更も確認が必要です。
- gulp-webserver 0.9.1が古いgulp-util/lodash.template、HTTPサーバー・自動ブラウザ起動依存を固定しています。lodash.templateには該当版の修正がありません。保守されている開発サーバーへの置換と、ポート4000・配信パス・監視/ライブリロード・自動起動の回帰確認が必要です。アラートを隠すための依存overrideは採用していません。
- Node Sassは公式に保守終了のため、公式推奨のDart Sassを採用しました。[Sass公式の案内](https://sass-lang.com/blog/node-sass-is-end-of-life/)。旧版を無理に動かすための非公式バイナリは追加していません。

### dev-log

- Gatsby 4とその旧プラグインがsanitize-html 1、PostCSS 7、Sharp 0.30、旧Parcel・webpack-dev-middleware等を要求します。修正版へのメジャー更新はHTMLサニタイズ結果、Markdown変換、CSS、画像生成、開発サーバーのAPIに影響します。すべてを一括overrideしてbuildが通っただけでは表示の同一性を保証できません。
- Gatsby本体と公式プラグインを互換性のある系列へそろえて移行し、GraphQL生成型・RSS・サブパス・画像・全記事HTMLと画像を比較する必要があります。Sharp等については移行先が修正版を採用していることも個別に再監査してください。
- 元の本番成果物か旧環境で再現できるビルドを比較基準として確保すると、残る移行の表示差分を検証できます。今回のUI/Sass固定はその比較を小さくするためです。

### no1-company-share

- Nuxt 2/Vue 2/Vuetify 2には、Nuxt 3/Vue 3/Vuetify 3以降での修正や未修正のvue-template-compiler等があります。これらは単なるバージョン指定変更では互換になりません。Vue 3対応コンポーネント、Nuxtモジュール、ストア/SSR/認証プラグインを移行し、一覧・詳細・投稿・編集・削除・ブックマーク・通報・ログイン・サービスワーカーの回帰テストが必要です。
- @nuxtjs/firebaseが旧Admin SDK/Firestore/protobufjsを持ち込みます。サーバー側SDKだけを強制更新するとモジュールの認証契約を壊す可能性があります。モジュール移行とFirebase Emulatorによるトークン/SSR/保存の検証を先に整える必要があります。
- 最新Firebase CLIにもstream-json 1系、古いUUID等が残ります。stream-json 3はメジャーが異なり、UUIDも旧系列を要求する上流があります。上流が修正版へ移行したCLI/Google SDKの公開、または各内部呼び出しの互換性検証が解消条件です。
- Functionsのnpm監査に残る中程度の項目は主にGoogle Storage系のUUID由来です。実装が使用するスケジュールとPUTの契約は確認しましたが、Google SDK内部の全UUID呼び出しのメジャー互換性までは保証していません。

## サプライチェーンへの配慮

新たに採用した実行用ライブラリは公式推奨のsassで、その他は既存の公式パッケージ系列を更新しました。未使用のFirebaseテストSDKと古いGulp ESLintラッパーは削除し、テストにはNode標準のtest/assertを利用しました。初回取得はinstallスクリプトを無効化し、Sharp等の必要な既存ネイティブ処理だけを後で実行しました。配布URLとintegrityはロックファイルに保持し、コミット対象をgitleaksで検査しました。no1-company-shareでは差分の文脈に含まれる既存Firebaseクライアント設定が1件検出されましたが、その値は追加・変更しておらず、追加行のスキャンは0件でした。将来の侵害まで防げるという保証ではありません。

## 残存アラートの追跡表

以下は取得時のアラートのうち修正ブランチでも対象範囲に入るものです。修正版候補はGitHubが示したfirst patched versionで、親依存との互換性を保証するものではありません。

### BaseballGame

| manifest / package | 残存バージョン | アラート数 | 追跡先 |
| --- | --- | ---: | --- |
| application/yarn.lock / protobufjs | 6.11.6 | 11 | [#125](https://github.com/shin4488/BaseballGame/security/dependabot/125) [#124](https://github.com/shin4488/BaseballGame/security/dependabot/124) [#115](https://github.com/shin4488/BaseballGame/security/dependabot/115) [#114](https://github.com/shin4488/BaseballGame/security/dependabot/114) [#113](https://github.com/shin4488/BaseballGame/security/dependabot/113) [#112](https://github.com/shin4488/BaseballGame/security/dependabot/112) [#111](https://github.com/shin4488/BaseballGame/security/dependabot/111) [#110](https://github.com/shin4488/BaseballGame/security/dependabot/110) [#109](https://github.com/shin4488/BaseballGame/security/dependabot/109) [#107](https://github.com/shin4488/BaseballGame/security/dependabot/107) [#105](https://github.com/shin4488/BaseballGame/security/dependabot/105) |
| application/yarn.lock / qs | 2.2.4, 2.2.5 | 3 | [#79](https://github.com/shin4488/BaseballGame/security/dependabot/79) [#70](https://github.com/shin4488/BaseballGame/security/dependabot/70) [#48](https://github.com/shin4488/BaseballGame/security/dependabot/48) |
| application/yarn.lock / open | 0.0.5 | 1 | [#47](https://github.com/shin4488/BaseballGame/security/dependabot/47) |
| application/yarn.lock / firebase | 8.10.1 | 1 | [#39](https://github.com/shin4488/BaseballGame/security/dependabot/39) |
| application/yarn.lock / body-parser | 1.8.4 | 1 | [#34](https://github.com/shin4488/BaseballGame/security/dependabot/34) |
| application/yarn.lock / lodash.template | 2.4.1 | 1 | [#23](https://github.com/shin4488/BaseballGame/security/dependabot/23) |

### dev-log

| manifest / package | 残存バージョン | アラート数 | 追跡先 |
| --- | --- | ---: | --- |
| yarn.lock / sanitize-html | 1.27.5 | 8 | [#221](https://github.com/shin4488/dev-log/security/dependabot/221) [#217](https://github.com/shin4488/dev-log/security/dependabot/217) [#201](https://github.com/shin4488/dev-log/security/dependabot/201) [#94](https://github.com/shin4488/dev-log/security/dependabot/94) [#56](https://github.com/shin4488/dev-log/security/dependabot/56) [#49](https://github.com/shin4488/dev-log/security/dependabot/49) [#2](https://github.com/shin4488/dev-log/security/dependabot/2) [#1](https://github.com/shin4488/dev-log/security/dependabot/1) |
| yarn.lock / decode-uri-component | 0.2.2 | 1 | [#213](https://github.com/shin4488/dev-log/security/dependabot/213) |
| yarn.lock / postcss | 7.0.36, 7.0.39 | 5 | [#204](https://github.com/shin4488/dev-log/security/dependabot/204) [#198](https://github.com/shin4488/dev-log/security/dependabot/198) [#197](https://github.com/shin4488/dev-log/security/dependabot/197) [#148](https://github.com/shin4488/dev-log/security/dependabot/148) [#41](https://github.com/shin4488/dev-log/security/dependabot/41) |
| yarn.lock / sharp | 0.30.7 | 2 | [#196](https://github.com/shin4488/dev-log/security/dependabot/196) [#43](https://github.com/shin4488/dev-log/security/dependabot/43) |
| yarn.lock / immutable | 3.8.4 | 1 | [#194](https://github.com/shin4488/dev-log/security/dependabot/194) |
| yarn.lock / tmp | 0.0.33 | 2 | [#164](https://github.com/shin4488/dev-log/security/dependabot/164) [#93](https://github.com/shin4488/dev-log/security/dependabot/93) |
| yarn.lock / serialize-javascript | 5.0.1 | 2 | [#163](https://github.com/shin4488/dev-log/security/dependabot/163) [#122](https://github.com/shin4488/dev-log/security/dependabot/122) |
| yarn.lock / uuid | 8.3.2 | 1 | [#162](https://github.com/shin4488/dev-log/security/dependabot/162) |
| yarn.lock / file-type | 16.5.4 | 1 | [#129](https://github.com/shin4488/dev-log/security/dependabot/129) |
| yarn.lock / @parcel/reporter-dev-server | 2.6.2 | 1 | [#101](https://github.com/shin4488/dev-log/security/dependabot/101) |
| yarn.lock / cookie | 0.4.2 | 1 | [#69](https://github.com/shin4488/dev-log/security/dependabot/69) |
| yarn.lock / webpack-dev-middleware | 4.3.0 | 1 | [#51](https://github.com/shin4488/dev-log/security/dependabot/51) |
| yarn.lock / got | 9.6.0 | 1 | [#9](https://github.com/shin4488/dev-log/security/dependabot/9) |

### no1-company-share

| manifest / package | 残存バージョン | アラート数 | 追跡先 |
| --- | --- | ---: | --- |
| functions/yarn.lock / stream-json | 1.9.1 | 1 | [#572](https://github.com/shin4488/no1-company-share/security/dependabot/572) |
| functions/yarn.lock / uuid | 8.3.2, 9.0.1 | 1 | [#522](https://github.com/shin4488/no1-company-share/security/dependabot/522) |
| functions/functions/yarn.lock / uuid | 9.0.1 | 1 | [#387](https://github.com/shin4488/no1-company-share/security/dependabot/387) |
| functions/functions/package-lock.json / uuid | 9.0.1 | 1 | [#292](https://github.com/shin4488/no1-company-share/security/dependabot/292) |
| application/yarn.lock / decode-uri-component | 0.2.2 | 1 | [#226](https://github.com/shin4488/no1-company-share/security/dependabot/226) |
| application/yarn.lock / postcss | 7.0.39 | 5 | [#220](https://github.com/shin4488/no1-company-share/security/dependabot/220) [#216](https://github.com/shin4488/no1-company-share/security/dependabot/216) [#215](https://github.com/shin4488/no1-company-share/security/dependabot/215) [#152](https://github.com/shin4488/no1-company-share/security/dependabot/152) [#40](https://github.com/shin4488/no1-company-share/security/dependabot/40) |
| application/yarn.lock / tar | 6.2.1 | 12 | [#217](https://github.com/shin4488/no1-company-share/security/dependabot/217) [#210](https://github.com/shin4488/no1-company-share/security/dependabot/210) [#209](https://github.com/shin4488/no1-company-share/security/dependabot/209) [#208](https://github.com/shin4488/no1-company-share/security/dependabot/208) [#207](https://github.com/shin4488/no1-company-share/security/dependabot/207) [#192](https://github.com/shin4488/no1-company-share/security/dependabot/192) [#130](https://github.com/shin4488/no1-company-share/security/dependabot/130) [#129](https://github.com/shin4488/no1-company-share/security/dependabot/129) [#117](https://github.com/shin4488/no1-company-share/security/dependabot/117) [#113](https://github.com/shin4488/no1-company-share/security/dependabot/113) [#111](https://github.com/shin4488/no1-company-share/security/dependabot/111) [#110](https://github.com/shin4488/no1-company-share/security/dependabot/110) |
| application/yarn.lock / http-proxy-middleware | 1.3.1 | 4 | [#198](https://github.com/shin4488/no1-company-share/security/dependabot/198) [#86](https://github.com/shin4488/no1-company-share/security/dependabot/86) [#85](https://github.com/shin4488/no1-company-share/security/dependabot/85) [#73](https://github.com/shin4488/no1-company-share/security/dependabot/73) |
| application/yarn.lock / nuxt | 2.18.1 | 2 | [#197](https://github.com/shin4488/no1-company-share/security/dependabot/197) [#64](https://github.com/shin4488/no1-company-share/security/dependabot/64) |
| application/yarn.lock / protobufjs | 6.11.3, 6.11.6 | 12 | [#196](https://github.com/shin4488/no1-company-share/security/dependabot/196) [#195](https://github.com/shin4488/no1-company-share/security/dependabot/195) [#173](https://github.com/shin4488/no1-company-share/security/dependabot/173) [#171](https://github.com/shin4488/no1-company-share/security/dependabot/171) [#170](https://github.com/shin4488/no1-company-share/security/dependabot/170) [#169](https://github.com/shin4488/no1-company-share/security/dependabot/169) [#168](https://github.com/shin4488/no1-company-share/security/dependabot/168) [#167](https://github.com/shin4488/no1-company-share/security/dependabot/167) [#166](https://github.com/shin4488/no1-company-share/security/dependabot/166) [#164](https://github.com/shin4488/no1-company-share/security/dependabot/164) [#151](https://github.com/shin4488/no1-company-share/security/dependabot/151) [#39](https://github.com/shin4488/no1-company-share/security/dependabot/39) |
| application/yarn.lock / tmp | 0.0.33 | 2 | [#177](https://github.com/shin4488/no1-company-share/security/dependabot/177) [#92](https://github.com/shin4488/no1-company-share/security/dependabot/92) |
| application/yarn.lock / serialize-javascript | 5.0.1, 6.0.2, 4.0.0 | 2 | [#176](https://github.com/shin4488/no1-company-share/security/dependabot/176) [#127](https://github.com/shin4488/no1-company-share/security/dependabot/127) |
| application/yarn.lock / uuid | 8.3.2 | 1 | [#175](https://github.com/shin4488/no1-company-share/security/dependabot/175) |
| application/yarn.lock / @tootallnate/once | 1.1.2 | 1 | [#174](https://github.com/shin4488/no1-company-share/security/dependabot/174) |
| application/yarn.lock / defu | 3.2.2, 5.0.1 | 1 | [#147](https://github.com/shin4488/no1-company-share/security/dependabot/147) |
| application/yarn.lock / devalue | 2.0.1 | 4 | [#132](https://github.com/shin4488/no1-company-share/security/dependabot/132) [#120](https://github.com/shin4488/no1-company-share/security/dependabot/120) [#119](https://github.com/shin4488/no1-company-share/security/dependabot/119) [#95](https://github.com/shin4488/no1-company-share/security/dependabot/95) |
| application/yarn.lock / elliptic | 6.6.1 | 1 | [#109](https://github.com/shin4488/no1-company-share/security/dependabot/109) |
| application/yarn.lock / vuetify | 2.7.2 | 2 | [#107](https://github.com/shin4488/no1-company-share/security/dependabot/107) [#106](https://github.com/shin4488/no1-company-share/security/dependabot/106) |
| application/yarn.lock / parse-git-config | 3.0.0 | 1 | [#83](https://github.com/shin4488/no1-company-share/security/dependabot/83) |
| application/yarn.lock / firebase | 9.23.0 | 1 | [#76](https://github.com/shin4488/no1-company-share/security/dependabot/76) |
| application/yarn.lock / vue | 2.7.16 | 1 | [#74](https://github.com/shin4488/no1-company-share/security/dependabot/74) |
| application/yarn.lock / cookie | 0.3.1 | 1 | [#71](https://github.com/shin4488/no1-company-share/security/dependabot/71) |
| application/yarn.lock / micromatch | 3.1.10 | 1 | [#65](https://github.com/shin4488/no1-company-share/security/dependabot/65) |
| application/yarn.lock / vue-template-compiler | 2.7.16 | 1 | [#60](https://github.com/shin4488/no1-company-share/security/dependabot/60) |
| application/yarn.lock / braces | 2.3.2 | 1 | [#56](https://github.com/shin4488/no1-company-share/security/dependabot/56) |
| application/yarn.lock / ip | 2.0.1 | 1 | [#55](https://github.com/shin4488/no1-company-share/security/dependabot/55) |
| application/yarn.lock / babel-traverse | 6.26.0 | 1 | [#51](https://github.com/shin4488/no1-company-share/security/dependabot/51) |
| application/yarn.lock / @google-cloud/firestore | 4.15.1 | 1 | [#43](https://github.com/shin4488/no1-company-share/security/dependabot/43) |
| application/yarn.lock / jsonwebtoken | 8.5.1 | 3 | [#28](https://github.com/shin4488/no1-company-share/security/dependabot/28) [#25](https://github.com/shin4488/no1-company-share/security/dependabot/25) [#24](https://github.com/shin4488/no1-company-share/security/dependabot/24) |

## PRと再開方法

- [algorithm-visualizer #19](https://github.com/shin4488/algorithm-visualizer/pull/19)
- [learning-transformer #17](https://github.com/shin4488/learning-transformer/pull/17)
- [BaseballGame #17（Draft）](https://github.com/shin4488/BaseballGame/pull/17)
- [dev-log #75（Draft）](https://github.com/shin4488/dev-log/pull/75)
- [no1-company-share #57（Draft）](https://github.com/shin4488/no1-company-share/pull/57)

マージ前にDraftの未検証条件を満たし、マージ後にルートでmake dependabotを再実行します。残存項目は個々のsecurity/dependabotページとnpm/yarn監査を再確認してください。アラートのdismissや危険なメジャー強制override、実環境デプロイは行っていません。
