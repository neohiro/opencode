"""
Regression tests for the robust opencode tool wrappers in .opencode/bin/.

These wrappers exist because recent opencode sessions produced hundreds of
tool failures (missing `path` key, oldString not found, ambiguous matches,
ripgrep JSON record overflow, bash fork failures). Each test below pins one
of those failure modes so it cannot silently regress.

Run:  python -m pytest tests/test_opencode_bin.py -q
"""

import json
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(REPO_ROOT, ".opencode", "bin")
EDIT = os.path.join(BIN, "edit")
BASH = os.path.join(BIN, "bash")
SHELL = os.path.join(BIN, "shell")
GREP = os.path.join(BIN, "grep")


def run(script, payload=None, args=None, cwd=None):
    """Invoke a wrapper and return (returncode, parsed_json_or_None, raw)."""
    argv = [sys.executable, script] + (args or [])
    stdin = json.dumps(payload) if payload is not None else ""
    proc = subprocess.run(
        argv, input=stdin, capture_output=True, text=True,
        cwd=cwd or REPO_ROOT, timeout=120,
    )
    raw = proc.stdout.strip() or proc.stderr.strip()
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = None
    return proc.returncode, parsed, raw


# --------------------------------------------------------------------------
# edit
# --------------------------------------------------------------------------

