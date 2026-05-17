# Tool Granularity Evaluation Report
## Config A (Coarse-Grained) vs Config B (Fine-Grained)

**Model:** google/gemini-2.5-flash via OpenRouter  
**Vault:** 100 markdown notes, 5 folders  
**Test queries:** 25 across 6 categories  
**Date:** 2026-05-16

---

## 1. Methodology

### Setup

Both configurations share the same Whoosh search backend and vault. Only the tool interface differs:

| Configuration | Tools | Design |
|---|---|---|
| **Config A** | 4 | Coarse-grained: each tool accepts multiple optional parameters |
| **Config B** | 9 | Fine-grained: each tool does exactly one thing |

Each configuration was evaluated against the same 25 ground-truth queries. The LLM receives only the tool schemas and system prompt — it decides which tools to call and with what arguments.

### Evaluation Metric

**Exact match** = the set of extracted note paths equals the set of expected paths exactly (precision = 1.0 AND recall ≥ min(expected, 10) / expected).

Secondary metrics: precision, recall, F1, tool calls per query, tokens per query, latency.

### Prompt Tuning Methodology

Both configs started with a minimal 2-line system prompt. Failures were diagnosed by inspecting the `trace` field in each result (round-by-round tool calls and backend responses). Prompts were iteratively improved to address specific failure patterns.

| Config | Iterations | Best Version | Best Success Rate |
|---|---|---|---|
| A | 3 (baseline → v1 → v2 → v3) | v2 | **88%** |
| B | 2 (baseline → v1 → v2) | v1 | **84%** |

---

## 2. Baseline Results (Minimal Prompt)

With a 2-line prompt ("You are a helpful assistant... Use the provided tools..."):

| Metric | Config A | Config B |
|---|---|---|
| Success rate | 40% (10/25) | 24% (6/25) |
| Avg tool calls | 1.00 | 1.16 |
| Avg tokens | 1,296 | 1,730 |
| Avg latency (s) | 1.744 | 1.755 |

**Per-category baseline:**

| Category | Config A | Config B |
|---|---|---|
| simple_lookup | 50% | 0% |
| tag_search | 100% | 100% |
| temporal | 33% | 67% |
| content_search | 0% | 0% |
| multi_faceted | 56% | 22% |
| graph_based | 14% | 0% |

**Key observation:** Config A had a higher baseline (40% vs 24%) despite more query failures. The difference traces to one root cause: with a minimal prompt, Config B's LLM used `get_note_by_title` correctly for tag queries but failed to format output, whereas Config A at least succeeded at tag and some multi-faceted queries.

**Dominant failure cause in both configs:** The LLM found correct results via tool calls but did not emit a structured `RESULT_PATHS: [...]` marker, so the evaluator scored them as empty. This single issue accounted for 8–10 failed queries per config at baseline.

---

## 3. Best Results After Prompt Tuning

### Config A — Best: v2 (88%)

**What the prompt added:**
- Vault structure and folder descriptions
- Title convention (filename → title)
- Folder vs. tag distinction (folders are NOT tags)
- Per-tool usage guide with decision rules
- Date boundary precision ("before Jan 8" → `date_to: 2026-01-07`)
- Folder-restricted query pattern (search then filter by path prefix)
- Mandatory `RESULT_PATHS` output format

### Config B — Best: v1 (84%)

**What the prompt added:**
- Same vault structure, title convention, and RESULT_PATHS format
- Tool selection table (9 tools with clear when-to-use rules)
- Multi-step intersection patterns (tag+content, tag+date, graph+folder)
- Title stripping rule ("attention mechanism research" → "Attention Mechanisms")
- Multi-hop graph chaining instructions

---

## 4. Head-to-Head Comparison (Best vs Best)

Config A v2 vs Config B v1:

| Metric | Config A | Config B | Winner |
|---|---|---|---|
| **Success rate** | **88% (22/25)** | 84% (21/25) | **A** |
| Avg tool calls | **1.08** | 1.40 | **A** |
| Avg tokens | **3,377** | 3,857 | **A** |
| Avg latency (s) | **1.541** | 1.503 | B (marginal) |

### Per-Category (Best Versions)

| Category | Config A | Config B | Winner |
|---|---|---|---|
| simple_lookup | **100%** | **100%** | Tie |
| tag_search | **100%** | **100%** | Tie |
| temporal | **100%** | **100%** | Tie |
| content_search | **100%** | **100%** | Tie |
| multi_faceted | **78%** | 67% | **A** |
| graph_based | **86%** | **86%** | Tie |

### Query-Level Breakdown

