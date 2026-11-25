# Textbook-to-Skill v0.1.0

A reusable agent workflow for transforming accessible textbooks into original, evidence-linked knowledge assets. Not a standalone PDF parser, vector database, model trainer or automatic correctness guarantee.

## Use
Install the directory as an Agent Skill in your client, or tell an agent with filesystem access to read SKILL.md. Invoke `$textbook-to-skill` with textbook paths, optional scope and target task. Default output is a knowledge pack. Optional outputs: independent domain skill or a reviewable integration patch. No GitHub push by default.

Example: 请使用 $textbook-to-skill 学习我提供的 DFMA 教材，目标为 SolidWorks 制造与装配设计决策。按章记录覆盖与来源，输出概念、规则、公式、脚本、验证及集成建议。未经证实的内容保留 candidate，不上传教材原文。

Initialize an empty output: `python scripts/init_pack.py ./my-knowledge-pack` (path must not exist). Validate structure: `python scripts/validate_pack.py ./my-knowledge-pack`. Run included synthetic tests: `python -m unittest discover -s evals -v`.

The tests cover the pack tools only. Actual extraction, source review, formula implementation, domain evaluations and integration require the supplied textbook and a capable agent. No textbook has been ingested in this release. No external service or model API is required by the two bundled scripts.
