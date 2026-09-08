#!/usr/bin/env python3
"""Launch Argus /review through Codex for every open GitHub pull request."""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = "rdeepmath91/agent-dev-command-harness"
REPO_DIR = Path("/Users/mraihanparlaungan/personal/argus/agent-dev-command-harness")
STATE_DIR = Path.home() / ".hermes" / "scripts" / "state" / "argus-review-requests"
LOG_DIR = STATE_DIR / "logs"
BATCH_PATH = STATE_DIR / "batch.json"
USER = "RaihanParl"
USAGE_THRESHOLD = 30.0
GH_BIN = "/Users/mraihanparlaungan/.hermes/scripts/gh-keychain-wrapper"


def weekly_usage_percent() -> float:
    """Read Codex weekly usage from ChatGPT's authenticated usage endpoint."""
    override = os.environ.get("OPENCODE_WEEKLY_USAGE_PERCENT")
    if override is not None:
        raw = override
    else:
        auth_path = Path.home() / ".local" / "share" / "opencode" / "auth.json"
        try:
            auth = json.loads(auth_path.read_text())
            token = auth["openai"]["access"]
            request = urllib.request.Request(
                "https://chatgpt.com/backend-api/wham/usage",
                headers={"Authorization": f"Bearer {token}", "User-Agent": "opencode"},
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.load(response)
            window = payload["rate_limit"]["primary_window"]
            if int(window["limit_window_seconds"]) < 6 * 24 * 60 * 60:
                return 0.0
            return float(window["used_percent"])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return 0.0
    try:
        usage_percent = float(raw)
    except ValueError:
        usage_percent = 0.0
    return usage_percent


def selected_model() -> str:
    return "gpt-5.6-sol" if weekly_usage_percent() > USAGE_THRESHOLD else "gpt-5.6-luna"


def run_review(number: int, url: str, model: str) -> int:
    prompt = (
        "Execute Argus Harness /review for this pull request, then execute "
        "/post-review for the validated current-head result. Read and follow "
        ".commands/review.md as authoritative contract; do not use OpenCode's "
        "generic review command and do not edit implementation files. "
        "review. Treat GitHub's historical PR-level `CHANGES_REQUESTED` "
        "metadata as non-current by itself; only active findings in the "
        "current exact-head report or unresolved current review threads block "
        "approval. If no active findings remain and all publication gates pass, "
        "the verdict must be `approve` and `/post-review` must publish `APPROVE`. "
        "If active findings remain, the verdict must be `changes_requested`, "
        "never `approve`; never claim approve while H-*, M-*, or L-* findings "
        "remain active. Regenerate inconsistent evidence before handoff. Do not report success unless output contains the "
        "canonical GitHub review URL. "
        "or review contract headings with equivalent meaning (for this repository, "
        "`## MVP contract` is acceptance material and `## Validation and handoff` "
        "is validation material). Do not stop merely because legacy exact heading "
        "names are absent when authoritative acceptance and validation bullets "
        "are present; continue Tier 2 and publish the real verdict. "
        "Publication is explicitly authorized for this cron invocation, but "
        "must stop if exact-head, receipt, ledger, helper-provenance, identity, "
        "or live-state checks fail. Before every GitHub CLI command, set "
        "GH_BIN=/Users/mraihanparlaungan/.hermes/scripts/gh-keychain-wrapper "
        "in the same shell command; this wrapper is mandatory. Publish one "
        "review event only after /review succeeds, and report its canonical "
        "GitHub review URL. Target: " + url
    )
    try:
        result = subprocess.run(
            ["codex", "exec", "--sandbox", "danger-full-access", "--model", model, prompt],
            cwd=REPO_DIR,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            env={**os.environ, "GH_BIN": GH_BIN},
            timeout=1800,
        )
    except subprocess.TimeoutExpired as error:
        def decode_output(value: str | bytes | None) -> str:
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="replace")
            return value or ""

        output = decode_output(error.stdout) + decode_output(error.stderr)
        print(output, end="")
        print("Codex review timed out after 1800 seconds.")
        state = load_state(number)
        state.update({"status": "failed", "updated_at": time.time()})
        save_state(number, state)
        return 124
    print(result.stdout, end="")
    print(result.stderr, end="")
    output = result.stdout + result.stderr
    final_response = output.rsplit("\ncodex\n", 1)[-1]
    review_url = re.search(
        r"https://github\.com/[^\s)]+/pull/\d+#pullrequestreview-\d+",
        final_response,
    )
    if (
        "Review blocked" in final_response
        or "/review` is blocked" in final_response
        or "was blocked by:" in final_response
        or "validated blocked result" in final_response
    ):
        status = "blocked by Argus preflight"
        state_status = "blocked"
    elif result.returncode == 0 and review_url:
        status = "completed"
        state_status = "completed"
    elif result.returncode == 0:
        status = "failed (no published GitHub review receipt)"
        state_status = "failed"
    else:
        status = f"failed (exit {result.returncode})"
        state_status = "failed"
    state = load_state(number)
    state.update({"status": state_status, "updated_at": time.time()})
    save_state(number, state)
    return result.returncode