| Query | Category | Config A | Config B | Tools A | Tools B | Tokens A | Tokens B |
|---|---|---|---|---|---|---|---|
| q01 | simple_lookup | ✓ | ✓ | 1 | 1 | 3,079 | 3,383 |
| q02 | simple_lookup | ✓ | ✓ | 1 | 1 | 3,028 | 3,332 |
| q03 | tag_search | ✓ | ✓ | 1 | 1 | 2,999 | 3,299 |
| q04 | tag_search | ✓ | ✓ | 1 | 1 | 3,669 | 3,967 |
| q05 | temporal | ✓ | ✓ | 1 | 1 | 2,997 | 3,296 |
| q06 | temporal | ✓ | ✓ | 1 | 1 | 3,229 | 3,527 |
| q07 | content_search | ✓ | ✓ | 1 | 1 | 3,006 | 3,307 |
| q08 | content_search | ✓ | ✓ | 1 | 1 | 2,816 | 3,115 |
| q09 | multi_faceted | ✓ | ✓ | 1 | **2** | 3,075 | 4,263 |
| q10 | graph_based | ✓ | ✓ | 1 | 1 | 3,681 | 3,964 |
| q11 | multi_faceted | ✓ | **✗** | 1 | 2 | 3,144 | 4,734 |
| q12 | multi_faceted | ✓ | ✓ | 1 | **2** | 2,936 | 4,226 |
| q13 | multi_faceted | ✓ | ✓ | 1 | 1 | 3,723 | 4,025 |
| q14 | multi_faceted | ✓ | ✓ | 1 | 1 | 3,568 | 3,849 |
| q15 | multi_faceted | ✓ | **✗** | 1 | 2 | 3,322 | 4,600 |
| q16 | graph_based | ✓ | ✓ | 1 | 1 | 3,079 | 3,404 |
| q17 | graph_based | ✓ | ✓ | 1 | **2** | 3,461 | 3,828 |
| q18 | graph_based | **✗** | **✗** | 1 | 2 | 3,453 | 3,181 |
| q19 | graph_based | ✓ | ✓ | 1 | **2** | 3,255 | 3,613 |
| q20 | graph_based | ✓ | ✓ | 1 | 1 | 3,694 | 3,977 |
| q21 | graph_based | ✓ | ✓ | 3 | 3 | 5,244 | 5,681 |
| q22 | multi_faceted | **✗** | **✗** | 1 | 2 | 3,633 | 4,900 |
| q23 | multi_faceted | **✗** | ✓ | 1 | 1 | 3,589 | 3,608 |
| q24 | multi_faceted | ✓ | ✓ | 1 | 1 | 3,213 | 3,512 |
| q25 | temporal | ✓ | ✓ | 1 | 1 | 3,519 | 3,822 |

**Queries where configs differ:**
- **q11** (tag+date): A ✓, B ✗ — Config B's tag search hit the 10-result cap; the expected notes were beyond it.
- **q15** (tag+content): A ✓, B ✗ — Intersection of two capped searches missed `Diffusion_Models.md` and `Recurrent_Networks.md`.
- **q23** (folder+tag): A ✗, B ✓ — Config B discovered that "reference" is a valid tag (`search_by_tags(["python","reference"])`); Config A's combined search couldn't express this.
- **q18**: Both fail — multi-hop graph query requiring chaining across non-adjacent notes.
- **q22**: Both fail — target meeting note ranks 11th in content search, beyond the 10-result cap.

---

## 5. Analysis

### 5.1 Token Efficiency

Config A used on average **480 fewer tokens per query** (3,377 vs 3,857). This is consistent: Config B requires more tool calls for multi-faceted queries (it has no combined search), and each additional tool call adds a round-trip to the message history.

For the 9 multi-faceted queries, Config B averaged **1.56 tool calls** vs Config A's **1.00**. The extra calls explain the token gap.

### 5.2 Where Fine-Grained Tools Help (Config B)

**q23 — folder+tag query:** Config B's `search_by_tags` accepts a list with AND logic. Passing `["python", "reference"]` surfaces only notes tagged with both — an elegant one-call solution. Config A's `search_notes` could not express this because "reference" is both a folder name and a tag, and the combined search conflated them.

**Temporal baseline:** Config B scored 67% at baseline vs Config A's 33%. The reason: `search_by_date` has an unambiguous name — the LLM called it immediately without needing prompt guidance. Config A's `search_notes` requires knowing to pass `date_from`/`date_to` params explicitly.

**Tool call clarity for graph queries:** In Config B, `get_incoming_links` vs `get_outgoing_links` are named for their direction. At baseline, Config A's LLM sometimes used `search_notes` instead of `get_related_notes` for graph queries. Config B had no such ambiguity.

### 5.3 Where Coarse-Grained Tools Help (Config A)

**Multi-faceted queries (q09, q11, q12, q13, q15):** Config A's `search_notes` accepts query, tags, and date_from/date_to simultaneously. One call handles all constraints. Config B must call multiple tools and intersect results manually — a process vulnerable to the 10-result cap.

