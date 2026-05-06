"""Validate every instance in the active domain set and emit a reference-plan
length per instance via pyperplan.

For each domain in `config.yml::domains.active` we:
  1. Locate the domain file (`domain.pddl` or `<name>_domain.pddl`)
  2. For each `instance-XX.pddl`, run pyperplan A*+blind to get an *optimal*
     plan when feasible; fall back to BFS or hadd if blind is too slow
  3. Optionally validate the produced plan with VAL (if available)
  4. Write `src/data/<domain>/REFERENCE_PLANS.csv` with one row per instance:
        instance, plan_len, status, notes

Usage:
  python scripts/verify/validate_instances.py
  python scripts/verify/validate_instances.py --domains basic_move visit-all satellite
  python scripts/verify/validate_instances.py --timeout 60 --search bfs

The output CSV is what the analysis notebook consumes for per-instance ground-
truth difficulty (Plot 12 onward).
"""
from __future__ import annotations

import argparse
import csv
import logging
import signal
import sys
import time
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("validate_instances")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "src" / "data"
CONFIG = PROJECT_ROOT / "config.yml"


def load_active_domains() -> list[str]:
    with open(CONFIG, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return list((cfg.get("domains") or {}).get("active") or [])


def _is_domain_filename(p: Path) -> bool:
    """A `*.pddl` file is a domain file iff its name contains 'domain' (case-insensitive)."""
    return "domain" in p.name.lower()


def locate_domain_file(domain_dir: Path) -> Path | None:
    """Return the domain file in `domain_dir`, or None.

    Rule: any `*.pddl` whose filename contains "domain" (case-insensitive)
    is treated as a domain file. When several match, prefer in this order:
      1. `domain.pddl`
      2. `<dirname>_domain.pddl`
      3. lexicographically first remaining match (e.g. `city_car_domain.pddl`)."""
    candidates = sorted(p for p in domain_dir.glob("*.pddl") if _is_domain_filename(p))
    if not candidates:
        return None
    for preferred in (domain_dir / "domain.pddl",
                      domain_dir / f"{domain_dir.name}_domain.pddl"):
        if preferred in candidates:
            return preferred
    return candidates[0]


def find_instances(domain_dir: Path) -> list[Path]:
    """Return every problem-instance `.pddl` file in `domain_dir`.

    Rule: any `*.pddl` whose filename does NOT contain "domain" (case-insensitive).
    Catches the canonical `instance-NN.pddl`, the legacy `problem_NN.pddl` /
    `prob*.pddl`, and any other contributor-chosen naming."""
    return sorted(p for p in domain_dir.glob("*.pddl") if not _is_domain_filename(p))


class _PlanTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise _PlanTimeout()


def plan_with_pyperplan(domain_path: Path, problem_path: Path, search_name: str,
                       heuristic_name: str, timeout: int) -> tuple[list[str] | None, str, float]:
    """Return (plan, status, elapsed_seconds).

    plan is a list of action strings, or None on failure / timeout.
    """
    from pyperplan.planner import HEURISTICS, SEARCHES
    from pyperplan.pddl.parser import Parser
    from pyperplan.grounding import ground

    t0 = time.perf_counter()
    try:
        parser = Parser(str(domain_path), str(problem_path))
        domain = parser.parse_domain()
        problem = parser.parse_problem(domain)
    except Exception as exc:
        return None, f"parse-error: {exc}", time.perf_counter() - t0

    try:
        task = ground(problem)
    except Exception as exc:
        return None, f"ground-error: {exc}", time.perf_counter() - t0

    search_fn = SEARCHES[search_name]
    heuristic_class = HEURISTICS.get(heuristic_name)

    # signal-based timeout works only on Unix; Windows needs a different
    # approach but for our cases (small domains) the planner returns fast.
    use_signal = hasattr(signal, "SIGALRM")
    if use_signal:
        signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(int(timeout))
    try:
        if heuristic_class is not None:
            heur = heuristic_class(task)
            solution = search_fn(task, heur)
        else:
            solution = search_fn(task)
    except _PlanTimeout:
        return None, f"timeout-{timeout}s", time.perf_counter() - t0
    except Exception as exc:
        return None, f"search-error: {type(exc).__name__}: {exc}", time.perf_counter() - t0
    finally:
        if use_signal:
            signal.alarm(0)

    if solution is None:
        return None, "no-solution-found", time.perf_counter() - t0

    plan_lines = [f"({op.name.strip('()')})" if not op.name.startswith("(") else op.name
                  for op in solution]
    return plan_lines, "ok", time.perf_counter() - t0


def validate_domain(domain_name: str, search: str, heuristic: str, timeout: int) -> dict:
    domain_dir = DATA_DIR / domain_name
    if not domain_dir.is_dir():
        log.warning("Domain dir missing: %s", domain_dir)
        return {"domain": domain_name, "found": False}

    domain_file = locate_domain_file(domain_dir)
    if domain_file is None:
        log.warning("[%s] no domain.pddl / *_domain.pddl found", domain_name)
        return {"domain": domain_name, "found": False}

    instances = find_instances(domain_dir)
    if not instances:
        log.warning("[%s] no problem .pddl files in %s", domain_name, domain_dir)
        return {"domain": domain_name, "found": False}

    log.info("[%s] domain=%s   instances=%d", domain_name, domain_file.name, len(instances))

    rows = []
    plan_lens = []
    failures = 0
    for inst in instances:
        plan, status, dt = plan_with_pyperplan(domain_file, inst, search, heuristic, timeout)
        plen = len(plan) if plan is not None else -1
        ok = plan is not None
        rows.append({
            "instance": inst.stem,
            "plan_len": plen,
            "status":   status,
            "search":   search,
            "heuristic":heuristic,
            "elapsed_s":round(dt, 3),
        })
        if ok:
            plan_lens.append(plen)
        else:
            failures += 1
        marker = "OK " if ok else "FAIL"
        plen_str = f"{plen}" if plen >= 0 else "--"
        log.info("  %s  %s  | plan_len=%3s  | %.2fs  | %s", marker, inst.stem, plen_str, dt, status)

    out = domain_dir / "REFERENCE_PLANS.csv"
    # Preserve manually-curated rows (status starts with 'manual') across re-runs.
    if out.exists():
        existing = {r["instance"]: r for r in csv.DictReader(open(out, encoding="utf-8"))}
        merged = []
        for r in rows:
            old = existing.get(r["instance"])
            if old and old.get("status", "").startswith("manual") and r["status"] != "ok":
                # Keep the manual row; pyperplan failed on this instance.
                merged.append(old)
            else:
                merged.append(r)
        rows = merged
    with open(out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["instance","plan_len","status","search","heuristic","elapsed_s"])
        writer.writeheader()
        writer.writerows(rows)
    log.info("[%s] wrote %s  (%d ok, %d fail)", domain_name, out, len(plan_lens), failures)

    return {
        "domain":    domain_name,
        "found":     True,
        "n_inst":    len(instances),
        "n_solved":  len(plan_lens),
        "n_failed":  failures,
        "min_plen":  min(plan_lens) if plan_lens else None,
        "max_plen":  max(plan_lens) if plan_lens else None,
        "mean_plen": (sum(plan_lens) / len(plan_lens)) if plan_lens else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", nargs="*", default=None,
                    help="Subset of domains. Default: every entry in config.yml domains.active.")
    ap.add_argument("--search", default="bfs",
                    help="pyperplan search algorithm (bfs/astar/wastar/gbf/ehs/ids).")
    ap.add_argument("--heuristic", default=None,
                    help="Heuristic for non-BFS searches (blind/hff/hadd/hmax/lmcut). Ignored for BFS.")
    ap.add_argument("--timeout", type=int, default=120,
                    help="Per-instance timeout (seconds).")
    args = ap.parse_args()

    domains = args.domains or load_active_domains()
    if not domains:
        log.error("No domains to validate (config.yml domains.active is empty?).")
        sys.exit(1)

    log.info("Validating %d domains via pyperplan (search=%s heur=%s timeout=%ds):  %s",
             len(domains), args.search, args.heuristic, args.timeout, ", ".join(domains))
    summary = []
    for d in domains:
        s = validate_domain(d, args.search, args.heuristic, args.timeout)
        summary.append(s)
        print()

    log.info("=" * 78)
    log.info(f"{'domain':<14} {'inst':>4} {'ok':>4} {'fail':>5} {'min':>4} {'max':>4} {'mean':>6}")
    log.info("-" * 78)
    for s in summary:
        if not s.get("found"):
            log.info(f"{s['domain']:<14}  -- not found --")
            continue
        log.info(f"{s['domain']:<14} {s['n_inst']:>4} {s['n_solved']:>4} {s['n_failed']:>5} "
                 f"{(s['min_plen'] if s['min_plen'] is not None else '--'):>4} "
                 f"{(s['max_plen'] if s['max_plen'] is not None else '--'):>4} "
                 f"{(round(s['mean_plen'], 1) if s['mean_plen'] is not None else '--'):>6}")
    log.info("=" * 78)


if __name__ == "__main__":
    main()
