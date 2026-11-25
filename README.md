# Textbook-to-Skill v0.2.0

A reusable agent workflow for transforming accessible textbooks into original, evidence-linked knowledge assets. Includes local native PDF extraction and an optional Docling semantic parsing adapter; not a model trainer or automatic correctness guarantee.

## Use
Install the directory as an Agent Skill in your client, or tell an agent with filesystem access to read SKILL.md. Invoke `$textbook-to-skill` with textbook paths, optional scope and target task. Default output is a knowledge pack. Optional outputs: independent domain skill or a reviewable integration patch. No GitHub push by default.

Example: 请使用 $textbook-to-skill 学习我提供的 DFMA 教材，目标为 SolidWorks 制造与装配设计决策。按章记录覆盖与来源，输出概念、规则、公式、脚本、验证及集成建议。未经证实的内容保留 candidate，不上传教材原文。

Initialize an empty output: `python scripts/init_pack.py ./my-knowledge-pack` (path must not exist). Validate structure: `python scripts/validate_pack.py ./my-knowledge-pack`. Run included synthetic tests: `python -m unittest discover -s evals -v`.

The tests cover the pack tools only. Actual extraction, source review, formula implementation, domain evaluations and integration require the supplied textbook and a capable agent. No textbook has been ingested in this release. No external service or model API is required by the two bundled scripts.

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

Docling is an optional local backend; first use may fetch model weights. See [PDF pipeline](references/pdf-pipeline.md) for preflight, evidence, scans, figure crops and review; [evaluation](references/extraction-evaluation.md) for metrics. MinerU is an optional independent external route, not bundled as an executable adapter. Source text/images and intermediate outputs stay private. Real textbook accuracy and semantic backend runtime have not yet been established. Existing pack schema remains compatible.
