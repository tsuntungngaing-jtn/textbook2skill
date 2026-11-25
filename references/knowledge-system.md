# Knowledge system v0.3.0

## Upstream inspiration and boundaries

- K12-KGraph (https://github.com/haolpku/K12-KGraph): typed educational nodes and evidence.
- ibook-skills (https://github.com/dmccreary/ibook-skills) and PRAT (https://github.com/IntAIEdu/PRAT): prerequisite annotation and DAG quality checks.
- HippoRAG (https://github.com/osu-nlp-group/hipporag) and GraphRAG (https://github.com/microsoft/graphrag): multi-hop retrieval inspiration. Local implementation is bounded traversal and lexical evidence search, not these algorithms.
- PaperQA2 (https://github.com/Future-House/paper-qa), SciFact (https://github.com/allenai/scifact), CoVe (https://aclanthology.org/2024.findings-acl.212/): source retrieval, claim-level support and independent review.
- Pint (https://github.com/hgrecco/pint): optional actual unit conversion dependency.
No upstream source code or restricted data copied. Review licenses before optional integration. External frameworks not connected in this release.

## Graph contract

Keep local graph JSON with four arrays: sources, evidence, nodes, edges. Source IDs must map to actual accessible editions in source-index.json; reconcile source hashes before use. Each source requires id/title/edition/sha256 (64 lowercase hex). Evidence: id/source_id/chapter/locator/status, optional original paraphrase summary and keywords, reviewer and review_log required for reviewed. Locator includes original physical page, printed page, section/table/equation and region when relevant. Mark source review only after actual readback; status is an assertion, not machine-proof. Do not store complete copyrighted pages in a public graph.

Nodes: id/type/title/status/evidence_ids. Types concept, formula, assumption, constraint, rule, procedure, case, evidence, script. Edges: id/from/to/type/scope/status/evidence_ids. Types prerequisite_of (prerequisite -> dependent), derived_from, depends_on, valid_under, applies_to, equivalent_to, contradicts, supported_by, implemented_by, related_to. States candidate, reviewed, blocked. Reviewed edges require reviewed endpoints and reviewed evidence. Candidate prerequisite cycles require adjudication; other relation cycles are permitted. Preserve original terminology and scoped aliases, not automatic name-based entity merges. Check edition, variable meaning, units, material and process conditions before linking. Inferred links remain candidates until separately reviewed.

Commands (from repository root):
- python scripts/knowledge_cli.py validate knowledge-graph.json
- python scripts/knowledge_cli.py search knowledge-graph.json "assembly time"
- python scripts/knowledge_cli.py paths knowledge-graph.json C1 --hops 3

Search uses reviewed summaries/keywords/locators and returns ranked evidence references. Graph traversal uses explicit reviewed seed IDs by default, in both directions, keeping edge direction/type/scope and evidence visible. Traversal is not logical implication: verify all intermediate nodes, edge scopes and evidence at the original source; contradictions are returned, not silently discarded. Revisit critical source regions before using retrieved claims.

## Claim and independent review

Review request JSON: {"claim":{"id":"claim1","author":"chapter-A","scope":"specified conditions"},"reviews":[{"claim_id":"claim1","reviewer":"independent-B","scope":"specified conditions","independent_read":true,"review_log":"local audit locator","evidence_ids":["E1"],"verdict":"SUPPORTED"}]}.
Run python scripts/knowledge_cli.py review graph.json review-request.json. Verification agent initially receives source and neutral question, not proposed answer; freeze independent result before showing the claim. Only then record review. Supported, contradicted, conditionally valid, equivalent, complementary, insufficient evidence are retained. Any accepted contradiction blocks automatic acceptance, regardless of number of supporting reviewers. Different scopes are rejected for same-scope adjudication and must be separately evaluated. Reviewer ID/attestation cannot prove isolation. Multiple sources with shared origin are not independent; document source lineage and avoid vote counting. SUPPORTED_BY_REVIEW is not certification.

For quantitative claims use quantity request: {"first":{"quantity":"stress","scope":"same material/conditions","value":1,"unit":"MPa"},"second":{"quantity":"stress","scope":"same material/conditions","value":1000,"unit":"kPa"},"relative_tolerance":0.000001,"absolute_tolerance":0}. Run python scripts/knowledge_cli.py quantity request.json. Tolerances must come from task/measurement context; absolute tolerance in first quantity's units. Same spelling can be compared directly, unlike units require Pint. Validate unit definitions (including offset units) and quantity semantics separately; dimensional compatibility alone does not imply physical equivalence. Formula equivalence requires independent derivation, declared assumptions, domain and tested numerical cases; no general symbolic solver in this version. A numeric disagreement is a candidate conflict, not proof a book is wrong.

## Decision engine

For reviewed rule nodes embed exact predicate object, e.g. {"node_id":"R1","scope":"declared application","input":"cost","op":"le","threshold":10,"unit":"dimensionless"}. This illustrative threshold is synthetic, not a textbook rule. Supported ops lt/le/eq/ge/gt/ne. A decision request contains scope, rules (array of exact predicate objects), facts (map keyed by input, each with value, unit, scope, origin, reviewed:true). Run python scripts/knowledge_cli.py decide graph.json decision.json.
Every predicate must exactly equal that node's reviewed predicate and scope. Numeric checks are conjunctive hard constraints: FAIL if any failed, UNKNOWN if incomplete, PASS only if every supplied rule passes. Before invocation freeze the complete relevant rule set, exceptions and candidate scope, including unresolved hard constraints; do not omit constraints to achieve PASS. No arbitrary code or eval; nonnumeric rules, exception handling, general formula compilation, costs and Pareto ranking remain authored workflows/scripts. Source/measurement review and actual engineering validation mandatory. Do not execute rules for harmful use.
