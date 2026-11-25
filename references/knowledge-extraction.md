# Knowledge extraction

Classify each item by purpose:
- Concept: terminology, meaning, variables, relationships, misconceptions, examples (original).
- Rule: trigger, required inputs, predicate, action, exceptions, priority/constraints, unknown behavior, verification.
- Formula: symbolic equation, named variables, units, assumptions, domain, singularities, numeric validation cases, script reference if implemented.
- Workflow: ordered decisions, branches, required observations, outputs, failure recovery.
- Empirical data: provenance, sample/population, units, conditions, uncertainty, rights. Do not redistribute protected tables or synthesize absent values.
- Visual knowledge: describe relevant geometric relationships in original words, with figure pointers. Do not turn a schematic into precise dimensions without stated evidence.

Every card has unique id, title, evidence, support, status and explanatory content. Evidence is a list of source_id and concrete locator, plus optional figure/table/equation identifier. Support: source, derived, inference, external. Status: candidate, verified, blocked. Verified means evidence inspected and semantics checked, not real-world certification. Derived items must show derivation and underlying evidence. Inference stays candidate unless verified separately; never attribute inference to the source.

De-duplicate by concept and applicable scope, not merely title. Keep competing rules separate if their contexts differ. Use stable IDs; record superseded versions rather than overwriting evidence history. A rule card should never imply that all factors have equal weight or that a missing constraint passed.
