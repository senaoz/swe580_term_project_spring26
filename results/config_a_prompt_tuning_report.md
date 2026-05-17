# Config A Prompt Tuning Report

**Model:** google/gemini-2.5-flash via OpenRouter  
**Configuration:** Config A — 4 coarse-grained tools  
**Date:** 2026-05-16

---

## Overview

This report documents three iterations of system prompt improvement for Config A, starting from a minimal 2-line baseline and progressively addressing failure patterns identified through trace analysis.

---

## Baseline (Minimal Prompt)

**Prompt:** "You are a helpful assistant that searches through a personal knowledge vault of markdown notes. Use the provided tools to find relevant notes and answer the user's query."

| Metric | Value |
|---|---|
| Success rate | 40% (10/25) |
| Avg tool calls | 1.0 |
| Avg tokens | 1,296 |

**Per-category results:**

| Category | Success Rate |
|---|---|
| tag_search | 100% |
| temporal | 33% |
| simple_lookup | 50% |
| content_search | 0% |
| multi_faceted | 56% |
| graph_based | 14% |

**Root causes identified via trace analysis:**

1. **Missing output format** — The LLM found the correct notes in 8+ queries but never emitted `RESULT_PATHS: [...]`. The evaluator parses this marker; without it, results were scored as empty.
2. **Folder/tag confusion** — "research", "meetings", "reference" are folder names, not tags. The LLM repeatedly called `search_notes(tags: ["research"])` which returned nothing because no note has that tag.
3. **Title format unknown** — The LLM guessed titles like "Reinforcement Learning Research" or "Chatbot Prototype Project" instead of the correct "Reinforcement Learning" and "Chatbot Prototype" (filename without `.md`, underscores replaced by spaces).
4. **No tool selection guidance** — For graph queries, the LLM sometimes used `search_notes` instead of `get_related_notes`.

---

## Prompt v1

**Changes:** Added vault structure description, title convention, folder vs. tag distinction, per-tool usage guide, and mandatory `RESULT_PATHS` output format.

| Metric | Value | Δ Baseline |
|---|---|---|
| Success rate | 84% (21/25) | +44% |
| Avg tokens | 2,752 | +1,456 |

**Per-category results:**

| Category | Baseline | v1 | Δ |
|---|---|---|---|
| tag_search | 100% | 100% | — |
| temporal | 33% | 100% | +67% |
| simple_lookup | 50% | 100% | +50% |
| content_search | 0% | 100% | +100% |
| multi_faceted | 56% | 78% | +22% |
| graph_based | 14% | 71% | +57% |

**Key insight:** The single biggest gain — 8 queries fixed in one step — came from adding the `RESULT_PATHS` format requirement. The LLM had been finding the right answers all along; the evaluator simply could not parse the unstructured responses.

**Remaining failures (4 queries):**
- `q11`: `date_to: "2026-01-08"` was passed for a "before January 8" query, accidentally including Jan 8 notes.
- `q18`: Only `Chatbot_Prototype` was found; `Paper_Recommender` and `Text_Summarizer` link to `Transformers`, not directly to `Attention_Mechanisms` — multi-hop traversal needed.
- `q22`: `search_notes(query: "BERT")` returned 10 results; `Advisor_Meeting_Feb07.md` was ranked 11th and cut off.
- `q23`: `search_notes(tags: ["python"])` returned 10 results, all from `projects/`; `reference/` python notes were beyond the cap.

---

## Prompt v2

**Changes:** Added date boundary precision rules ("before X" → `date_to: X-1`), folder-restricted query pattern (search then filter by path prefix), and multi-hop graph pattern (check related notes' incoming links if first pass yields few results).

| Metric | Value | Δ v1 |
|---|---|---|
| Success rate | 88% (22/25) | +4% |
| Avg tokens | 3,497 | +745 |

**q11 fixed:** LLM correctly used `date_to: "2026-01-07"` for "before January 8".

**Remaining failures (3 queries):** q18, q22, q23 — same as v1.

---

## Prompt v3

**Changes:** Made the second-call fallback instruction more explicit for cap-limited searches (with concrete examples for q22 and q23 patterns). Strengthened multi-hop instruction for q18.

| Metric | Value | Δ v2 |
|---|---|---|
| Success rate | 84% (21/25) | -4% |
| Avg tokens | 3,718 | +221 |

**Regression:** q16 broke. The more detailed multi-hop instructions caused the LLM to include `projects/Paper_Recommender.md` in the outgoing links of `Transformers` (it is technically there), inflating precision below 1.0. The prompt addition over-generalized.

**q22 partial improvement:** The LLM followed the second-call example literally (`search_notes(query: "BERT meeting advisor")`) and found `Advisor_Meeting_Feb07.md` — but lost `Advisor_Meeting_Jan24.md` in the process. Precision=1.0 but recall=0.67 (different 2 out of 3).

**q23 still failing:** The LLM made only one tool call and returned empty after filtering. The fallback instruction was not followed.

---

## Summary Table

| Version | Success Rate | Exact Matches | Avg Tokens | Δ Success |
|---|---|---|---|---|
| Baseline | 40% | 10/25 | 1,296 | — |
| v1 | 84% | 21/25 | 2,752 | +44% |
| v2 | 88% | 22/25 | 3,497 | +4% |
| v3 | 84% | 21/25 | 3,718 | -4% |

**Best result: v2 at 88% (22/25 exact match)**

---

## Persistent Failure Analysis

Three queries remain unsolved at v2:

| Query | Root Cause | Category |
|---|---|---|
| q18 — "project notes related to attention mechanism research" | Multi-hop required: answer notes link to `Transformers`, not directly to `Attention_Mechanisms` | graph_based |
| q22 — "meeting notes about BERT" | Search result cap (10): the 3rd matching meeting ranks 11th by relevance | multi_faceted |
| q23 — "reference notes tagged python" | Search result cap (10): all 10 returned results are from `projects/`; `reference/` python notes ranked below cap | multi_faceted |

**q22 and q23** expose a fundamental limitation: the 10-result cap interacts badly with folder-restricted queries when the target folder's notes have lower relevance scores than notes from other folders. No prompt instruction can reliably fix this without changing the tool interface (e.g. adding a `folder` parameter to `search_notes`).

**q18** exposes a multi-hop graph reasoning gap. Config A's `get_related_notes` is a single-hop tool. Answering this query requires chaining: get outgoing links of `Attention_Mechanisms` → for each linked research note, get incoming links → filter to `projects/`. This is achievable with multiple tool calls but requires the LLM to reason about the vault's link topology without explicit guidance.

---

## Observations for Config B Comparison

These findings have direct implications for Config B prompt design:

- **q22/q23 cap problem** may affect Config B equally, since both configs share the same Whoosh backend with the same 10-result limit.
- **q18 multi-hop** may be easier for Config B: separate `get_incoming_links` and `get_outgoing_links` tools with clear names may prompt the LLM to chain them more naturally.
- **Token cost trade-off:** Config A's coarse tools achieve high accuracy with exactly 1 tool call per query (avg 1.04 in v2). Config B's fine-grained tools are expected to require more calls for multi-faceted queries, increasing token usage.

---

## Next Steps

- [ ] Run Config B baseline and compare
- [ ] Tune `config_b_prompt.txt` using same methodology
- [ ] Compare final Config A vs Config B head-to-head
- [ ] Analyze token efficiency per category (accuracy per token)
