# タグとReleaseの公開

既存CIがタグ・Releaseを作成する場合は、その手順を使って結果を確認する。手動のGit・GitHub CLI操作で公開する場合は、次の順で進める。

1. タグが未作成なら、確定したコミットSHAを指すタグを作成してpushする。タグの形式はリポジトリの規約に従う。

```bash
git tag <タグ> <対象SHA>
git push <remote> refs/tags/<タグ>
```

2. タグが既にある場合は、参照先が対象SHAと一致することを確認して使う。ローカルにだけある場合は、そのタグをpushする。
3. リモート上のタグを確認してからGitHub Releaseを作成する。タグのpushでCIがReleaseを作る場合は、その完了を確認し、二重作成しない。

```bash
gh release create <タグ> --verify-tag --title <Release名> --notes-file <ノートファイル>
gh release view <タグ>
```

成果物が必要ならリポジトリの手順で添付する。公開後はタグの実際の参照先・Releaseの内容・添付ファイルを確認する。応答が不明な場合は状態を調べてから再実行する。
