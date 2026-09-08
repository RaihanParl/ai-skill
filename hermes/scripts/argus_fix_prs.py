#!/usr/bin/env python3
"""Run Argus review/fix loops for the user's own reviewed pull requests."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = "rdeepmath91/agent-dev-command-harness"
REPO_DIR = Path("/Users/mraihanparlaungan/personal/argus/agent-dev-command-harness")
USER = "RaihanParl"
SELF_LOGINS = {"RaihanParl", "rdeepmath91"}
GH_BIN = "/Users/mraihanparlaungan/.hermes/scripts/gh-keychain-wrapper"
STATE_DIR = Path.home() / ".hermes" / "scripts" / "state" / "argus-fix-prs"
LOG_DIR = STATE_DIR / "logs"
BATCH_PATH = STATE_DIR / "batch.json"
LOCK_PATH = STATE_DIR / "scheduler.lock"


def gh(*args: str) -> object:
    result = subprocess.run(
        [GH_BIN, *args], cwd=REPO_DIR, capture_output=True, text=True,
        env={**os.environ, "GH_BIN": GH_BIN}, check=True,
    )
    return json.loads(result.stdout)


def pr_metadata(number: int) -> dict:
    return gh("pr", "view", str(number), "--repo", REPO,
              "--json", "number,url,title,state,isDraft,author,headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus,reviewDecision")


def external_review(number: int, head: str) -> dict | None:
    reviews = gh("api", f"repos/{REPO}/pulls/{number}/reviews", "--paginate")
    candidates = [r for r in reviews if r.get("user", {}).get("login") not in SELF_LOGINS
                  and r.get("state") in {"CHANGES_REQUESTED", "COMMENTED", "APPROVED"}]
    return max(candidates, key=lambda r: r.get("submitted_at", ""), default=None)


def eligibility(number: int) -> tuple[bool, dict]:
    pr = pr_metadata(number)
    head = pr["headRefOid"]
    review = external_review(number, head)
    eligible = (pr["state"] == "OPEN" and not pr["isDraft"]
                and pr.get("author", {}).get("login") in SELF_LOGINS and review is not None)
    return eligible, {"pr": pr, "review": review}


def state_path(number: int) -> Path:
    return STATE_DIR / f"{number}.json"


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def worker_prompt(url: str, review_id: str) -> str:
    return f"""Execute this Argus own-PR remediation workflow for {url}.

Use Argus Harness native commands first. Read .commands/review.md and .commands/fix.md as authoritative contracts. This PR is owned by {USER}; external review evidence is review id {review_id}. Address that external review, not self-authored review text.

Workflow:
1. Fetch live PR metadata, exact head, source branch, mergeability, external reviews, and unresolved review threads.
2. If PR conflicts with live main, reconcile main first in the PR source worktree. Prefer a normal merge of main because current /fix delivery policy is non-force. If a true rebase is unavoidable, require exact remote-head lease and preserve all unrelated work; never blind-force push.
3. Run /review at the exact reconciled head, then /fix every active safe finding that is tied to the external review. Preserve questions, unsafe scope, missing evidence, and environment blockers as blockers.
4. Validate each fix and broader repository checks. Commit one bounded change and push only after exact-head, branch, authorization, parent, and non-force delivery checks pass.
5. Comment on the PR with the fix commit, addressed finding IDs, validation summary, and request for the original reviewer to re-review. Do not publish a duplicate review from this workflow.
6. Repeat /review -> /fix -> validate -> push -> reviewer comment until no active findings remain. Never claim clean while a finding or required evidence remains unresolved.

If any harness-native path fails, breaks, hangs, crashes, or blocks: verify the failure; create an issue in this Argus repository using /issue; continue with another native path, otherwise use a spawned subagent. Do not hide blockers.

