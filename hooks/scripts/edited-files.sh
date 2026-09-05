#!/usr/bin/env bash
# 呼び出し元の input・event_cwd・project_dir から files 配列を作る。
# 失敗が明示された編集は除外する。改名は移動先を使い、削除されたファイルは整形しない。
paths=$(jq -c '[
  if (.tool_response | type) == "object" and .tool_response.success == false then empty
  elif .tool_name == "apply_patch" then
    (.tool_input.command | split("\n")) as $lines
    | range(0; $lines | length) as $i
    | select(($lines[$i + 1] // "" | startswith("*** Move to: ")) | not)
    | $lines[$i]
    | capture("^\\*\\*\\* (?:Add File|Update File|Move to): (?<path>.+)$").path
  elif (.tool_name == "Write" or .tool_name == "Edit" or .tool_name == "MultiEdit") then
    .tool_input.file_path // .tool_response.filePath // empty
  else empty end
] | unique' <<< "$input") || exit 2

files=()
while IFS= read -r -d '' path; do
  case "$path" in /*) ;; *) path="$event_cwd/$path" ;; esac
  [ -f "$path" ] || continue
  # ../ とリンクを解決し、リポジトリ外と削除済みファイルを除外する。
  # 末尾が改行のファイル名も、コマンド置換で欠けないようにする。
  path=$(realpath "$path" && printf '.') || exit 2
  path=${path%$'\n.'}
  case "$path" in "$project_dir"/*) ;; *) continue ;; esac
  # 実パスとリンク経由のパスが同じファイルを指しても、整形は1回にする。
  for file in "${files[@]}"; do
    [ "$file" != "$path" ] || continue 2
  done
  files+=("$path")
done < <(jq -j '.[] | ., "\u0000"' <<< "$paths")
