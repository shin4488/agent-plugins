"""Run ShellCheck without executing shell code and emit GitHub-compatible SARIF."""

import json
import subprocess
import sys
from urllib.parse import quote


def main():
    if not sys.argv[1:]:
        raise SystemExit("Specify the shell entry points to analyze.")
    scan = subprocess.run(
        ["shellcheck", "--check-sourced", "--external-sources", "--source-path=SCRIPTDIR", "--format=json1", "--", *sys.argv[1:]],
        capture_output=True,
        text=True,
    )
    # 1は検出あり。実行・入力エラーを空の解析結果として登録しない。
    if scan.returncode not in (0, 1):
        sys.stderr.write(scan.stderr)
        raise SystemExit(scan.returncode)
    comments = json.loads(scan.stdout)["comments"]
    rules = {}
    results = []
    for finding in comments:
        rule_id = f"SC{finding['code']}"
        rules.setdefault(rule_id, {
            "id": rule_id,
            "helpUri": f"https://www.shellcheck.net/wiki/{rule_id}",
            "shortDescription": {"text": rule_id},
        })
        results.append({
            "ruleId": rule_id,
            "level": {"error": "error", "warning": "warning", "info": "note", "style": "note"}[finding["level"]],
            "message": {"text": finding["message"]},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": quote(finding["file"], safe="/"), "uriBaseId": "%SRCROOT%"},
                "region": {"startLine": finding["line"], "startColumn": finding["column"]},
            }}],
        })
    version = subprocess.check_output(["shellcheck", "--version"], text=True)
    version = next(line.removeprefix("version: ") for line in version.splitlines() if line.startswith("version: "))
    json.dump({
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "ShellCheck", "version": version,
                "informationUri": "https://www.shellcheck.net/", "rules": list(rules.values()),
            }},
            "results": results,
            "invocations": [{"executionSuccessful": True}],
        }],
    }, sys.stdout)
    print()


if __name__ == "__main__":
    main()
