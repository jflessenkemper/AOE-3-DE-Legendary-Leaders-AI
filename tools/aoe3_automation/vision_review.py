"""Reviewer-driven vision-check workflow for the matrix.

Instead of calling the Anthropic API mid-matrix, the runner emits a
``vision_review_request.json`` next to each civ's screenshots. A reviewer
(typically Claude reading images via the Read tool) then:

  1. Lists pending reviews     — ``vision_review.py list``
  2. Opens each scene PNG      — Read tool / image viewer
  3. Writes verdicts to disk   — ``vision_review.py verdict <art_dir> ...``
                                 OR drop a ``vision_verdicts.json`` directly.

Verdict file shape (one per civ, sibling of the screenshots)::

    {
      "loading":    {"pass": true,  "reason": "...", "issues": []},
      "in_game":    {"pass": true,  "reason": "...", "issues": []},
      "scoreboard": {"pass": false, "reason": "...", "issues": ["..."]}
    }

The matrix_validator's ``vision_check`` axis passes for a civ iff every
scene present in the verdicts file has ``pass: true``. Missing verdicts
file = axis red until a review happens.

Why the file-based pattern over an inline API call:
  * No API key / network dep — the matrix runs fully offline.
  * Claude-in-the-loop reviewers see the *actual frames* in the same
    context that ran the matrix, with full per-civ doctrine context.
  * Verdicts are auditable artifacts — a reviewer's call gets archived
    next to the screenshot it judged, not lost in a model API response.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARTIFACT_DIR = HERE / "artifacts" / "matrix_runner"


def _iter_civ_dirs(root: Path) -> list[Path]:
    """Every per-civ artifact dir holds a ``vision_review_request.json``
    that the runner wrote at end-of-civ. Sort numerically so the list
    follows the matrix order."""
    if not root.exists():
        return []
    out: list[Path] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "vision_review_request.json").exists():
            out.append(child)
    return out


def cmd_list(args: argparse.Namespace) -> int:
    """Show every civ that has a review request pending. Per-civ output:
    civ name + idx + screenshot paths + doctrine summary + verdict status."""
    root = Path(args.root) if args.root else ARTIFACT_DIR
    dirs = _iter_civ_dirs(root)
    if not dirs:
        print(f"no review requests found under {root}", file=sys.stderr)
        return 1
    pending = 0
    done = 0
    for d in dirs:
        req = json.loads((d / "vision_review_request.json").read_text())
        verdicts_path = d / "vision_verdicts.json"
        verdicts: dict = {}
        if verdicts_path.exists():
            try:
                verdicts = json.loads(verdicts_path.read_text())
            except json.JSONDecodeError:
                verdicts = {}
        scene_names = [s["scene"] for s in req.get("scenes", [])]
        judged = [s for s in scene_names if s in verdicts and "pass" in verdicts[s]]
        all_done = scene_names and len(judged) == len(scene_names)
        status = "DONE" if all_done else f"PENDING {len(judged)}/{len(scene_names)}"
        if all_done:
            done += 1
        else:
            pending += 1
        if args.pending_only and all_done:
            continue
        print(f"=== [{status}] civ_idx={req['civ_idx']:02d} {req['civ_name']} ===")
        print(f"  artifact_dir: {d}")
        print(f"  doctrine:     {req['doctrine_summary']}")
        print(f"  batch civs:   {', '.join(req['batch_civs'])}")
        for s in req.get("scenes", []):
            v = verdicts.get(s["scene"])
            mark = ("✅" if v and v.get("pass") else
                    "❌" if v else "⏳")
            print(f"    {mark} {s['scene']:<11s} {s['path']}")
            if v and v.get("reason"):
                print(f"        reason: {v['reason']}")
        print()
    print(f"Summary: {pending} pending, {done} done, {len(dirs)} total")
    return 0


def cmd_verdict(args: argparse.Namespace) -> int:
    """Write or update a verdict for a single (civ_dir, scene). Useful for
    ad-hoc fixes; the bulk-review path is to write the JSON file directly."""
    art = Path(args.art_dir).resolve()
    if not art.exists():
        print(f"art_dir not found: {art}", file=sys.stderr)
        return 2
    verdicts_path = art / "vision_verdicts.json"
    verdicts: dict = {}
    if verdicts_path.exists():
        try:
            verdicts = json.loads(verdicts_path.read_text())
        except json.JSONDecodeError:
            verdicts = {}
    verdicts[args.scene] = {
        "pass": args.passed,
        "reason": args.reason or "",
        "issues": args.issue or [],
    }
    verdicts_path.write_text(json.dumps(verdicts, indent=2))
    print(f"wrote {verdicts_path} ({args.scene}: pass={args.passed})")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    """Block until a new pending civ appears under the artifact root, then
    print its review request and exit. Designed for concurrent-review use:
    the matrix runs in the background, the reviewer loops on
    ``vision_review.py watch`` to pick up each batch's review request the
    moment it lands on disk.

    Behaviour:
      * Starts by snapshotting which civs already have request files.
      * Polls every ``--interval`` seconds (default 5) for a new request file.
      * On first new arrival (still pending — not yet judged), prints the
        full review request the same way ``list`` does for that one civ.
      * Exits 0 on a found new pending review.
      * Exits 1 if ``--timeout`` seconds pass without a new pending review.
      * Exits 2 if the artifact root never appears.

    Pair with the matrix run for an interleaved flow::

        # terminal A
        python3 tools/aoe3_automation/matrix_runner.py --deep &

        # terminal B (review loop — wakes once per civ artifact)
        while python3 tools/aoe3_automation/vision_review.py watch; do
          # reviewer reviews; writes vision_verdicts.json
          true
        done
    """
    import time as _time
    root = Path(args.root) if args.root else ARTIFACT_DIR
    deadline = _time.monotonic() + args.timeout if args.timeout > 0 else None
    # Snapshot already-present (any state) civ dirs so we only fire on truly
    # new arrivals; the reviewer can call ``list`` separately to triage
    # existing backlog.
    seen: set[Path] = set(_iter_civ_dirs(root)) if root.exists() else set()
    while True:
        if not root.exists():
            if deadline and _time.monotonic() > deadline:
                print(f"timeout: {root} never appeared", file=sys.stderr)
                return 2
            _time.sleep(args.interval)
            continue
        for d in _iter_civ_dirs(root):
            if d in seen:
                continue
            # New arrival — check if it's actually pending (no verdicts yet).
            verdicts_path = d / "vision_verdicts.json"
            if verdicts_path.exists():
                seen.add(d)
                continue
            req = json.loads((d / "vision_review_request.json").read_text())
            print(f"=== NEW PENDING: civ_idx={req['civ_idx']:02d} "
                  f"{req['civ_name']} ===")
            print(f"  artifact_dir: {d}")
            print(f"  doctrine:     {req['doctrine_summary']}")
            print(f"  batch civs:   {', '.join(req['batch_civs'])}")
            for s in req.get("scenes", []):
                print(f"    {s['scene']:<11s} {s['path']}")
            return 0
        if deadline and _time.monotonic() > deadline:
            print(f"timeout: no new pending review in "
                  f"{args.timeout}s under {root}", file=sys.stderr)
            return 1
        _time.sleep(args.interval)


def cmd_summary(args: argparse.Namespace) -> int:
    """One-line per civ summary, suitable for piping into reports."""
    root = Path(args.root) if args.root else ARTIFACT_DIR
    dirs = _iter_civ_dirs(root)
    if not dirs:
        return 1
    for d in dirs:
        req = json.loads((d / "vision_review_request.json").read_text())
        verdicts_path = d / "vision_verdicts.json"
        verdicts: dict = {}
        if verdicts_path.exists():
            try:
                verdicts = json.loads(verdicts_path.read_text())
            except json.JSONDecodeError:
                verdicts = {}
        scene_names = [s["scene"] for s in req.get("scenes", [])]
        passes = sum(1 for s in scene_names
                     if verdicts.get(s, {}).get("pass") is True)
        fails = sum(1 for s in scene_names
                    if verdicts.get(s, {}).get("pass") is False)
        pending = len(scene_names) - passes - fails
        print(f"civ_idx={req['civ_idx']:02d} {req['civ_name']:<24s}  "
              f"pass={passes} fail={fails} pending={pending}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List every civ's pending review.")
    p_list.add_argument("--root", help="Override artifact root.")
    p_list.add_argument("--pending-only", action="store_true",
                        help="Suppress already-judged civs from the listing.")
    p_list.set_defaults(func=cmd_list)

    p_v = sub.add_parser("verdict", help="Write a single scene verdict.")
    p_v.add_argument("art_dir", help="Civ artifact dir.")
    p_v.add_argument("scene", choices=["loading", "in_game", "scoreboard"])
    p_v.add_argument("--pass", dest="passed", action="store_true",
                     help="Mark this scene as passing.")
    p_v.add_argument("--fail", dest="passed", action="store_false",
                     help="Mark this scene as failing.")
    p_v.add_argument("--reason", default="", help="Short rationale.")
    p_v.add_argument("--issue", action="append", default=[],
                     help="Add an issue line (repeatable).")
    p_v.set_defaults(func=cmd_verdict, passed=True)

    p_s = sub.add_parser("summary", help="One-line per-civ summary.")
    p_s.add_argument("--root", help="Override artifact root.")
    p_s.set_defaults(func=cmd_summary)

    p_w = sub.add_parser("watch",
                         help="Block until a new pending civ review appears.")
    p_w.add_argument("--root", help="Override artifact root.")
    p_w.add_argument("--interval", type=float, default=5.0,
                     help="Poll interval in seconds (default 5).")
    p_w.add_argument("--timeout", type=float, default=0,
                     help="Timeout in seconds; 0 = wait forever.")
    p_w.set_defaults(func=cmd_watch)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
