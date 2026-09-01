# Conventions for AI sessions in this repo

## Scope

This repo produces RDF deliverables from published CDISC COSMoS, plus an
authored overlay for qualified biomedical concepts. The pipeline is notebooks.
There is no application code, no service, no API. Resist scope creep — if a task
starts to look like "let's also do X", flag it before implementing.

At P0 there are no deliverables at all. Do not write documentation, baselines or
README claims for artifacts that do not exist.

## Layering — the rule that decides where something goes

**Core** is a mechanical rendering of *published* COSMoS. **Overlay** is authored
content. The test: did CDISC publish this, or did this repo decide it?
Disambiguating colliding slot names, minting predicate IRIs, choosing a variable
order rule — all authored, however mechanical they look. Where an authored choice
is unavoidable inside the core rendering, name it in `docs/decisions.md` and
record it in the deliverable's provenance. Never let it pass as published.

## Source pinning

- The upstream commit SHA is pinned in the first code cell of
  `notebooks/10_fetch_cosmos.ipynb`. Bumping it is a deliberate action.
- One SHA co-pins all four inputs — two CSV exports and two LinkML models.
  A bump refreshes them in lockstep.
- `cdisc-org/COSMoS` publishes no tags and no releases, and the schemas declare
  no `version:`. The SHA is the only version handle. Never resolve `latest` at
  build time: `cdisc-org.github.io/COSMoS/export/…` is the current publication
  and is not pinnable.
- **Never fetch from the CDISC Library API.** It is member-gated (auth test,
  2026-08-05: valid key, 401 "Members-only content"). A gated dependency breaks
  the reproducibility claim this repo rests on.
- Every input gets its own `.fetch_meta_*.json` sidecar: source URL, commit SHA,
  SHA-256, size, retrieval timestamp, and for the exports the derived package
  date.

## Self-containment

This repo must rebuild from its own pinned inputs with no dependency on
`cdisc-for-ai` or any other repo. Do not read a file from another repo at build
time and do not copy a downloaded artifact across. Citing another repo's
*written analysis* in prose is fine; depending on its *files* is not.

## Code style

- Python 3 + Pandas where useful. `pyyaml` for YAML, `rdflib` for validation,
  LinkML generators where they do the job.
- 4-space indentation. No exceptions.
- Complete, copy-paste-ready code. No `# fill this in` placeholders, no `...`.
- Fail-fast. No defensive try/except around things that should never fail. No
  silent auto-fixes that mask bad source data.
- No emojis in code, comments, or generated files unless explicitly asked.

## Code modification

- When asked to fix one thing, fix only that thing.
- Show a unified diff before editing — wait for approval before applying.
- Never "improve", "simplify", or "clean up" code that was not part of the
  request.
- Never remove code that looks redundant — there may be reasons not visible in
  the diff.
- Surgical precision. Bytes outside the requested change must be identical.

## Data integrity

- Never fabricate, simulate, or generate example data.
- Never invent C-codes, definitions, preferred terms, class names, or counts.
  The pinned CSV exports are the only source of truth for instances; the pinned
  LinkML models are the only source of truth for structure.
- Everything derived, nothing asserted. What is not derivable from a pinned
  source is marked `[VERIFY]`, not guessed.
- No LOINC or NCIt claim that has not been verified against the service or the
  package.
- If real data is unavailable, state clearly and stop. Do not fall back to
  plausible-looking placeholders.
- Reports and notebooks state their rules and coverage, so agreement is read as
  validation of the rules, not of the corpus.

## Notebook generation

- Generate `.ipynb` files via Python's `json` module. Never write JSON text
  directly.
- Build the notebook as a Python dict. Use helper functions `markdown_cell()`
  and `code_cell()`.
- Each cell's `source` field must be a list of strings, each ending with `\n`.
- Write with `json.dump(notebook, file, indent=1, ensure_ascii=False)`.
- Preserve `kernelspec` / `language_info` across any programmatic execution —
  stash and restore. The local kernel is Python 3.12.6.
- After generation, verify the notebook opens in Jupyter immediately.

## Git

Git operations are the user's to run. Describe the commit; do not execute it.
