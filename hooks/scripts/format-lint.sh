#!/usr/bin/env bash
# 作業ディレクトリはリポジトリルート、引数は編集済みファイルの絶対パス。
project_dir=$PWD
terraform_dirs=()
biome_dirs=()
biome_files=()
status=0

# NUL区切りで、空白や改行を含むディレクトリも1件として扱う。
unique_dirs() {
  printf '%s\0' "$@" | jq -jRs 'split("\u0000") | unique[] | select(length > 0) | ., "\u0000"'
}

for file; do
  dir=${file%/*}
  case "$file" in
    *.tf)
      if ! command -v terraform >/dev/null 2>&1; then
        printf 'Terraformをスキップ: terraformが見つかりません\n' >&2
        continue
      fi
      # 編集ファイルだけを整形し、無関係な.tfに差分を作らない。
      # ファイルの場所で起動し、tfenv等にリポジトリのバージョン指定を読ませる。
      (cd "$dir" && terraform fmt "$file") >&2 || status=2
      terraform_dirs+=("$dir")
      ;;
    *.ts | *.tsx | *.js | *.jsx | *.json | *.jsonc | *.css | *.html)
      # このファイルの祖先にある最上位の設定を、プロジェクトの入口にする。
      # 入れ子のroot:falseやextendsはBiome自身に解決させ、JSONCをシェルで解析しない。
      config_dir=
      while :; do
        if [ -f "$dir/biome.json" ] || [ -f "$dir/biome.jsonc" ]; then
          config_dir=$dir
        fi
        [ "$dir" != "$project_dir" ] || break
        dir=${dir%/*}
      done
      if [ -n "$config_dir" ]; then
        biome_dirs+=("$config_dir")
        biome_files+=("$file")
      fi
      ;;
  esac
done

# validateは編集ファイルと同じモジュールごとに1回にまとめる。
# initはprovider取得や設定変更を伴うため自動実行しない。
# 呼び出し元のroot moduleは拡張子から分からないので、親へ推測して移動しない。
while IFS= read -r -d '' dir; do
  if [ -d "$dir/.terraform" ]; then
    (cd "$dir" && terraform validate -no-color) >&2 || status=2
  else
    printf 'Terraform validateをスキップ（未初期化）: %s\n' "$dir" >&2
  fi
done < <(unique_dirs "${terraform_dirs[@]}")

while IFS= read -r -d '' dir; do
  [ -n "$dir" ] || continue
  # リポジトリのバージョンを使う。npxによる自動取得やホストの別バージョンへの代替はしない。
  # monorepoの依存配置に合わせ、設定の場所からリポジトリルートまでを探索する。
  package_dir=$dir
  while [ ! -x "$package_dir/node_modules/.bin/biome" ]; do
    [ "$package_dir" != "$project_dir" ] || break
    package_dir=${package_dir%/*}
  done
  biome="$package_dir/node_modules/.bin/biome"
  if [ ! -x "$biome" ]; then
    printf 'Biomeをスキップ（依存未インストール）: %s\n' "$dir" >&2
    continue
  fi
  targets=()
  # 同じ設定を起点にするファイルをまとめ、別プロジェクトの対象を混ぜない。
  for i in "${!biome_files[@]}"; do
    [ "${biome_dirs[$i]}" != "$dir" ] || targets+=("${biome_files[$i]}")
  done
  # リポジトリの設定・除外指定を使い、Biomeが安全と分類する修正だけを適用する。
  # --unsafeは付けず、残る指摘をエージェントへ返す。
  # 自動探索に任せず、ファイルごとに選んだ設定の場所を明示する。
  # 除外設定で対象が0件になった場合だけは正常終了とし、設定エラー等は隠さない。
  (cd "$dir" && "$biome" check --write --no-errors-on-unmatched --config-path="$dir" "${targets[@]}") >&2 || status=2
done < <(unique_dirs "${biome_dirs[@]}")

exit "$status"
