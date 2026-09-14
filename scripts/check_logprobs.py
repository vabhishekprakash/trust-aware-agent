"""Check whether the model provider returns token log probabilities.

The fifth confidence signal in this project needs per-token log
probabilities. Run this script to confirm the provider you are pointing
at actually returns them before relying on that signal.

Usage:
    python scripts/check_logprobs.py
    python scripts/check_logprobs.py --model llama3.2:3b
    python scripts/check_logprobs.py --base-url http://localhost:11434/v1
    python scripts/check_logprobs.py --native

The default checks the OpenAI-compatible endpoint, which any hosted provider
also offers. --native checks Ollama's own /api/chat endpoint, the one
src/agent/provider.py uses, where log probabilities arrive as a top-level
"logprobs" list.

Exit codes: 0 log probabilities returned, 1 not returned, 2 provider unreachable
or it answered with an error status (the status and body are printed).
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
    parser.add_argument("--native", action="store_true", help="check Ollama's native /api/chat endpoint instead")
    args = parser.parse_args()

    messages = [{"role": "user", "content": args.prompt}]
    if args.native:
        base = args.base_url.rstrip("/")
        base = base[: -len("/v1")] if base.endswith("/v1") else base
        url = base + "/api/chat"
        body = {
            "model": args.model,
            "messages": messages,
            "stream": False,
            "logprobs": True,
            "top_logprobs": 3,
            "options": {"num_predict": 5, "temperature": 0},
        }
    else:
        url = args.base_url.rstrip("/") + "/chat/completions"
        body = {
            "model": args.model,
            "messages": messages,
            "max_tokens": 5,
            "temperature": 0,
            "logprobs": True,
            "top_logprobs": 3,
        }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:300]
        print(f"provider at {args.base_url} returned HTTP {exc.code}: {body}")
        return 2
    except urllib.error.URLError as exc:
        print(f"could not reach {args.base_url}: {exc}")
        return 2

    if args.native:
        text = data["message"]["content"]
        tokens = data.get("logprobs") or []
    else:
        choice = data["choices"][0]
        text = choice["message"]["content"]
        tokens = (choice.get("logprobs") or {}).get("content") or []

    print(f"endpoint: {url}")
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
