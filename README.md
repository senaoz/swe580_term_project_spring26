# SWE 580 — Tool Granularity Project

## Submission

| | File |
|---|---|
| Tool configs | [config_a_tools.json](config_a_tools.json) · [config_b_tools.json](config_b_tools.json) |
| System prompts | [config_a_prompt.txt](config_a_prompt.txt) · [config_b_prompt.txt](config_b_prompt.txt) |
| Results | [results/final/config_a_20260516_215635.json](results/final/config_a_20260516_215635.json) · [results/final/config_b_20260516_215635.json](results/final/config_b_20260516_215635.json) · [results/final/comparison_20260516_215635.json](results/final/comparison_20260516_215635.json) |
| Report | [PDF](https://github.com/senaoz/swe580_term_project_spring26/blob/main/SWE%20580%20Term%20Project%20Report.pdf) |

---


## Files Overview

| File | Your role |
|---|---|
| `config_a_tools.json` | **Edit** — tool descriptions for Config A (4 tools) |
| `config_b_tools.json` | **Edit** — tool descriptions for Config B (9 tools) |
| `config_a_prompt.txt` | **Edit** — system prompt for Config A |
| `config_b_prompt.txt` | **Edit** — system prompt for Config B |
| `test_queries.json` | Read-only — 25 queries with ground truth |
| `evaluator.py` | Read-only — runs evaluation, computes metrics |
| `executors.py` | Read-only — maps tool calls to search backend |
| `search_backend.py` | Read-only — Whoosh search implementation |
| `llm_runner.py` | Read-only — LLM API interaction loop |
| `vault/` | Read-only — 100 markdown notes |

## Setup

**1. Create a virtual environment and install dependencies:**
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Get an API key:**

You can use any method you prefer to access Gemini 2.5 Flash. The code assumes the OpenRouter interface but you can easily modify it to any other OpenAI-compatible API by changing `--base-url` and `--model`.

## Running the Evaluator

Edit the provided `.env` file and replace the placeholder with your key:
```
LLM_API_KEY=your_openrouter_key_here
```
Then load it and run:
```bash
export $(cat .env) && python evaluator.py
```

Or pass the key directly on the command line:
```bash
python evaluator.py --api-key YOUR_KEY
```

This runs both Config A and Config B on all 25 queries and prints a side-by-side comparison.

**Useful options:**

| Flag | Default | Description |
|---|---|---|
| `--api-key` | — | Your OpenRouter API key (required) |
| `--model` | `google/gemini-2.5-flash` | LLM to use |
| `--config` | `both` | Run only `a`, only `b`, or `both` |
| `--delay` | `2.0` | Seconds between queries (avoid rate limits) |
| `--verbose` | off | Print tool call trace per query |
| `--output-dir` | `results/` | Where to save JSON output |

**Run one config at a time to save credits while iterating** (if `--config` is omitted, both configs run):
```bash
python evaluator.py --api-key YOUR_KEY --config a
python evaluator.py --api-key YOUR_KEY --config b
```

**Inspect individual tool calls during the run:**
```bash
python evaluator.py --api-key YOUR_KEY --config a --verbose
```

Each query result in the saved JSON files also contains a `"trace"` field — a round-by-round log of every tool called, the arguments passed, and the result returned. This is useful for debugging why a query succeeded or failed: you can follow exactly what the LLM did to arrive at its final response.

## What You Can Edit

### Tool descriptions (`config_a_tools.json`, `config_b_tools.json`)

You may edit any `"description"` field — for tools and for their parameters. Tool names and parameter names are fixed; changing them will break the executor routing.

Example — before:
```json
"description": "Search notes in the vault."
```

After:
```json
"description": "Search notes by free-text content, tags, and/or date range. Use this as your primary discovery tool. Combine parameters to narrow results — e.g., pass both query and tags to find tagged notes matching a topic."
```

### System prompts (`config_a_prompt.txt`, `config_b_prompt.txt`)

Plain text files. Write whatever system-level instructions help the LLM use the tools correctly for each configuration. There is no required format — the prompt is passed verbatim as the system message.

## Understanding the Output

Results are saved to `results/` as JSON files. The console prints a summary table:

```
Metric                    Config A     Config B       Winner
-----------------------------------------------------------------
Success Rate                 0.72         0.68            A
Avg Precision                0.81         0.74            A
Avg Recall                   0.75         0.71            A
Avg F1                       0.78         0.72            A
Avg Tool Calls               2.40         3.10            A
Avg Tokens                1823.0       2241.0            A
Avg Latency (s)              3.21         4.05            A
```

**Metrics defined:**
- **Success rate** — fraction of queries with perfect precision and full recall (up to 10 notes)
- **Precision** — of notes returned, fraction that were correct
- **Recall** — of correct notes (capped at 10), fraction that were returned
- **F1** — harmonic mean of precision and recall

**Important:** the evaluator extracts note paths from the LLM's final response by looking for a `RESULT_PATHS: ["path/to/note.md", ...]` line. Your system prompt should instruct the LLM to include this line in its response, otherwise extracted paths may be empty even when the correct notes were retrieved.

## What to Submit

1. Your four edited files: `config_a_tools.json`, `config_b_tools.json`, `config_a_prompt.txt`, `config_b_prompt.txt`
2. The `results/` folder with your final evaluation JSON files
3. Your written report (see project definition for required sections)
