"""READMEの「編集後フック（post-edit）」に書いた動作を、hooks/scripts/post-edit.sh に編集イベントを渡して確かめる。

一時ディレクトリに作ったGitリポジトリと、呼び出しを記録する模擬のterraform・biome・リポジトリ固有のpost-edit.shを使う。
"""

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

POST_EDIT = Path(__file__).resolve().parent.parent / "hooks" / "scripts" / "post-edit.sh"
# ホストにあるterraformなどを使わないよう、PATHにはフックが使うこれらのコマンドと模擬コマンドだけを置く。
HOOK_COMMANDS = ("bash", "cat", "dirname", "git", "jq", "realpath")


def patch(*lines):
    return "\n".join(["*** Begin Patch", *lines, "*** End Patch"])


def update(path):
    return [f"*** Update File: {path}", "@@", "-old", "+new"]


class HookTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        # フックはリンクを解決したパスを渡すため、期待値もそろえる（macOSの /var は /private/var へのリンク）。
        self.tmp = Path(os.path.realpath(tmp.name))
        self.repo = self.tmp / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.log_dir = self.tmp / "log"
        self.log_dir.mkdir()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        for name in HOOK_COMMANDS:
            path = shutil.which(name)
            self.assertIsNotNone(path, f"{name} が見つかりません")
            (self.bin / name).symlink_to(path)

    def make_file(self, relative, base=None):
        path = (base or self.repo) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
        return str(path)

    def write_command(self, path, name, status=0, header="#!/usr/bin/env bash"):
        """呼び出しごとに作業ディレクトリと引数を記録し、標準出力・標準エラー出力に書いてstatusで終わるコマンドを置く。"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        log = shlex.quote(str(self.log_dir / f"{name}.jsonl"))
        path.write_text(
            f"{header}\n"
            # -で始まる引数をjqのオプションと取り違えないよう、1つずつ標準入力から渡す。
            # jq 1.6は -Rs で読んだ入力の末尾のNULを落とすため、NUL区切りでは渡さない。
            f"for arg in \"$PWD\" \"$@\"; do printf '%s' \"$arg\" | jq -Rs .; done | jq -cs . >> {log}\n"
            f"echo '{name} stdout'\n"
            f"echo '{name} stderr' >&2\n"
            f"exit {status}\n"
        )
        path.chmod(0o755)

    def add_repository_hook(self, status=0):
        hook = self.repo / ".claude" / "hooks" / "post-edit.sh"
        stdin = shlex.quote(str(self.log_dir / "repository-hook.stdin"))
        # shebangに関係なくbashで、実行権限がなくても実行されることを、あわせて確かめる。
        self.write_command(hook, "repository-hook", status, header=f"#!/usr/bin/env python3\ncat > {stdin}")
        hook.chmod(0o644)

    def calls(self, name):
        """[作業ディレクトリ, 引数...] を呼び出しの順に返す。"""
        log = self.log_dir / f"{name}.jsonl"
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text().splitlines()]

    def run_hook(self, tool_name, tool_input, cwd=None, tool_response=None):
        event = {"cwd": str(cwd or self.repo), "tool_name": tool_name, "tool_input": tool_input}
        if tool_response is not None:
            event["tool_response"] = tool_response
        return subprocess.run(
            ["bash", str(POST_EDIT)],
            input=json.dumps(event),
            capture_output=True,
            encoding="utf-8",
            # 対象のリポジトリは、フックを起動した場所ではなく編集イベントのcwdから決まる。
            cwd=self.tmp,
            # 一時ディレクトリの上位にあるGitリポジトリを見つけないようにする。
            env={"PATH": str(self.bin), "HOME": str(self.tmp), "GIT_CEILING_DIRECTORIES": str(self.tmp)},
        )


class TargetFilesTest(HookTestCase):
    """どのファイルを、どの形でリポジトリ固有のpost-edit.shに渡すか。"""

    def setUp(self):
        super().setUp()
        self.add_repository_hook()

    def test_write_edit_multiedit_pass_absolute_path_from_repository_root_without_stdin(self):
        target = self.make_file("src/app.txt")
        for tool_name in ("Write", "Edit", "MultiEdit"):
            with self.subTest(tool_name=tool_name):
                result = self.run_hook(tool_name, {"file_path": target}, cwd=self.repo / "src")
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls("repository-hook"), [[str(self.repo), target]] * 3)
        self.assertEqual((self.log_dir / "repository-hook.stdin").read_text(), "")

    def test_apply_patch_passes_added_updated_and_moved_files_in_one_call(self):
        added = self.make_file("src/added.txt")
        updated = self.make_file("src/updated.txt")
        moved = self.make_file("src/moved.txt")
        result = self.run_hook(
            "apply_patch",
            {
                "command": patch(
                    "*** Add File: added.txt",
                    "+new",
                    *update("updated.txt"),
                    "*** Update File: before-move.txt",
                    "*** Move to: moved.txt",
                    "@@",
                    "-old",
                    "+new",
                    "*** Delete File: deleted.txt",
                )
            },
            cwd=self.repo / "src",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        [call] = self.calls("repository-hook")
        self.assertEqual(call[0], str(self.repo))
        self.assertCountEqual(call[1:], [added, updated, moved])

    def test_failed_edit_runs_nothing(self):
        target = self.make_file("app.txt")
        result = self.run_hook("Write", {"file_path": target}, tool_response={"success": False})
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertEqual(self.calls("repository-hook"), [])

    def test_files_outside_repository_are_excluded(self):
        inside = self.make_file("inside.txt")
        outside = self.make_file("outside.txt", base=self.tmp)
        (self.repo / "link-to-outside.txt").symlink_to(outside)
        result = self.run_hook(
            "apply_patch",
            {"command": patch(*update("../outside.txt"), *update("link-to-outside.txt"), *update("inside.txt"))},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls("repository-hook"), [[str(self.repo), inside]])

    def test_same_file_through_symlink_is_passed_once(self):
        target = self.make_file("real.txt")
        (self.repo / "link.txt").symlink_to("real.txt")
        result = self.run_hook("apply_patch", {"command": patch(*update("real.txt"), *update("link.txt"))})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls("repository-hook"), [[str(self.repo), target]])

    def test_file_name_with_space_and_trailing_newline_is_passed_unchanged(self):
        target = self.make_file("dir name/file name\n")
        result = self.run_hook("Write", {"file_path": target})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls("repository-hook"), [[str(self.repo), target]])

    def test_edit_outside_git_repository_runs_nothing(self):
        self.write_command(self.bin / "terraform", "terraform")
        work = self.tmp / "not-a-repository"
        target = self.make_file("main.tf", base=work)
        result = self.run_hook("Write", {"file_path": target}, cwd=work)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertEqual(self.calls("terraform"), [])


class RepositoryHookTest(HookTestCase):
    """リポジトリ固有のpost-edit.shがあるときの実行と結果の返し方。"""

    def setUp(self):
        super().setUp()
        self.write_command(self.bin / "terraform", "terraform")
        self.target = self.make_file("main.tf")

    def test_output_and_exit_code_are_returned_unchanged_instead_of_standard_processing(self):
        self.add_repository_hook(status=3)
        result = self.run_hook("Write", {"file_path": self.target})
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr),
            (3, "repository-hook stdout\n", "repository-hook stderr\n"),
        )
        self.assertEqual(self.calls("repository-hook"), [[str(self.repo), self.target]])
        self.assertEqual(self.calls("terraform"), [])

    def test_hook_linked_outside_repository_runs_neither_it_nor_standard_processing(self):
        outside = self.tmp / "outside-hook.sh"
        self.write_command(outside, "repository-hook")
        link = self.repo / ".claude" / "hooks" / "post-edit.sh"
        link.parent.mkdir(parents=True)
        link.symlink_to(outside)
        result = self.run_hook("Write", {"file_path": self.target})
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertEqual(self.calls("repository-hook"), [])
        self.assertEqual(self.calls("terraform"), [])


class StandardProcessingTest(HookTestCase):
    """リポジトリ固有のpost-edit.shがないときのTerraform・Biomeの処理。"""

    def test_terraform_formats_edited_files_and_validates_only_initialized_directories(self):
        self.write_command(self.bin / "terraform", "terraform")
        infra = self.repo / "infra"
        network = self.repo / "modules" / "network"
        first = self.make_file("infra/a.tf")
        second = self.make_file("infra/b.tf")
        self.make_file("infra/unedited.tf")
        (infra / ".terraform").mkdir()
        module = self.make_file("modules/network/main.tf")
        result = self.run_hook(
            "apply_patch",
            {"command": patch(*update("infra/a.tf"), *update("infra/b.tf"), *update("modules/network/main.tf"))},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertCountEqual(
            self.calls("terraform"),
            [
                [str(infra), "fmt", first],
                [str(infra), "fmt", second],
                [str(network), "fmt", module],
                [str(infra), "validate", "-no-color"],
            ],
        )
        # 未初期化のためvalidateを飛ばしたディレクトリを、理由とともに出力する。
        self.assertIn(str(network), result.stderr)

    def test_biome_checks_files_once_per_project_with_its_installed_biome(self):
        # web/ は依存をリポジトリのルートに置き、入れ子の設定を持つ。tools/ は自分の依存を持つ。
        self.write_command(self.repo / "node_modules" / ".bin" / "biome", "root-biome")
        self.write_command(self.repo / "tools" / "node_modules" / ".bin" / "biome", "tools-biome")
        self.make_file("web/biome.json")
        self.make_file("web/app/biome.jsonc")
        self.make_file("tools/biome.json")
        page = self.make_file("web/app/page.tsx")
        style = self.make_file("web/style.css")
        script = self.make_file("tools/build.js")
        self.make_file("README.md")
        self.make_file("package.json")
        result = self.run_hook(
            "apply_patch",
            {
                "command": patch(
                    *update("web/app/page.tsx"),
                    *update("web/style.css"),
                    *update("tools/build.js"),
                    *update("README.md"),
                    *update("package.json"),
                )
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        for name, files in (("root-biome", [page, style]), ("tools-biome", [script])):
            with self.subTest(name=name):
                [call] = self.calls(name)
                args = call[1:]
                self.assertEqual(args[:2], ["check", "--write"])
                self.assertNotIn("--unsafe", args)
                self.assertCountEqual([arg for arg in args[2:] if not arg.startswith("--")], files)

    def test_missing_terraform_and_biome_are_skipped_with_reason(self):
        self.make_file("main.tf")
        self.make_file("web/biome.json")
        self.make_file("web/app.ts")
        result = self.run_hook("apply_patch", {"command": patch(*update("main.tf"), *update("web/app.ts"))})
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertIn("terraform", result.stderr)
        self.assertIn(str(self.repo / "web"), result.stderr)

    def test_tool_failure_returns_exit_code_2_with_its_output_on_stderr(self):
        cases = (
            ("terraform", self.bin / "terraform", "main.tf"),
            ("biome", self.repo / "node_modules" / ".bin" / "biome", "app.ts"),
        )
        self.make_file("biome.json")
        for name, command, file in cases:
            with self.subTest(name=name):
                self.write_command(command, name, status=1)
                result = self.run_hook("Write", {"file_path": self.make_file(file)})
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertIn(f"{name} stdout", result.stderr)
                self.assertIn(f"{name} stderr", result.stderr)


if __name__ == "__main__":
    unittest.main()
