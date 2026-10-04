"""Require a plugin version bump when distributed skills or hooks change."""

import json
import re
import subprocess
import sys

MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")
# 利用側へ配布される内容。Claude Codeはversionが同じだと `plugin update` で更新しない。
DISTRIBUTED = ("skills/", "hooks/")
VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def read_version(ref, path):
    try:
        manifest = json.loads(git("show", f"{ref}:{path}"))
    except subprocess.CalledProcessError:
        return None
    return manifest.get("version")


def parse(version):
    match = VERSION.match(version or "")
    return tuple(map(int, match.groups())) if match else None


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit("Usage: check_plugin_version.py <base-ref> [<head-ref>]")
    base, head = sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "HEAD"
    errors = []

    head_versions = {path: read_version(head, path) for path in MANIFESTS}
    for path, version in head_versions.items():
        if parse(version) is None:
            errors.append((path, f"versionをX.Y.Z形式で指定してください（現在: {version}）"))
    if len(set(head_versions.values())) > 1:
        detail = "、".join(f"{path}: {version}" for path, version in head_versions.items())
        errors.append((MANIFESTS[0], f"両manifestのversionをそろえてください（{detail}）"))

    changed = [f for f in git("diff", "--name-only", base, head).splitlines() if f.startswith(DISTRIBUTED)]
    base_version = parse(read_version(base, MANIFESTS[0]))
    head_version = parse(head_versions[MANIFESTS[0]])
    if changed and base_version and head_version and head_version <= base_version:
        listed = "、".join(changed[:5]) + (" ほか" if len(changed) > 5 else "")
        errors.append((
            MANIFESTS[0],
            f"skills/・hooks/ が変更されています（{listed}）。"
            f"利用側で更新されるよう、両manifestのversionを {'.'.join(map(str, base_version))} より上げてください",
        ))

    for path, message in errors:
        print(f"::error file={path}::{message}")
    if errors:
        raise SystemExit(1)
    print(f"OK: version {head_versions[MANIFESTS[0]]}、配布対象の変更 {len(changed)} 件")


if __name__ == "__main__":
    main()