def run_json(args: list[str]) -> object:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def load_state(number: int) -> dict:
    path = STATE_DIR / f"{number}.json"
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(number: int, state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / f"{number}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def current_head_reviewed(number: int, head_sha: str) -> bool:
    reviews = run_json(
        [GH_BIN, "api", f"repos/{REPO}/pulls/{number}/reviews", "--paginate"]
    )
    return any(
        review.get("user", {}).get("login") == USER
        and review.get("commit_id") == head_sha
        for review in reviews
    )


def load_batch() -> dict:
    try:
        return json.loads(BATCH_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_batch(batch: dict) -> None:
    BATCH_PATH.write_text(json.dumps(batch, indent=2, sort_keys=True) + "\n")


def review_summary(number: int, state: dict) -> str:
    log_path = state.get("log")
    text = Path(log_path).read_text(errors="replace") if log_path else ""
    urls = re.findall(r"https://github\.com/[^\s)]+/pull/\d+#pullrequestreview-\d+", text)
    events = re.findall(r'"event": "(APPROVE|REQUEST_CHANGES|COMMENT)"', text)
    labels = {"APPROVE": "APPROVED", "REQUEST_CHANGES": "CHANGES_REQUESTED", "COMMENT": "COMMENTED"}
    label = labels.get(events[-1], "BLOCKED") if events else "BLOCKED"
    return f"PR #{number}: {label}\n{urls[-1]}" if urls else f"PR #{number}: {label} — no review published"


def publish_batch_summary() -> None:
    batch = load_batch()
    entries = batch.get("entries", [])
    if not entries:
        return
    for entry in entries:
        pid = load_state(int(entry["number"])).get("pid")
        if isinstance(pid, int) and process_alive(pid):
            return
    lines = ["Argus review summary", "", "Published reviews:", ""]
    for entry in entries:
        lines.append(review_summary(int(entry["number"]), load_state(int(entry["number"]))))
        lines.append("")
    subprocess.run(["hermes", "send", "--to", "telegram:1724955702", "--quiet", "\n".join(lines).rstrip()], check=False)
    BATCH_PATH.unlink(missing_ok=True)


def wait_for_batch(entries: list[dict]) -> None:
    while any(
        isinstance(load_state(int(entry["number"])).get("pid"), int)
        and process_alive(load_state(int(entry["number"])).get("pid"))
        for entry in entries
    ):
        time.sleep(5)


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--wait-batch":
        batch = load_batch()
        wait_for_batch(batch.get("entries", []))
        publish_batch_summary()
        return
    if len(sys.argv) == 5 and sys.argv[1] == "--run-review":
        raise SystemExit(run_review(int(sys.argv[2]), sys.argv[3], sys.argv[4]))

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    publish_batch_summary()
    prs = run_json(
        [
            GH_BIN,
            "pr",
            "list",
            "--repo",
            REPO,
            "--state",
            "open",
            "--json",
            "number,url,title,headRefOid,author,isDraft",
        ]
    )
    if not prs:
        return

    dry_run = os.environ.get("ARGUS_REVIEW_DRY_RUN") == "1"
    model = selected_model()
    batch = load_batch()
    entries = batch.get("entries", [])
    for pr in prs:
        if pr.get("author", {}).get("login") == USER:
            continue
        if pr.get("isDraft"):
            continue
        number = int(pr["number"])
        head_sha = pr["headRefOid"]
        state = load_state(number)
        pid = state.get("pid")
        if isinstance(pid, int) and process_alive(pid):
            continue
        if state.get("head_sha") == head_sha and state.get("status") in {
            "already_reviewed",
        }:
            continue
        if current_head_reviewed(number, head_sha):
            save_state(
                number,
                {"head_sha": head_sha, "status": "already_reviewed", "updated_at": time.time()},
            )
            continue

        command = [sys.executable, str(Path(__file__)), "--run-review", str(number), pr["url"], model]
        if dry_run:
            print(f"would launch PR #{number}: {' '.join(command)}")
            continue

        attempt_id = f"{int(time.time())}-{os.getpid()}"
        log_path = LOG_DIR / f"{number}-{head_sha[:12]}-{attempt_id}.log"
        log_file = log_path.open("wb")
        process = subprocess.Popen(
            command,
            cwd=REPO_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log_file.close()
        save_state(
            number,
            {
                "head_sha": head_sha,
                "pid": process.pid,
                "model": model,
                "status": "started",
                "log": str(log_path),
                "updated_at": time.time(),
            },
        )
        entries.append({"number": number, "head_sha": head_sha})
        print(f"launched Argus /review via Codex for PR #{number} (pid {process.pid}); log: {log_path}")
    if entries:
        save_batch({"entries": entries, "created_at": batch.get("created_at", time.time())})
        if not dry_run:
            subprocess.Popen(
                [sys.executable, str(Path(__file__)), "--wait-batch"],
                cwd=REPO_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )


if __name__ == "__main__":
    main()
