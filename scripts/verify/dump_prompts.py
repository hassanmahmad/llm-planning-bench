#!/usr/bin/env python3
"""Prompt-uniformity verification for STEPS.md §1.6.

For each (model × domain × condition):
  - build the full prompt string via prompts.compose.build_problem_prompt
  - dump it to _tmp/prompts/{model}/{domain}_{condition}.txt
  - hash it (SHA-256)

Then assert:
  (A) cross-model byte-identity per (domain, condition)
  (B) baseline vs cot differ ONLY in the CoT scaffold preamble block
      (everything outside the scaffold is byte-identical)

On success, copy one reference per (domain, condition) into
src/tests/fixtures/prompts/ — that's the evidence artifact the
methodology section cites.

Usage (from the project root):
  python scripts/verify/dump_prompts.py --instance instance-01
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parents[2]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from prompts.compose import build_problem_prompt  # noqa: E402
from prompts.shell import COT_SCAFFOLD            # noqa: E402

MODELS = ["llama8", "qwen25", "llama33"]
DOMAINS = ["blocksworld", "citycar", "tetris"]
CONDITIONS = ["baseline", "cot"]

DOMAIN_FILES = {
    "blocksworld": "blocksworld_domain.pddl",
    "citycar":     "city_car_domain.pddl",
    "tetris":      "tetris_domain.pddl",
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _scaffold_preamble(description: str, problem: str) -> str:
    """The exact slice that CoT prepends to the baseline body."""
    full = COT_SCAFFOLD(description, problem)
    assert full.endswith(description), (
        "COT_SCAFFOLD no longer ends with the verbatim description — "
        "update this helper to match shell.py."
    )
    return full[: -len(description)]


def _assert_cot_scaffold_only(baseline: str, cot: str, preamble: str) -> None:
    """Confirm cot == baseline with `preamble` inserted at the description boundary.

    The only allowed difference between the two prompts is the scaffold block.
    Any other drift means compose.py leaked a branch we didn't expect.
    """
    if preamble not in cot:
        raise AssertionError(
            "CoT prompt does not contain the scaffold preamble verbatim — "
            "compose.py and shell.py have drifted."
        )
    reconstructed = cot.replace(preamble, "", 1)
    if reconstructed != baseline:
        raise AssertionError(
            "CoT − scaffold ≠ baseline. The two conditions differ outside "
            "the CoT block (would break the prompt-uniformity claim)."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--instance",
        default="instance-01",
        help="Instance stem to build prompts for (default: instance-01)",
    )
    parser.add_argument(
        "--data-root",
        default=str(SRC_DIR / "data"),
        help="Root of the PDDL data tree",
    )
    parser.add_argument(
        "--dump-dir",
        default=str(PROJECT_ROOT / "_tmp" / "prompts"),
        help="Where per-model dumps go (scratch)",
    )
    parser.add_argument(
        "--fixtures-dir",
        default=str(SRC_DIR / "tests" / "fixtures" / "prompts"),
        help="Where the 6 reference prompts are saved on success",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Run the asserts but do not (over)write fixtures",
    )
    args = parser.parse_args()

    data_root = Path(args.data_root)
    dump_dir = Path(args.dump_dir)
    fixtures_dir = Path(args.fixtures_dir)
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    print(f"instance       = {args.instance}")
    print(f"data root      = {data_root}")
    print(f"dump dir       = {dump_dir}")
    print(f"fixtures dir   = {fixtures_dir}")
    print()

    prompts: dict[tuple[str, str, str], str] = {}
    failures = 0

    for domain in DOMAINS:
        domain_dir = data_root / domain
        dom_pddl = domain_dir / DOMAIN_FILES[domain]
        prob_pddl = domain_dir / f"{args.instance}.pddl"
        if not dom_pddl.exists() or not prob_pddl.exists():
            print(f"  MISSING inputs for {domain}: {dom_pddl} / {prob_pddl}")
            failures += 1
            continue
        pddl_domain = _read(dom_pddl)
        pddl_problem = _read(prob_pddl)

        for condition in CONDITIONS:
            prompt = build_problem_prompt(
                domain=domain,
                condition=condition,
                pddl_domain=pddl_domain,
                pddl_problem=pddl_problem,
            )
            for model in MODELS:
                prompts[(model, domain, condition)] = prompt
                out_path = dump_dir / model / f"{domain}_{condition}.txt"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(prompt, encoding="utf-8")

    # -------- (A) cross-model byte-identity --------
    print("Cross-model identity check:")
    for domain in DOMAINS:
        for condition in CONDITIONS:
            hashes = {
                model: _sha(prompts[(model, domain, condition)])
                for model in MODELS
                if (model, domain, condition) in prompts
            }
            unique = set(hashes.values())
            tag = f"{domain}/{condition}"
            if len(unique) == 1:
                print(f"  ok   {tag:28s} sha256={next(iter(unique))[:12]}")
            else:
                print(f"  FAIL {tag:28s} hashes={hashes}")
                failures += 1

    # -------- (B) baseline vs cot differs only in the scaffold --------
    print()
    print("Baseline-vs-CoT scaffold-only check:")
    from prompts.descriptions import DOMAIN_DESCRIPTIONS
    for domain in DOMAINS:
        key = (MODELS[0], domain, "baseline")
        if key not in prompts:
            continue
        baseline = prompts[key]
        cot = prompts[(MODELS[0], domain, "cot")]
        description = DOMAIN_DESCRIPTIONS[domain]
        problem_pddl = _read(data_root / domain / f"{args.instance}.pddl")
        preamble = _scaffold_preamble(description, problem_pddl)
        try:
            _assert_cot_scaffold_only(baseline, cot, preamble)
            print(f"  ok   {domain:28s} diff is CoT-scaffold-only ({len(preamble)} chars)")
        except AssertionError as err:
            print(f"  FAIL {domain:28s} {err}")
            failures += 1

    if failures:
        print()
        print(f"FAILED: {failures} check(s) did not pass — fixtures not written.")
        return 1

    # -------- write fixtures --------
    print()
    if args.no_write:
        print("--no-write set: skipping fixtures write.")
        return 0

    print(f"Writing 6 reference fixtures to {fixtures_dir}")
    for domain in DOMAINS:
        for condition in CONDITIONS:
            src = dump_dir / MODELS[0] / f"{domain}_{condition}.txt"
            dst = fixtures_dir / f"{domain}_{condition}.txt"
            shutil.copyfile(src, dst)
            print(f"  {dst.relative_to(PROJECT_ROOT)}")

    print()
    print("Prompt uniformity: PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
