"""Retrieval support: is the response backed by the passages the agent retrieved?

Three views, all computable at inference time from the response and the
retrieved chunk texts. Lexical: the share of the response's content words
found in a chunk. Embedding: cosine between the response and a chunk in the
same bge space the retriever uses. Entailment: a small NLI cross-encoder's
probability that a chunk entails the response. Each is taken against the
best-scored chunk and as the maximum over the k chunks.
"""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from calibration.grader import content_words, shared_words

PROVENANCE = {
    "lexical_support_top1": "share of the response's content words found in the best chunk (grader's stems and prefixes)",
    "lexical_support_max": "the same, maximum over the k chunks",
    "cosine_top1": "bge cosine between the response and the best chunk",
    "cosine_max": "bge cosine, maximum over the k chunks",
    "nli_entail_top1": "NLI cross-encoder P(entailment) with the best chunk as premise and the response as hypothesis",
    "nli_entail_max": "the same, maximum over the k chunks",
    "nli_contradict_max": "NLI P(contradiction), maximum over the k chunks",
}

NLI_MODEL = "cross-encoder/nli-MiniLM2-L6-H768"
NLI_LABELS = ("contradiction", "entailment", "neutral")


def lexical_support(response: str, chunk_text: str) -> float:
    words = len(content_words(response))
    return round(shared_words(response, chunk_text) / words, 4) if words else 0.0


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return round(float(a @ b) / denom, 4) if denom else 0.0


def nli_model(name: str = NLI_MODEL):
    """The cross-encoder, loaded on first use; None when it cannot be loaded (reported by the caller)."""
    try:
        from sentence_transformers import CrossEncoder

        return CrossEncoder(name, max_length=512)
    except Exception:  # noqa: BLE001 - the caller reports which signals are missing
        return None


def nli_probabilities(model, pairs: list[tuple[str, str]]) -> list[dict]:
    logits = np.asarray(model.predict(pairs, apply_softmax=True))
    return [{label: round(float(p), 4) for label, p in zip(NLI_LABELS, row)} for row in logits]


def support_features(response: str, chunk_texts: list[str], embed: Optional[Callable[[list[str]], np.ndarray]] = None,
                     chunk_vectors: Optional[np.ndarray] = None, nli=None) -> dict:
    """Features for one response against its k retrieved chunks, in retrieval order.

    `embed` maps texts to vectors; `chunk_vectors` are the chunks' stored
    vectors when the caller has them, otherwise the chunks are embedded.
    Signals whose model is unavailable are left out rather than zeroed.
    """
    out = {}
    if chunk_texts:
        lexical = [lexical_support(response, c) for c in chunk_texts]
        out["lexical_support_top1"] = lexical[0]
        out["lexical_support_max"] = max(lexical)
    if embed is not None and chunk_texts:
        r = embed([response])[0]
        vectors = chunk_vectors if chunk_vectors is not None else embed(chunk_texts)
        cos = [cosine(r, v) for v in vectors]
        out["cosine_top1"] = cos[0]
        out["cosine_max"] = max(cos)
    if nli is not None and chunk_texts:
        probs = nli_probabilities(nli, [(c, response) for c in chunk_texts])
        out["nli_entail_top1"] = probs[0]["entailment"]
        out["nli_entail_max"] = max(p["entailment"] for p in probs)
        out["nli_contradict_max"] = max(p["contradiction"] for p in probs)
    return out
