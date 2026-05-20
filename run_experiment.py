#!/usr/bin/env python3
"""
Run evaluation for a specific config+version, save prompt snapshot + results,
and append a summary line to EXPERIMENT_LOG.md.

Usage:
  python run_experiment.py --config a --version v0 --api-key YOUR_KEY
  python run_experiment.py --config b --version v1 --api-key YOUR_KEY [--notes "what changed"]
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime


def read_prompt(config: str) -> str:
    path = f"config_{config}_prompt.txt"
    with open(path) as f:
        return f.read()


def run_evaluator(config: str, output_dir: str, api_key: str, model: str) -> dict:
    result = subprocess.run(
        [
            sys.executable, "evaluator.py",
            "--config", config,
            "--output-dir", output_dir,
            "--api-key", api_key,
            "--model", model,
            "--delay", "1.5",
        ],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    if result.returncode != 0:
        print("STDERR:", result.stderr[-2000:])
        raise RuntimeError(f"Evaluator failed: {result.returncode}")
    print(result.stdout)
    return result.stdout


def parse_aggregate(output_dir: str, config: str) -> dict:
    for f in os.listdir(output_dir):
        if f.startswith(f"config_{config}_") and f.endswith(".json"):
            with open(os.path.join(output_dir, f)) as fh:
                data = json.load(fh)
            return data.get("aggregate", {})
    return {}


def append_log(version: str, config: str, agg: dict, notes: str, prompt: str):
    log_path = "EXPERIMENT_LOG.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    success = agg.get("success_rate", 0)
    exact = agg.get("exact_matches", "?")
    tokens = agg.get("avg_tokens", 0)
    tool_calls = agg.get("avg_tool_calls", 0)

    entry = f"""
---

## Config {config.upper()} — {version} — {timestamp}

**Result:** {success:.0%} ({exact}/25) | avg tokens: {tokens:.0f} | avg tool calls: {tool_calls:.2f}

**Changes:** {notes if notes else "—"}

**Prompt snapshot:**

```
{prompt}
```
"""
    with open(log_path, "a") as f:
        f.write(entry)
    print(f"\nLogged to {log_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, choices=["a", "b"])
    parser.add_argument("--version", required=True)
    parser.add_argument("--api-key", default=os.environ.get("LLM_API_KEY", ""))
    parser.add_argument("--model", default="google/gemini-2.5-flash")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("No API key. Pass --api-key or set LLM_API_KEY env var.")

    output_dir = f"results/config_{args.config}_{args.version}"
    os.makedirs(output_dir, exist_ok=True)

    # Save prompt snapshot before running
    prompt = read_prompt(args.config)
    with open(os.path.join(output_dir, "prompt.txt"), "w") as f:
        f.write(prompt)

    print(f"\n=== Running Config {args.config.upper()} {args.version} ===")
    run_evaluator(args.config, output_dir, args.api_key, args.model)

    agg = parse_aggregate(output_dir, args.config)
    append_log(args.version, args.config, agg, args.notes, prompt)
    print(f"Results saved to {output_dir}/")


if __name__ == "__main__":
    main()
