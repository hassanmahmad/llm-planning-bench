# report/

LaTeX source for the project report. Day 1 contains only the
Methodology section plus the prompt appendix; other sections fill in
on Days 2-4.

## Files

| File | Source of truth for | Filled on |
|------|---------------------|-----------|
| `main.tex` | document skeleton, packages, section order | Day 1 |
| `methodology.tex` | Methodology (pipeline, prompts, config, iteration, validator, verification) | Day 1 |
| `appendix_prompts.tex` | Appendix A — 12 reference prompts (6 domains × 2 conditions) via `\lstinputlisting` of `../src/tests/fixtures/prompts/*.txt` | Day 1 |
| *(future)* `context.tex`, `experimental_design.tex`, `results.tex`, `discussion.tex`, `limitations.tex`, `conclusions.tex` | rest of the report | Days 2-4 |

## Build

```bash
cd report/
latexmk -pdf main.tex
```

## Refreshing the prompt appendix

The appendix inputs the fixtures under `../src/tests/fixtures/prompts/`
directly via `\lstinputlisting`, so the PDF is always in sync with the
on-disk fixtures. If the prompt composer changes, rerun:

```bash
python scripts/verify/dump_prompts.py --instance instance-01
```

from the project root to regenerate the fixtures and re-verify the
uniformity asserts before rebuilding the PDF.
