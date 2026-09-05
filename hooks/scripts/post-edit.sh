#!/usr/bin/env bash
set -e

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
input=$(cat)
# プラグインはキャッシュから実行される。対象リポジトリは編集イベントのcwdから求める。
event_cwd=$(jq -er '.cwd | strings | select(length > 0)' <<< "$input")
project_dir=$(git -C "$event_cwd" rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$project_dir"
project_dir=$(pwd -P)

# 両ツールの入力差をここで吸収し、リポジトリ側にJSON解析を複製させない。
source "$script_dir/edited-files.sh"
[ "${#files[@]}" -gt 0 ] || exit 0

# リポジトリ専用の処理があれば優先する。共通処理と二重には実行しない。
hook="$project_dir/.claude/hooks/post-edit.sh"
if [ -f "$hook" ]; then
  hook=$(realpath "$hook")
  # リポジトリ外のシェルをリンク経由で実行しない。リポジトリ自体の信頼確認は利用者が行う。
  case "$hook" in "$project_dir"/*) ;; *) exit 0 ;; esac
  # 出力と終了コードをそのまま返し、リポジトリ側の失敗を共通側で成功にしない。
  exec bash "$hook" "${files[@]}"
fi

exec bash "$script_dir/format-lint.sh" "${files[@]}"
