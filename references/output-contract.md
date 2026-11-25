# Output contract v1

New output directory, default knowledge pack:
- `source-index.json`: object {sources: [{id,title,edition,locator,sha256,access,rights}]} (sha256 null if bytes unavailable).
- `coverage.json`: object {sections: [{source_id,locator,status,notes}]} status in pending, parsed, reviewed, partial, blocked, out_of_scope.
- `concepts.jsonl`, `rules.jsonl`, `formula-index.jsonl`: one JSON object per line, empty if no items. Base fields: id, title, evidence (array of {source_id,locator}), support (source/derived/inference/external), status (candidate/verified/blocked), content (object).
- Rules content: trigger, required_inputs, predicate, action, exceptions, unknown_behavior, validation (each non-empty; exceptions may be []).
- Formula content: expression, variables, assumptions, domain, validation (assumptions may be []).
- `workflows.md`, `integration.md`, `validation-report.md`: original authored documents, actual limitations, no fabricated verification. Empty categories explicitly explained.
- Optional `scripts/`, `evals/`: tested calculation helpers and independent evaluation design, distinguish examples and held-out cases. Domain-skill mode additionally generates `SKILL.md` and places supporting resources in references/scripts as appropriate, preserving the pack and locators. Integration-patch mode adds a reviewable patch with target path and version.

Starter skeleton: `python scripts/init_pack.py <new-directory>`. Edit structured files using real sources. Structural validation: `python scripts/validate_pack.py <directory>`. PASS only confirms field/ID/locator format and source ID consistency, not factual correctness.

For a public repository deliver only original rule descriptions, lawful metadata, formulas/independent implementations where permitted, and redistributable data. Keep raw books, extracted full text, OCR, protected tables and images outside the repository. Maintain explicit rights and source access status.

Optional local PDF sidecar v0.2.0: manifest.json, native pages.json and PNGs, or semantic document.json and element crops/Markdown. Bind to source SHA-256 and 1-based physical page locators. Public knowledge pack contains only lawful original summaries, provenance and review status, not raw pages or complete extracts. Existing pack schema unchanged.

## Optional knowledge-system sidecars (v0.3.0)
For graph-enabled packs deliver `knowledge-graph.json`, claim/review records, decision requests/results, task plan/state (private if sensitive), and ablation plans/results when actually executed. Follow knowledge-system.md and collaborative-learning.md. Existing source-index and JSONL files remain primary pack inputs; graph source IDs and hashes must be reconciled to them. Do not call a structural graph pass semantic verification. Use only original paraphrases and lawful locators in public packs.