The intersection vulnerability is the key weakness of fine-grained tools: when `search_by_tags` returns 10 results (cap hit) and `search_by_content` returns 10 different results, the intersection may miss notes that are beyond cap in either search. Config A avoids this by filtering at the backend level.

**q11 specifically:** Config A passed with 1 tool call using `search_notes(tags: ["python"], date_to: "2026-01-07")`. Config B failed because `search_by_tags(["python"])` returned 10 results that excluded 3 of the 4 expected notes.

### 5.4 Prompt Sensitivity

Both configs required substantial prompt engineering to reach peak performance:

| Config | Baseline | After Tuning | Gain |
|---|---|---|---|
| A | 40% | 88% | +48% |
| B | 24% | 84% | +60% |

Config B had a lower baseline but a larger absolute gain. The most impactful single change in both cases was adding the `RESULT_PATHS` output format requirement — without it, the LLM was finding correct answers but the evaluator could not parse them.

Config B required more complex prompt instructions (multi-step intersection patterns, multi-hop graph chaining) because its tools are more primitive. Config A's richness is in the tool parameters; Config B's is in the prompt.

### 5.5 Persistent Failures

Three queries failed in both configurations:

| Query | Category | Root Cause |
|---|---|---|
| q18 | graph_based | Multi-hop: expected projects link to Transformers, not directly to Attention_Mechanisms. Requires chaining get_related_notes across 2 levels. |
| q22 | multi_faceted | Backend cap: the 3rd expected meeting note ranks 11th in content search. No prompt instruction can overcome ranking limits. |
| q23* | multi_faceted | Config A only: "reference" tag not surfaced because folder/tag ambiguity. Config B solved this with `search_by_tags(["python","reference"])`. |

*q23 failed only in Config A.

---

## 6. Findings and Recommendations

### Finding 1: Output format is the most critical prompt element

The single largest performance gap — at baseline, both configs performed far below their potential — was caused by the absence of a structured output format instruction. The LLM found correct answers but expressed them in unstructured prose. Adding `RESULT_PATHS: [...]` as a mandatory output requirement fixed 8–10 queries per config instantly.

**Implication:** When designing LLM tool systems, the output contract (how the LLM should report results) is as important as the tool input contract (how parameters are described).

### Finding 2: Coarse-grained tools are more token-efficient for multi-faceted queries

Config A handled all multi-parameter queries in a single tool call. Config B required 1.56 calls on average for the same category, and the intersection pattern introduced a failure mode (cap vulnerability) that Config A does not have.

For production systems where latency and token cost matter, coarse-grained tools with well-designed parameter sets are preferable for queries that combine multiple filters.

### Finding 3: Fine-grained tools have lower baseline but more room for improvement via naming

Config B had a lower baseline (24% vs 40%) because 9 tools create more decision points. However, clear tool names (`get_incoming_links`, `search_by_date`) conveyed intent without needing prompt guidance in some categories (temporal: 67% baseline vs 33% for A).

This suggests fine-grained tools benefit more from good naming than from prompt instructions alone.

### Finding 4: The 10-result backend cap creates an asymmetric disadvantage for fine-grained tools

Config B's intersection pattern requires both tool results to contain the target notes. When either is capped, notes are missed. Config A's combined search applies all filters at the index level before truncating, so the cap affects final results less severely.

Increasing the result cap (or adding a `folder` filter parameter to `search_notes`) would likely improve Config B's multi-faceted performance more than prompt tuning.

### Recommendation

**For simple retrieval tasks** (lookup, single-tag, date-only, content-only): either configuration works equally well. Choose based on team familiarity.

**For multi-faceted queries combining tags, dates, and content:** Config A is preferable — it handles all constraints in one call, avoids intersection cap issues, and uses fewer tokens.

**For graph-traversal queries:** both configs perform similarly (86% each). Config B's explicit link-direction tools (`get_incoming_links` vs `get_outgoing_links`) provide clarity, but Config A's `get_related_notes(direction: ...)` achieves the same result with fewer calls.

**If extending the system:** adding a `folder` parameter to the backend search would benefit Config B most (fixes q23, q22 patterns). Adding a `max_results` override would benefit both.

---

## 7. Limitations

- **Single model:** All results use Gemini 2.5 Flash. A different model (e.g. GPT-4o, Claude Haiku) may favor different granularity due to differences in instruction following and tool call behavior.
- **25 queries:** The query set is small. Some per-category results (simple_lookup: 2 queries, tag_search: 2 queries) are not statistically robust.
- **Prompted system prompts:** The prompts were iteratively tuned by observing failures. A real-world deployment would have no such advantage. The baseline numbers are more representative of zero-shot performance.
- **No session state:** All tools are stateless. Multi-hop queries that benefit from remembering intermediate results (e.g. "first find all attention notes, then find what projects link to them") are handled entirely in the LLM's context window.
