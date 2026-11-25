# Extraction suite v0.2.4

This release integrates the four requested development directions at foundation level. It does not claim best-in-class local accuracy. Upstream tools are referenced or invoked through public interfaces, not copied. Pin exact dependency, model, tier and dataset versions; review licenses and model download needs. Keep textbook source and intermediate evidence private.

## 0.2.1: multi-parser comparison

- MinerU 4.x CLI and structured content contract: https://github.com/opendatalab/MinerU/blob/master/docs/en/usage/cli_tools.md ; https://github.com/opendatalab/MinerU/blob/master/docs/en/reference/output_files.md . It returns zero-based page_idx, metadata.producer and structured blocks. Use the actual installed release and check CLI help; no implicit remote endpoint; check local configuration/network before private input. No MinerU model installed in the test environment.
- Docling: https://github.com/docling-project/docling ; existing semantic adapter. PaddleOCR (https://github.com/PaddlePaddle/PaddleOCR) is a candidate for region-specific fallback, not automatically invoked.
- PyMuPDF: native source evidence. Compare on equal physical page scope. Source SHA and one-based original page IDs must match. Native text may include more than the MinerU plain-text-block subset, so difference is a review signal, not error rate.
- Commands:
  python scripts/pdf_pipeline.py native textbook.pdf private-evidence/native --start 5 --end 10
  python scripts/extraction_suite.py mineru textbook.pdf private-evidence/mineru --start 5 --end 10 --tier standard
  python scripts/extraction_suite.py compare private-evidence/native/pages.json private-evidence/mineru/pages.json private-evidence/compare.json
- MinerU output retains ZIP and original blocks, including formulas, tables and images; only plain text is normalized for page comparison. Use actual artifact references, page geometry and source render for other elements. Missing pages remain explicit. No arbitrary ZIP extraction.

## 0.2.2: chart data and image analysis

Use WebPlotDigitizer (https://github.com/automeris-io/WebPlotDigitizer, https://automeris.io/docs/digitize/) for assisted complex chart digitization; PDFFigures2 (https://github.com/allenai/pdffigures2) for scholarly figure/caption candidates; OpenCV (https://github.com/opencv/opencv) for optional advanced masks. These are external references, not embedded implementations. Prefer explicit text/tables and native vector data over pixel estimates for the same quantity/conditions. Do not infer precise dimensions from a schematic.

Local command: python scripts/extraction_suite.py chart crop.png calibration.json private-evidence/points.json

Example calibration JSON: {"rgb":[255,0,0],"tolerance":25,"roi":[0,0,101,101],"x_axis":[0,100,0,10,"linear"],"y_axis":[100,0,1,100,"log10"],"max_spread_px":3}
ROI is [left,top,right,bottom), pixels use top-left origin of actual crop. Each axis is [pixel0,pixel1,value0,value1,scale]. Review both labeled anchors, independent ticks, units, legend and source crop. RGB Euclidean threshold selects candidates; per-column median and stroke bounds, ambiguous columns excluded, missing/outside counted. Orthogonal, single-valued XY plots only; no automatic axis detection, perspective/rotation, overlapping same-color series, dual axes or guaranteed exclusion of grid/legend. No interpolation of missing data or extrapolation. Stroke extent is not total measurement uncertainty. Preserve image hash, calibration, review evidence and overlay or spot checks; do not promote unreviewed estimates to verified rules.

## 0.2.3: metrics

Use official OmniDocBench (https://github.com/opendatalab/OmniDocBench) for comparable text/order, formula CDM and table TEDS, Microsoft Table Transformer/GriTS (https://github.com/microsoft/table-transformer) for table topology/content/location. Run pinned upstream evaluator and dataset; do not relabel local exact scores as official metrics. Formula equivalence, table semantic alignment and chart point error need separately validated evaluation. Use strict literal matching for numbers, units, formulas, cells, figure labels and reading order, retaining sign, case, punctuation, exponent and blank/zero distinctions. Per-case source region and independent reviewer must verify critical fields before knowledge admission. Gold annotation must cover difficult and missing items.

## 0.2.4: blind pilot and routing

Use OmniDocBench and olmOCR-Bench (https://github.com/allenai/olmocr), plus licensed private engineering holdout. Suggested initial sample: 40 pages across ordinary text, multicolumn, mixed-language, scans, dense formulas, merged tables, vector drawings and charts. Freeze dev and holdout before tuning; avoid overlapping source passages and adjacent near-duplicates, not only identical page IDs. Hashes detect changes but do not enforce access isolation. Keep gold files inaccessible to parser/agent until predictions are frozen. Separate public results from private holdout results.

Plan JSON example: {"cases":[{"id":"dev1","source_sha256":"<64 lowercase hex>","page":1,"split":"dev","stratum":"formula"},{"id":"test1","source_sha256":"<64 lowercase hex>","page":2,"split":"holdout","stratum":"table"}]}
python scripts/extraction_suite.py freeze plan.json frozen.json

Gold and predictions each have {"plan_sha256":"<frozen plan hash>","items":[{"case_id":"test1","id":"cell1","kind":"table_cell","value":"-0.15 MPa"}]}. Stable IDs and locators from independent annotator, not chosen by predictions. Kinds: text, number, unit, formula, table_cell, figure_label, reading_order. Keep provenance and annotation metadata alongside files. Missing predictions are allowed and reduce recall. Gold must cover every holdout case.
python scripts/extraction_suite.py evaluate frozen.json gold.json predictions.json report.json

Report overall and per-stratum exact-match precision, recall, F1, missing, extra, mismatch and unresolved critical fields. Whitespace collapse only. Use identical plan and field set for native, Docling, MinerU and hybrid. Optimize routing on dev only: native for straightforward text, semantic for scan/layout/formulas/tables, alternate parser for conflicts, review original evidence for every critical field. Record actual versions, wall time, hardware, failures and predictions hash. Real benchmark runs NOT_RUN; no claim of measured improvement. Zero unresolved critical fields applies to reviewed decision-rule admission, not overall book accuracy.
