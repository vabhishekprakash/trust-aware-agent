"""Check whether the model provider returns token log probabilities.

The fifth confidence signal in this project needs per-token log
probabilities. Run this script to confirm the provider you are pointing
at actually returns them before relying on that signal.

Usage:
    python scripts/check_logprobs.py
    python scripts/check_logprobs.py --model llama3.2:3b
    python scripts/check_logprobs.py --base-url http://localhost:11434/v1

Exit codes: 0 log probabilities returned, 1 not returned, 2 provider unreachable.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--model", default="qwen2.5:3b-instruct")
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    parser.add_argument("--prompt", default="Reply with exactly one word: yes")
    args = parser.parse_args()

    body = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "max_tokens": 5,
        "temperature": 0,
        "logprobs": True,
        "top_logprobs": 3,
    }
    request = urllib.request.Request(
        args.base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.load(response)
    except urllib.error.URLError as exc:
        print(f"could not reach {args.base_url}: {exc}")
        return 2

    choice = data["choices"][0]
    text = choice["message"]["content"]
    tokens = (choice.get("logprobs") or {}).get("content") or []

    print(f"model: {data.get('model')}")
    print(f"reply: {text!r}")
    if not tokens:
        print("log probabilities: not returned by this provider or model")
        return 1

    print(f"log probabilities: returned for {len(tokens)} token(s)")
    for token in tokens:
        alternatives = ", ".join(
            f"{alt['token']!r}={alt['logprob']:.3f}" for alt in token.get("top_logprobs", [])
        )
        print(f"  {token['token']!r:<12} logprob={token['logprob']:.3f}  alternatives: {alternatives}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
