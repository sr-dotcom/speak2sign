"""The review script's collection and failure handling, with a stub `codex` on PATH (no network)."""
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "codex_review.sh"
BASH = shutil.which("bash")
needs_bash = pytest.mark.skipif(BASH is None or shutil.which("git") is None, reason="bash and git are both required")


def make_repo(tmp_path, codex_behaviour):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    (repo / "AGENTS.md").write_text("brief\n")
    (repo / "CLAUDE.md").write_text("rules\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "codex").write_text(textwrap.dedent(codex_behaviour))
    (stub / "codex").chmod(0o755)
    return repo, stub


def run(repo, stub, *args):
    env = {**os.environ, "PATH": f"{stub}{os.pathsep}{os.environ['PATH']}"}
    return subprocess.run([BASH, str(SCRIPT), *args], cwd=repo, env=env, capture_output=True, text=True)


ECHO_PAYLOAD = """\
    #!/usr/bin/env bash
    # stub codex: echo the payload back after the marker so the test can inspect it
    payload=$(cat)
    echo "codex"
    echo "$payload"
    """


@needs_bash
def test_nothing_to_review_exits_2(tmp_path):
    repo, stub = make_repo(tmp_path, ECHO_PAYLOAD)
    r = run(repo, stub)
    assert r.returncode == 2 and "nothing to review" in r.stdout


@needs_bash
def test_untracked_file_with_a_space_is_included(tmp_path):
    repo, stub = make_repo(tmp_path, ECHO_PAYLOAD)
    (repo / "new panel.js").write_text("console.log(1)\n")
    r = run(repo, stub)
    assert r.returncode == 0
    assert "new panel.js" in r.stdout and "console.log(1)" in r.stdout
    assert "=== CLAUDE.md ===" in r.stdout and "rules" in r.stdout


@needs_bash
def test_commit_argument_must_name_exactly_one_commit(tmp_path):
    repo, stub = make_repo(tmp_path, ECHO_PAYLOAD)
    for bad in ("HEAD~3", "--stat", "HEAD..HEAD~1"):
        r = run(repo, stub, bad)
        assert r.returncode == 3 and "does not name a commit" in r.stderr, bad
    r = run(repo, stub, "HEAD")
    assert r.returncode == 0 and "=== diff ===" in r.stdout and "AGENTS.md" in r.stdout


@needs_bash
def test_answer_is_taken_between_the_marker_and_the_token_count(tmp_path):
    stub = "#!/usr/bin/env bash\ncat > /dev/null\necho 'mcp: startup noise'\necho codex\necho 'P2 | x | y | z'\necho 'tokens used'\necho '12,345'\necho 'P2 | x | y | z'\n"
    repo, stub_dir = make_repo(tmp_path, stub)
    (repo / "x.txt").write_text("x\n")
    r = run(repo, stub_dir)
    assert r.returncode == 0 and r.stdout.strip() == "P2 | x | y | z"


@needs_bash
def test_codex_failure_is_reported_not_hidden(tmp_path):
    repo, stub = make_repo(tmp_path, "#!/usr/bin/env bash\necho 'auth error: not logged in' >&2\nexit 1\n")
    (repo / "x.txt").write_text("x\n")
    r = run(repo, stub)
    assert r.returncode == 3 and "not logged in" in r.stderr and "unavailable" in r.stderr
