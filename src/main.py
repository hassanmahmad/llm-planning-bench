#!/usr/bin/env python3
"""CLI entry point for the PDDL Planning Framework."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict

from core.pddl_planner import PDDLPlanner
from utils.configuration import load_config
from utils.logging_utils import configure_logging, get_logger


def _build_parser(config: Dict) -> argparse.ArgumentParser:
    """Create the CLI parser with defaults pulled from config.yml."""
    domains_cfg = config.get("domains") or {}
    domain_choices = domains_cfg.get("available") or domains_cfg.get("active") or []
    model_choices = (config.get("models") or {}).get("active") or []
    # stub is always available; 'auto' defers to weights_path basename detection
    model_choices = sorted(set(list(model_choices) + ["stub", "auto"]))
    condition_choices = config.get("conditions") or ["baseline", "cot"]

    generation = config.get("generation") or {}
    iteration = config.get("iteration") or {}

    parser = argparse.ArgumentParser(
        description="PDDL Planning with Large Language Models",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--problems_path",
        default=config.get("PROBLEMS_PATH", "src/data"),
        help="Directory containing PDDL domains and problems",
    )
    parser.add_argument(
        "--weights_path",
        default=config.get("MODEL_PATH", "src/models"),
        help="Directory with model weights (ignored for --model stub)",
    )
    parser.add_argument(
        "--output_dir",
        default=config.get("MODEL_OUTPUT", "src/results"),
        help="Destination directory for generated plans",
    )

    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all discovered domains in batch mode",
    )
    parser.add_argument(
        "--domain",
        type=str,
        choices=domain_choices or None,
        help="Process only the specified domain name",
    )
    parser.add_argument(
        "--instance",
        type=str,
        default=None,
        help="Restrict to a single problem (filename stem, e.g. instance-01)",
    )
    parser.add_argument(
        "--condition",
        choices=condition_choices,
        default="baseline",
        help="Prompting condition: 'baseline' or 'cot'",
    )
    parser.add_argument(
        "--iterations",
        "--max_iterations",
        dest="max_iterations",
        type=int,
        default=iteration.get("max_iterations", config.get("DEFAULT_ITERATIONS", 4)),
        help="Maximum validation iterations per problem (stop_on_success)",
    )

    parser.add_argument(
        "--sampling",
        action="store_true",
        help="Enable sampling (temperature / top-k) instead of greedy decoding",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=generation.get("temperature", config.get("TEMPERATURE", 0.6)),
        help="Sampling temperature",
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=generation.get("top_k", config.get("TOP_K", 10)),
        help="Top-k for sampling",
    )
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=generation.get("max_new_tokens", config.get("MAX_TOKENS", 4096)),
        help="Maximum tokens to generate per response",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=generation.get("seed", config.get("SEED", 42)),
        help="Random seed for torch/numpy/python — applied globally before generation",
    )

    boolean_action = argparse.BooleanOptionalAction
    parser.add_argument(
        "--add_system_prompt",
        action=boolean_action,
        default=True,
        help="Include the system prompt when talking to the model",
    )
    parser.add_argument(
        "--include_prompt",
        action=boolean_action,
        default=True,
        help="Persist the prompt alongside the model output",
    )
    parser.add_argument(
        "--skip_special_tokens",
        action=boolean_action,
        default=True,
        help="Strip tokenizer special tokens from the output",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable additional debug logging",
    )

    parser.add_argument(
        "--model",
        choices=model_choices,
        default="auto",
        help="Model alias (from config.yml models.active) or 'stub' / 'auto'",
    )
    parser.add_argument(
        "--cluster",
        choices=["local", "leonardo"],
        default="local",
        help="Execution target — 'local' activates Project B's local overrides",
    )
    parser.add_argument(
        "--log-level",
        default=config.get("LOG_LEVEL", "INFO"),
        help="Root logging level",
    )
    parser.add_argument(
        "--log-file",
        default=config.get("LOG_FILE"),
        help="Optional path to also write logs",
    )

    return parser


def main():
    """Main function to run the PDDL planning pipeline."""

    try:
        config = load_config()
    except Exception as exc:  # pragma: no cover - fatal configuration
        print(f"Failed to load config.yml: {exc}", file=sys.stderr)
        sys.exit(1)

    parser = _build_parser(config)
    args = parser.parse_args()

    configure_logging(level=args.log_level, log_file=args.log_file)
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger = get_logger(__name__)
    logger.info("Starting PDDL Planning Framework")

    _set_global_seed(args.seed)
    logger.info("Random seed set to %d", args.seed)

    args.output_dir = _resolve_output_dir(args)
    _validate_paths(args.problems_path, args.weights_path, logger)

    logger.debug("CLI arguments: %s", vars(args))

    try:
        planner = PDDLPlanner(args, config)
        planner.setup()
        planner.run()
        logger.info("PDDL Planning Framework completed successfully")
    except KeyboardInterrupt:
        logger.warning("Execution interrupted by user")
        sys.exit(1)
    except Exception:
        logger.exception("Fatal error during planning run")
        sys.exit(1)


def _set_global_seed(seed: int) -> None:
    """Seed torch / numpy / python globally so sampling is reproducible."""
    import random
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _validate_paths(problems_path: str, weights_path: str, logger: logging.Logger) -> None:
    """Ensure the provided directories exist before running the planner."""
    if not Path(problems_path).exists():
        logger.error("Problems path does not exist: %s", problems_path)
        sys.exit(1)
    # weights_path may be a local directory OR a HuggingFace repo ID
    # (e.g. "meta-llama/Llama-3.1-8B-Instruct"). HF repo IDs always contain
    # a "/" but never start with "./" or "/" and never exist on disk.
    is_hf_repo = "/" in weights_path and not Path(weights_path).exists()
    if not is_hf_repo and not Path(weights_path).exists():
        logger.error("Model weights path does not exist: %s", weights_path)
        sys.exit(1)


def _resolve_output_dir(args: argparse.Namespace) -> str:
    """Build src/results/{model}/ — {domain}/{condition} are appended by the processor."""
    output_dir = Path(args.output_dir)

    if args.model and args.model.lower() != "auto":
        model_alias = args.model.lower()
    else:
        model_alias = Path(args.weights_path).name.lower()

    if model_alias:
        output_dir = output_dir / model_alias

    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError:
        pass

    return str(output_dir)


if __name__ == "__main__":
    main()