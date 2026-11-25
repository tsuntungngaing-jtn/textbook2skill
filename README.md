# Textbook-to-Skill v0.3.0

A reusable agent workflow for transforming accessible textbooks into original, evidence-linked knowledge assets. Includes local native PDF extraction and an optional Docling semantic parsing adapter; not a model trainer or automatic correctness guarantee.

## Use
Install the directory as an Agent Skill in your client, or tell an agent with filesystem access to read SKILL.md. Invoke `$textbook-to-skill` with textbook paths, optional scope and target task. Default output is a knowledge pack. Optional outputs: independent domain skill or a reviewable integration patch. No GitHub push by default.

Example: 请使用 $textbook-to-skill 学习我提供的 DFMA 教材，目标为 SolidWorks 制造与装配设计决策。按章记录覆盖与来源，输出概念、规则、公式、脚本、验证及集成建议。未经证实的内容保留 candidate，不上传教材原文。

Initialize an empty output: `python scripts/init_pack.py ./my-knowledge-pack` (path must not exist). Validate structure: `python scripts/validate_pack.py ./my-knowledge-pack`. Run included synthetic tests: `python -m unittest discover -s evals -v`.

Tests cover pack tools and synthetic extraction cases. Actual extraction, source review, formula implementation, domain evaluations and integration require the supplied textbook and a capable agent. No textbook has been ingested in this release. No external service or model API is required by the two bundled scripts.

## PDF extraction v0.2.0

Install optional dependencies in an isolated environment (review upstream licenses, hardware and model download requirements):

```sh
python -m pip install -r requirements-pdf.txt
python scripts/pdf_pipeline.py native textbook.pdf private-evidence/native --start 1 --end 10
python -m pip install -r requirements-semantic.txt
python scripts/pdf_pipeline.py semantic textbook.pdf private-evidence/semantic --start 1 --end 10
python scripts/extraction_metrics.py gold.json predictions.json
python -m unittest discover -s evals -v
```

Docling is an optional local backend; first use may fetch model weights. See [PDF pipeline](references/pdf-pipeline.md) for preflight, evidence, scans, figure crops and review; [evaluation](references/extraction-evaluation.md) for metrics. MinerU 4.x is now available via a local optional adapter. Source text/images and intermediate outputs stay private. Real textbook accuracy and semantic backend runtime have not yet been established. Existing pack schema remains compatible.

## v0.2.4 — integrated extraction suite

See [extraction suite](references/extraction-suite.md) for commands, upstream projects, data formats, review gates and limitations. Four development directions are implemented at a foundational level: local MinerU 4.x invocation and normalized page comparison; calibrated color-based chart extraction; strict engineering-field scoring; frozen dev/holdout evaluation. This is an implementation milestone, not an accuracy-certified release. The five new synthetic tests pass locally; MinerU and Docling were not installed in that environment; real textbook holdout and official external benchmark results remain NOT_RUN.

Install appropriate optional dependencies separately: `pip install -r requirements-pdf.txt`; for charts, `pip install -r requirements-chart.txt`. Install MinerU 4.x using upstream instructions in a dedicated environment. Run `python -m unittest discover -s evals -v`.

## v0.3.0 — knowledge graph, decision and collaborative learning

This release integrates the planned v0.3–v0.6 development directions into one foundational implementation. See [knowledge system](references/knowledge-system.md) and [collaborative learning](references/collaborative-learning.md). The previous PDF extraction and pack tools remain available.

Local CLI: `python scripts/knowledge_cli.py --help`. Optional cross-unit comparisons: install `requirements-knowledge.txt` in a suitable environment. Run tests with `python -m unittest discover -s evals -v`. The new modules use a lightweight local graph, typed predicate checks, reviewer evidence records, resumable task ledger and paired scores; they do not train a model, automatically launch subagents, run external GraphRAG/PaperQA/LangGraph systems, or verify real textbooks by themselves.

New synthetic test cases are provided. Runtime and real textbook accuracy must be verified separately; this release does not claim measured downstream improvement.