def test_edit_basic_replacement(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello world\nsecond\n", encoding="utf-8")
    rc, res, _ = run(EDIT, {"path": str(f), "oldString": "hello", "newString": "goodbye"})
    assert rc == 0, res
    assert res["success"] is True
    assert res["match_mode"] == "exact"
    assert f.read_text(encoding="utf-8") == "goodbye world\nsecond\n"


def test_edit_accepts_schema_aliases(tmp_path):
    """Sessions used `filePath`/`old_string`; the harness wants `path`/`oldString`."""
    f = tmp_path / "b.txt"
    f.write_text("alpha\n", encoding="utf-8")
    rc, res, _ = run(EDIT, {"filePath": str(f), "old_string": "alpha", "new_string": "beta"})
    assert rc == 0, res
    assert f.read_text(encoding="utf-8") == "beta\n"


def test_edit_missing_path_is_actionable(tmp_path):
    rc, res, _ = run(EDIT, {"oldString": "a", "newString": "b"})
    assert rc == 2
    assert res["success"] is False
    assert "path" in res["message"]


def test_edit_missing_file_is_reported(tmp_path):
    rc, res, _ = run(EDIT, {"path": str(tmp_path / "nope.txt"),
                            "oldString": "a", "newString": "b"})
    assert rc == 1
    assert "not found" in res["message"].lower()


def test_edit_identical_strings_rejected(tmp_path):
    f = tmp_path / "c.txt"
    f.write_text("same\n", encoding="utf-8")
    rc, res, _ = run(EDIT, {"path": str(f), "oldString": "same", "newString": "same"})
    assert rc == 1
    assert "identical" in res["message"].lower()


def test_edit_ambiguous_match_refuses(tmp_path):
    f = tmp_path / "d.txt"
    f.write_text("dup\nx\ndup\n", encoding="utf-8")
    rc, res, _ = run(EDIT, {"path": str(f), "oldString": "dup", "newString": "uniq"})
    assert rc == 1
    assert res["match_count"] == 2
    assert f.read_text(encoding="utf-8") == "dup\nx\ndup\n"  # untouched


def test_edit_replace_all(tmp_path):
    f = tmp_path / "e.txt"
    f.write_text("dup\nx\ndup\n", encoding="utf-8")
    rc, res, _ = run(EDIT, {"path": str(f), "oldString": "dup",
                            "newString": "uniq", "replaceAll": True})
    assert rc == 0, res
    assert f.read_text(encoding="utf-8") == "uniq\nx\nuniq\n"


def test_edit_tolerates_crlf_mismatch(tmp_path):
    f = tmp_path / "f.txt"
    f.write_bytes(b"alpha\r\nbeta\r\ngamma\r\n")
    rc, res, _ = run(EDIT, {"path": str(f), "oldString": "alpha\nbeta",
                            "newString": "BETA"})
    assert rc == 0, res
    assert res["match_mode"] == "eol-normalized"
    data = f.read_bytes()
    assert b"BETA" in data
    assert b"\r\n" in data, "CRLF line endings must be preserved"


def test_edit_crlf_whitespace_tolerant_keeps_offsets(tmp_path):
    """Regression: fuzzy spans were computed on LF-normalised text but applied
    to CRLF text, corrupting the file."""
    body = "line1\r\n" + "def foo():\r\n" + "    return 1\r\n" + "tail\r\n"
    f = tmp_path / "g.txt"
    f.write_bytes(body.encode("utf-8"))
    rc, res, _ = run(EDIT, {"path": str(f), "oldString": "def foo():\n    return 1",
                            "newString": "def foo():\n    return 2"})
    assert rc == 0, res
    assert res["match_mode"] == "whitespace-tolerant"
    text = f.read_bytes().decode("utf-8")
    assert "return 2" in text
    assert "return 1" not in text
    assert "line1" in text and "tail" in text, "surrounding content must survive"


def test_edit_whitespace_tolerant_fallback(tmp_path):
    f = tmp_path / "h.txt"
    f.write_text("def foo():\n        return 1\n", encoding="utf-8")
    rc, res, _ = run(EDIT, {"path": str(f), "oldString": "def foo():\n    return 1",
                            "newString": "def foo():\n        return 2"})
    assert rc == 0, res
    assert res["match_mode"] == "whitespace-tolerant"
    assert f.read_text(encoding="utf-8") == "def foo():\n        return 2\n"


def test_edit_preserves_bom(tmp_path):
    f = tmp_path / "i.txt"
    f.write_bytes(b"\xef\xbb\xbfhello\n")
    rc, res, _ = run(EDIT, {"path": str(f), "oldString": "hello", "newString": "bye"})
    assert rc == 0, res
    assert f.read_bytes().startswith(b"\xef\xbb\xbf"), "BOM must be preserved"


def test_edit_not_found_returns_closest_lines(tmp_path):
    f = tmp_path / "j.txt"
    f.write_text("int main():\n    return 0;\n", encoding="utf-8")
    rc, res, _ = run(EDIT, {"path": str(f), "oldString": "totally unrelated text",
                            "newString": "x"})
    assert rc == 1
    assert res["success"] is False
    assert isinstance(res.get("closest_lines"), list)


def test_edit_cli_flags_form(tmp_path):
    f = tmp_path / "k.txt"
    f.write_text("cli test\n", encoding="utf-8")
    rc, res, _ = run(EDIT, None, args=["--path=" + str(f), "--oldString=cli test",
                                       "--newString=cli ok"])
    assert rc == 0, res
    assert "cli ok" in f.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# bash / shell
# --------------------------------------------------------------------------

def test_bash_runs_simple_command():
    rc, res, _ = run(BASH, None, args=["--command=echo hello"])
    assert rc == 0, res
    assert res["success"] is True
    assert "hello" in res["stdout"]


def test_bash_json_stdin_form():
    rc, res, _ = run(BASH, {"command": "echo from-stdin"})
    assert rc == 0, res
    assert "from-stdin" in res["stdout"]


def test_bash_propagates_exit_code():
    rc, res, _ = run(BASH, None, args=["--command=exit 3"])
    assert rc == 3
    assert res["exitCode"] == 3
    assert res["success"] is False


def test_bash_honours_workdir(tmp_path):
    rc, res, _ = run(BASH, None, args=["--command=cd", "--workdir=" + str(tmp_path)])
    assert rc == 0, res
    # 'cd' alone is a builtin; verify workdir is echoed instead
    rc, res, _ = run(BASH, None, args=["--command=pwd", "--workdir=" + str(tmp_path)])
    assert rc == 0, res
    assert str(tmp_path).lower() in (res.get("stdout") or "").lower()


def test_bash_requires_command():
    rc, res, _ = run(BASH, None, args=[])
    assert rc == 1
    assert res["success"] is False


def test_shell_delegates_and_resolves_own_path(tmp_path):
    """shell must not depend on the caller's cwd."""
    rc, res, _ = run(SHELL, None, args=["--command=echo delegated"], cwd=str(tmp_path))
    assert rc == 0, res
    assert "delegated" in res["stdout"]


# --------------------------------------------------------------------------
# grep
# --------------------------------------------------------------------------

def test_grep_finds_matches_in_single_file(tmp_path):
    f = tmp_path / "k.txt"
    f.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
    rc, res, _ = run(GREP, None, args=["--pattern=beta", "--path=" + str(f)])
    assert rc == 0, res
    assert res["matchCount"] >= 1
    assert any(m.get("line") == 2 for m in res["matches"])


def test_grep_parses_windows_absolute_paths(tmp_path):
    """ripgrep emits C:\\path\\file:12:text - naive split(':') corrupts the line."""
    f = tmp_path / "l.txt"
    f.write_text("needle here\n", encoding="utf-8")
    rc, res, _ = run(GREP, None, args=["--pattern=needle", "--path=" + str(f)])
    assert rc == 0, res
    assert res["matchCount"] >= 1
    first = res["matches"][0]
    assert "file" in first and "line" in first and "text" in first
    assert isinstance(first["line"], int)


def test_grep_rejects_missing_path():
    rc, res, _ = run(GREP, None, args=["--pattern=x", "--path=" + os.path.join(REPO_ROOT, "no_such_dir_zzz")])
    assert rc == 1
    assert res["success"] is False


def test_grep_requires_pattern():
    rc, res, _ = run(GREP, None, args=[])
    assert rc == 2
    assert res["success"] is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
