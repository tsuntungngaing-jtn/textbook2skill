# Integration with domain agents

Knowledge-pack mode provides reusable files and a human-readable index. Domain-skill mode adds a concise name/description and task workflow in SKILL.md, explicit links to relevant references and scripts, and optionally agents/openai.yaml if supported. Load topic files on demand; don't load the entire book or every rule for every task. A new agent skill does not change model weights.

Integration-patch mode: inspect existing target skill and current revision; map triggers to knowledge modules; preserve existing verification gates and domain constraints; record what files would change, new tests, dependencies, migration and rollback. Do not implicitly change or push the target. For CAD/DFMA: retrieve only applicable decision cards before design; preserve functional interfaces; measure geometry; compare feasible processes with evidence; run deterministic cost or assembly calculations only with actual inputs; require native CAD validation. No CAD runtime success can be inferred from textbook extraction.

Official format references: https://agentskills.io/specification ; https://developers.openai.com/plugins/build/skills ; https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md ; https://developers.openai.com/blog/eval-skills . These are format and evaluation resources, not domain evidence.
