"""Tests for the model provider and its disk cache."""

import json

import pytest

from agent.provider import Generation, OllamaProvider

NATIVE_RESPONSE = {
    "model": "qwen2.5:3b-instruct",
    "message": {"role": "assistant", "content": "Earth"},
    "done": True,
    "logprobs": [
        {
            "token": "Earth",
            "logprob": -0.25,
            "top_logprobs": [{"token": "Earth", "logprob": -0.25}, {"token": "Mars", "logprob": -1.5}],
        }
    ],
    "eval_count": 2,
}

MESSAGES = [{"role": "user", "content": "Name one planet."}]


class FakeTransport:
    def __init__(self, response=None, error=None):
        self.calls = []
        self.response = response or NATIVE_RESPONSE
        self.error = error

    def __call__(self, url, body):
        self.calls.append((url, body))
        if self.error:
            raise self.error
        return json.loads(json.dumps(self.response))


@pytest.fixture
def provider(tmp_path):
    transport = FakeTransport()
    p = OllamaProvider(
        model="qwen2.5:3b-instruct",
        base_url="http://fake:11434",
        cache_dir=tmp_path,
        transport=transport,
        num_ctx=4096,
    )
    return p, transport


def test_generate_parses_text_and_logprobs(provider):
    p, _ = provider
    g = p.generate(MESSAGES, temperature=0.0, seed=42, logprobs=True, top_logprobs=2)
    assert isinstance(g, Generation)
    assert g.text == "Earth"
    assert g.tokens == ["Earth"]
    assert g.logprobs == [-0.25]
    assert g.top_logprobs == [[("Earth", -0.25), ("Mars", -1.5)]]
    assert g.model == "qwen2.5:3b-instruct"
    assert g.cached is False


def test_identical_call_is_served_from_cache(provider):
    p, transport = provider
    first = p.generate(MESSAGES, temperature=0.0, seed=42)
    second = p.generate(MESSAGES, temperature=0.0, seed=42)
    assert len(transport.calls) == 1
    assert second.text == first.text
    assert second.cached is True


def test_cache_survives_a_new_provider_instance(tmp_path):
    t1 = FakeTransport()
    OllamaProvider(model="m", base_url="http://fake:11434", cache_dir=tmp_path, transport=t1).generate(MESSAGES)
    t2 = FakeTransport()
    g = OllamaProvider(model="m", base_url="http://fake:11434", cache_dir=tmp_path, transport=t2).generate(MESSAGES)
    assert len(t2.calls) == 0
    assert g.cached is True


def test_cache_key_depends_on_seed_and_temperature(provider):
    p, transport = provider
    p.generate(MESSAGES, temperature=0.0, seed=42)
    p.generate(MESSAGES, temperature=0.0, seed=43)
    p.generate(MESSAGES, temperature=0.7, seed=42)
    assert len(transport.calls) == 3


def test_cache_file_records_request_and_response(provider, tmp_path):
    p, _ = provider
    p.generate(MESSAGES, seed=3)
    stored = json.loads(next(tmp_path.rglob("*.json")).read_text(encoding="utf-8"))
    assert stored["request"]["options"]["seed"] == 3
    assert stored["response"]["message"]["content"] == "Earth"


def test_request_body_carries_options(provider):
    p, transport = provider
    p.generate(MESSAGES, temperature=0.7, seed=7, max_tokens=33, logprobs=True, top_logprobs=3)
    url, body = transport.calls[0]
    assert url == "http://fake:11434/api/chat"
    assert body["model"] == "qwen2.5:3b-instruct"
    assert body["messages"] == MESSAGES
    assert body["stream"] is False
    assert body["logprobs"] is True
    assert body["top_logprobs"] == 3
    assert body["options"]["seed"] == 7
    assert body["options"]["temperature"] == 0.7
    assert body["options"]["num_predict"] == 33
    assert body["options"]["num_ctx"] == 4096


def test_transport_error_propagates_and_is_not_cached(tmp_path):
    transport = FakeTransport(error=ConnectionError("down"))
    p = OllamaProvider(model="m", base_url="http://fake:11434", cache_dir=tmp_path, transport=transport)
    with pytest.raises(ConnectionError):
        p.generate(MESSAGES)
    assert not list(tmp_path.rglob("*.json"))


def test_malformed_reply_raises_and_is_not_cached(tmp_path):
    transport = FakeTransport(response={"model": "m", "done": True, "error": "something"})
    p = OllamaProvider(model="m", base_url="http://fake:11434", cache_dir=tmp_path, transport=transport)
    with pytest.raises(ValueError):
        p.generate(MESSAGES)
    assert not list(tmp_path.rglob("*.json"))


def test_truncated_cache_file_is_refetched_and_rewritten(provider, tmp_path):
    p, transport = provider
    p.generate(MESSAGES)
    cached = next(tmp_path.rglob("*.json"))
    cached.write_text('{"request": {}, "resp', encoding="utf-8")
    g = p.generate(MESSAGES)
    assert len(transport.calls) == 2
    assert g.cached is False
    assert json.loads(cached.read_text(encoding="utf-8"))["response"]["message"]["content"] == "Earth"
    assert not list(tmp_path.rglob("*.tmp"))


def test_logprobs_absent_when_not_requested(provider):
    p, transport = provider
    transport.response = {"model": "m", "message": {"role": "assistant", "content": "Earth"}, "done": True}
    g = p.generate(MESSAGES, logprobs=False)
    assert g.logprobs is None
    assert g.tokens is None
    assert g.top_logprobs is None