This invocation explicitly authorizes bounded fixes, one non-force push per successful loop, and a PR comment. Never force-push, merge the PR, close issues, or alter unrelated files. Report exact heads, commits, review URLs, comments, tests, blockers, and final state."""


def run_worker(number: int, url: str, review_id: str, model: str, apply: bool, head: str) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True); LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not apply:
        print(f"would launch fixer for PR #{number}: external review {review_id}")
        return 0
    prompt = worker_prompt(url, review_id)
    log = LOG_DIR / f"{number}-{int(time.time())}.log"
    with log.open("w", encoding="utf-8") as handle:
        try:
            result = subprocess.run(
                ["codex", "exec", "--sandbox", "danger-full-access", "--model", model, prompt],
                cwd=REPO_DIR, stdin=subprocess.DEVNULL, stdout=handle, stderr=subprocess.STDOUT,
                env={**os.environ, "GH_BIN": GH_BIN}, timeout=3600,
            )
            handle.flush()
            text = log.read_text(encoding="utf-8", errors="replace")
            status = "blocked" if "remediation is blocked" in text or "Blocker " in text else ("completed" if result.returncode == 0 else f"failed:{result.returncode}")
        except subprocess.TimeoutExpired:
            status = "failed:timeout"
    state = {"number": number, "head": head, "review_id": review_id,
             "status": status, "log": str(log), "updated_at": time.time()}
    state_path(number).write_text(json.dumps(state, indent=2) + "\n")
    summary = log.read_text(encoding="utf-8", errors="replace")[-12000:]
    subprocess.run(
        ["hermes", "send", "--to", "telegram:1724955702", "--quiet",
         f"Argus own-PR fixer — PR #{number} — {status}\n\n{summary}"],
        check=False,
    )
    print(f"PR #{number}: {status}; log: {log}")
    return 0 if status == "completed" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", type=int, action="append", help="PR number; repeat for parallel workers")
    parser.add_argument("--url")
    parser.add_argument("--apply", action="store_true", help="allow bounded fix/push/comment workflow")
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--run-worker", nargs=5, metavar=("NUMBER", "URL", "REVIEW_ID", "MODEL", "HEAD"))
    args = parser.parse_args()
    if args.run_worker:
        number, url, review_id, model, head = args.run_worker
        return run_worker(int(number), url, review_id, model, args.apply, head)
    if args.url and args.pr:
        parser.error("use --pr or --url, not both")
    numbers = args.pr or []
    if args.url:
        match = re.search(r"/pull/(\d+)", args.url)
        if not match:
            parser.error("invalid GitHub PR URL")
        numbers = [int(match.group(1))]
    if not numbers:
        prs = gh("pr", "list", "--repo", REPO, "--state", "open", "--json", "number")
        numbers = [int(p["number"]) for p in prs]
    jobs = []
    for number in numbers:
        eligible, evidence = eligibility(number)
        pr = evidence["pr"]
        review = evidence["review"]
        if not eligible:
            print(f"PR #{number}: skipped (not own open non-draft PR with external review)")
            continue
        print(f"PR #{number}: eligible; head {pr['headRefOid']}; review {review['id']} by {review['user']['login']}; merge={pr.get('mergeable')}")
        jobs.append((number, pr["url"], review["id"], pr["headRefOid"]))
    if not jobs:
        return 0
    if not args.apply:
        for number, _, review_id, _ in jobs:
            print(f"would launch fixer for PR #{number}: external review {review_id}")
        return 0
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("fixer scheduler already running")
            return 0
        for number, url, review_id, head in jobs:
            previous = {}
            try:
                previous = json.loads(state_path(number).read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            pid = previous.get("pid")
            if isinstance(pid, int) and process_alive(pid):
                continue
            if (previous.get("head") == head and previous.get("review_id") == review_id
                    and previous.get("status") in {"completed", "blocked", "failed:timeout"}):
                continue
            log = LOG_DIR / f"{number}-{head[:12]}-{int(time.time())}.log"
            command = [sys.executable, str(Path(__file__)), "--run-worker", str(number), url,
                       str(review_id), args.model, head, "--apply"]
            log_file = log.open("w", encoding="utf-8")
            process = subprocess.Popen(command, cwd=REPO_DIR, stdout=log_file,
                                       stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                       start_new_session=True, env={**os.environ, "GH_BIN": GH_BIN})
            log_file.close()
            state_path(number).write_text(json.dumps({"number": number, "head": head,
                "review_id": review_id, "pid": process.pid, "status": "started",
                "log": str(log), "updated_at": time.time()}, indent=2) + "\n")
            print(f"launched fixer for PR #{number} (pid {process.pid}); log: {log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
