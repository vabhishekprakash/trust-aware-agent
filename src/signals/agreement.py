"""Sampling agreement: k resampled drafts against each other and against the graded draft.

Agreement is lexical on purpose, the grader's own normalise, stopword drop
and stems, so the signal shares no machinery with the judge. The cost is
that paraphrases read as disagreement, so the signal partly measures
lexical variance. The raw samples are stored with the run so a different
agreement function can be tried without resampling.
"""

from __future__ import annotations

from itertools import combinations

from calibration.grader import _ABSTAIN, content_words

PROVENANCE = {
    "sa_mean_pairwise": "mean content-word Jaccard between pairs of the k samples",
    "sa_min_pairwise": "minimum pairwise Jaccard among the k samples",
    "sa_mean_to_draft": "mean Jaccard between each sample and the graded draft; the label belongs to the draft",
    "sa_min_to_draft": "minimum Jaccard between a sample and the graded draft",
    "sa_max_to_draft": "maximum Jaccard between a sample and the graded draft",
    "sa_abstain_share": "share of samples that abstain (grader's abstain pattern)",
    "sa_form_agree": "share of samples whose abstain-or-not form matches the graded draft",
    "sa_samples": "number of samples (k)",
}


def jaccard(a: str, b: str) -> float:
    wa, wb = content_words(a), content_words(b)
    if not wa and not wb:
        return 1.0
    return round(len(wa & wb) / len(wa | wb), 4) if (wa | wb) else 0.0


def agreement_features(samples: list[str], draft: str) -> dict:
    if not samples:
        return {k: 0.0 for k in PROVENANCE} | {"sa_samples": 0}
    pairs = [jaccard(a, b) for a, b in combinations(samples, 2)] or [1.0]
    to_draft = [jaccard(s, draft) for s in samples]
    draft_abstains = bool(_ABSTAIN.search(draft))
    forms = [bool(_ABSTAIN.search(s)) for s in samples]
    return {
        "sa_mean_pairwise": round(sum(pairs) / len(pairs), 4),
        "sa_min_pairwise": round(min(pairs), 4),
        "sa_mean_to_draft": round(sum(to_draft) / len(to_draft), 4),
        "sa_min_to_draft": round(min(to_draft), 4),
        "sa_max_to_draft": round(max(to_draft), 4),
        "sa_abstain_share": round(sum(forms) / len(forms), 4),
        "sa_form_agree": round(sum(1 for f in forms if f == draft_abstains) / len(forms), 4),
        "sa_samples": len(samples),
    }
