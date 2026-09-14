# Feature table, dev, free signals only

134 items from dev-v1check, dev-reserve; labels from the graded rows (1 = CORRECT). Every feature below is computed from the agent's own run: the trace it wrote and the texts of the chunks it retrieved. Each is computable at inference time on a question with no known answer, because none reads the item record. The strata block kept next to the features (bucket, evidence retrieved, rank, calculator flag) is ground truth for reporting only.

## Excluded from the features, ground truth

- evidence.retrieved, evidence.rank, evidence.page_retrieved: computed from the item's gold evidence quote.
- bucket: the item's label bucket.
- needs_calculator, spurious_calc: the item's calculator flag and a flag derived from it.
- gold_answer, gold_aliases, readings, premise_fix, expected: the item's reference answer and expected action.

## Provenance and the inference-time statement

| feature | comes from | at inference time |
|---|---|---|
| action_answer | trace.action == ANSWER | yes, from the run |
| action_abstain | trace.action == ABSTAIN | yes, from the run |
| action_clarify | trace.action == CLARIFY | yes, from the run |
| clarify_by_prompt | trace.clarify_by is prompt or both: the model asked on its own | yes, from the run |
| abstain_by_prompt | trace.abstain_by is prompt or both | yes, from the run |
| readings_count | trace.readings.parsed, how many readings the readings step listed | yes, from the run |
| readings_fired | trace.readings.fired | yes, from the run |
| calc_lines | trace.draft.calc, how many CALC lines the draft issued | yes, from the run |
| calc_uncomputable | trace.draft.calc, how many of them the calculator refused | yes, from the run |
| calc_round | trace.calls has a draft_after_calc step | yes, from the run |
| response_words | word count of trace.response | yes, from the run |
| response_content_words | content words in trace.response after the grader's normalise and stopword drop | yes, from the run |
| response_hedges | count of hedge words in trace.response (may, typically, about, ...) | yes, from the run |
| response_abstain_phrase | trace.response matches the grader's abstain pattern | yes, from the run |
| response_form_answer | grader classify_form of trace.response is ANSWER (text only, no hint) | yes, from the run |
| draft_changed_by_calc | trace.draft.raw differs from trace.draft.final | yes, from the run |
| best_score | trace.retrieval[0].score, cosine of the query to the best chunk | yes, from the run |
| score_gap | best score minus the second score | yes, from the run |
| score_mean_k | mean score over the k hits | yes, from the run |
| score_spread | best score minus the kth score | yes, from the run |
| distinct_pages_k | number of distinct start pages among the k hits | yes, from the run |
| page_span_k | max minus min numeric start page among the k hits (0 when fewer than two numeric) | yes, from the run |
| top3_same_page | the top three hits share one start page | yes, from the run |
| lexical_support_top1 | share of the response's content words found in the best chunk (grader's stems and prefixes) | yes, from the run |
| lexical_support_max | the same, maximum over the k chunks | yes, from the run |
| cosine_top1 | bge cosine between the response and the best chunk | yes, from the run |
| cosine_max | bge cosine, maximum over the k chunks | yes, from the run |
| nli_entail_top1 | NLI cross-encoder P(entailment) with the best chunk as premise and the response as hypothesis | yes, from the run |
| nli_entail_max | the same, maximum over the k chunks | yes, from the run |
| nli_contradict_max | NLI P(contradiction), maximum over the k chunks | yes, from the run |

## Mean by label (1 = CORRECT), pooled and in the decisive stratum, then by bucket

Pooled means mix the buckets, and the buckets differ in label rate, so a pooled gap can be a bucket difference. The decisive stratum is answerable items with the evidence retrieved, 33 right against 17 wrong here, where retrieval is held fixed and the model's judgement decides.

| feature | pooled label 1 | pooled label 0 | decisive label 1 | decisive label 0 | answerable | ambiguous | unanswerable | false_premise | constant? |
|---|---|---|---|---|---|---|---|---|---|
| action_answer | 0.514 (sd 0.503) | 0.531 (sd 0.503) | 1.000 (sd 0.000) | 0.471 (sd 0.514) | 0.710 (sd 0.458) | 0.889 (sd 0.333) | 0.000 (sd 0.000) | 0.621 (sd 0.494) |  |
| action_abstain | 0.471 (sd 0.503) | 0.359 (sd 0.484) | 0.000 (sd 0.000) | 0.235 (sd 0.437) | 0.194 (sd 0.398) | 0.000 (sd 0.000) | 0.971 (sd 0.171) | 0.379 (sd 0.494) |  |
| action_clarify | 0.014 (sd 0.120) | 0.109 (sd 0.315) | 0.000 (sd 0.000) | 0.294 (sd 0.470) | 0.097 (sd 0.298) | 0.111 (sd 0.333) | 0.029 (sd 0.171) | 0.000 (sd 0.000) |  |
| clarify_by_prompt | 0.000 (sd 0.000) | 0.000 (sd 0.000) | 0.000 (sd 0.000) | 0.000 (sd 0.000) | 0.000 (sd 0.000) | 0.000 (sd 0.000) | 0.000 (sd 0.000) | 0.000 (sd 0.000) | yes |
| abstain_by_prompt | 0.471 (sd 0.503) | 0.375 (sd 0.488) | 0.000 (sd 0.000) | 0.235 (sd 0.437) | 0.194 (sd 0.398) | 0.000 (sd 0.000) | 1.000 (sd 0.000) | 0.379 (sd 0.494) |  |
| readings_count | 0.557 (sd 0.555) | 0.875 (sd 0.678) | 0.758 (sd 0.502) | 1.176 (sd 0.728) | 0.839 (sd 0.632) | 0.889 (sd 0.601) | 0.353 (sd 0.544) | 0.793 (sd 0.620) |  |
| readings_fired | 0.014 (sd 0.120) | 0.109 (sd 0.315) | 0.000 (sd 0.000) | 0.294 (sd 0.470) | 0.097 (sd 0.298) | 0.111 (sd 0.333) | 0.029 (sd 0.171) | 0.000 (sd 0.000) |  |
| calc_lines | 0.043 (sd 0.204) | 0.125 (sd 0.333) | 0.061 (sd 0.242) | 0.059 (sd 0.243) | 0.097 (sd 0.298) | 0.000 (sd 0.000) | 0.029 (sd 0.171) | 0.138 (sd 0.351) |  |
| calc_uncomputable | 0.029 (sd 0.168) | 0.094 (sd 0.294) | 0.030 (sd 0.174) | 0.000 (sd 0.000) | 0.065 (sd 0.248) | 0.000 (sd 0.000) | 0.029 (sd 0.171) | 0.103 (sd 0.310) |  |
| calc_round | 0.043 (sd 0.204) | 0.125 (sd 0.333) | 0.061 (sd 0.242) | 0.059 (sd 0.243) | 0.097 (sd 0.298) | 0.000 (sd 0.000) | 0.029 (sd 0.171) | 0.138 (sd 0.351) |  |
| response_words | 18.329 (sd 15.128) | 31.703 (sd 25.642) | 25.818 (sd 14.114) | 25.941 (sd 15.258) | 25.242 (sd 15.870) | 34.222 (sd 28.164) | 10.029 (sd 11.101) | 37.862 (sd 29.425) |  |
| response_content_words | 11.771 (sd 8.756) | 19.016 (sd 14.467) | 15.818 (sd 7.986) | 15.118 (sd 7.865) | 15.468 (sd 8.936) | 21.000 (sd 16.109) | 7.147 (sd 7.020) | 22.414 (sd 16.513) |  |
| response_hedges | 0.043 (sd 0.204) | 0.156 (sd 0.407) | 0.091 (sd 0.292) | 0.176 (sd 0.529) | 0.097 (sd 0.349) | 0.222 (sd 0.441) | 0.029 (sd 0.171) | 0.138 (sd 0.351) |  |
| response_abstain_phrase | 0.471 (sd 0.503) | 0.359 (sd 0.484) | 0.000 (sd 0.000) | 0.235 (sd 0.437) | 0.194 (sd 0.398) | 0.000 (sd 0.000) | 0.971 (sd 0.171) | 0.379 (sd 0.494) |  |
| response_form_answer | 0.514 (sd 0.503) | 0.531 (sd 0.503) | 1.000 (sd 0.000) | 0.471 (sd 0.514) | 0.710 (sd 0.458) | 0.889 (sd 0.333) | 0.000 (sd 0.000) | 0.621 (sd 0.494) |  |
| draft_changed_by_calc | 0.043 (sd 0.204) | 0.125 (sd 0.333) | 0.061 (sd 0.242) | 0.059 (sd 0.243) | 0.097 (sd 0.298) | 0.000 (sd 0.000) | 0.029 (sd 0.171) | 0.138 (sd 0.351) |  |
| best_score | 0.730 (sd 0.057) | 0.755 (sd 0.041) | 0.757 (sd 0.052) | 0.767 (sd 0.039) | 0.753 (sd 0.049) | 0.728 (sd 0.035) | 0.705 (sd 0.052) | 0.765 (sd 0.036) |  |
| score_gap | 0.029 (sd 0.024) | 0.021 (sd 0.020) | 0.033 (sd 0.023) | 0.022 (sd 0.018) | 0.026 (sd 0.021) | 0.014 (sd 0.010) | 0.028 (sd 0.026) | 0.025 (sd 0.022) |  |
| score_mean_k | 0.685 (sd 0.053) | 0.716 (sd 0.033) | 0.704 (sd 0.051) | 0.723 (sd 0.029) | 0.708 (sd 0.044) | 0.703 (sd 0.031) | 0.666 (sd 0.049) | 0.720 (sd 0.031) |  |
| score_spread | 0.066 (sd 0.033) | 0.059 (sd 0.035) | 0.078 (sd 0.034) | 0.067 (sd 0.035) | 0.067 (sd 0.035) | 0.039 (sd 0.016) | 0.057 (sd 0.030) | 0.067 (sd 0.039) |  |
| distinct_pages_k | 6.686 (sd 0.941) | 6.594 (sd 0.955) | 6.667 (sd 0.957) | 6.706 (sd 0.772) | 6.645 (sd 0.943) | 6.333 (sd 1.000) | 6.824 (sd 0.936) | 6.517 (sd 0.949) |  |
| page_span_k | 169.557 (sd 74.289) | 151.516 (sd 67.290) | 164.818 (sd 61.433) | 140.000 (sd 78.186) | 154.806 (sd 66.814) | 162.778 (sd 64.379) | 178.324 (sd 87.413) | 153.103 (sd 61.210) |  |
| top3_same_page | 0.014 (sd 0.120) | 0.031 (sd 0.175) | 0.030 (sd 0.174) | 0.000 (sd 0.000) | 0.016 (sd 0.127) | 0.000 (sd 0.000) | 0.000 (sd 0.000) | 0.069 (sd 0.258) |  |
| lexical_support_top1 | 0.465 (sd 0.329) | 0.481 (sd 0.244) | 0.729 (sd 0.215) | 0.488 (sd 0.255) | 0.595 (sd 0.271) | 0.425 (sd 0.112) | 0.202 (sd 0.200) | 0.543 (sd 0.250) |  |
| lexical_support_max | 0.606 (sd 0.267) | 0.612 (sd 0.198) | 0.812 (sd 0.154) | 0.617 (sd 0.180) | 0.709 (sd 0.201) | 0.699 (sd 0.132) | 0.380 (sd 0.170) | 0.635 (sd 0.219) |  |
| cosine_top1 | 0.653 (sd 0.144) | 0.710 (sd 0.120) | 0.766 (sd 0.079) | 0.714 (sd 0.111) | 0.731 (sd 0.104) | 0.717 (sd 0.058) | 0.536 (sd 0.095) | 0.730 (sd 0.136) |  |
| cosine_max | 0.683 (sd 0.128) | 0.741 (sd 0.113) | 0.779 (sd 0.076) | 0.739 (sd 0.090) | 0.749 (sd 0.096) | 0.792 (sd 0.064) | 0.581 (sd 0.084) | 0.755 (sd 0.126) |  |
| nli_entail_top1 | 0.058 (sd 0.101) | 0.077 (sd 0.119) | 0.094 (sd 0.108) | 0.106 (sd 0.122) | 0.092 (sd 0.118) | 0.170 (sd 0.226) | 0.015 (sd 0.030) | 0.043 (sd 0.052) |  |
| nli_entail_max | 0.212 (sd 0.192) | 0.240 (sd 0.212) | 0.327 (sd 0.196) | 0.327 (sd 0.231) | 0.302 (sd 0.220) | 0.263 (sd 0.180) | 0.114 (sd 0.127) | 0.182 (sd 0.170) |  |
| nli_contradict_max | 0.760 (sd 0.291) | 0.618 (sd 0.304) | 0.583 (sd 0.286) | 0.636 (sd 0.293) | 0.625 (sd 0.283) | 0.378 (sd 0.201) | 0.963 (sd 0.090) | 0.615 (sd 0.329) |  |

A gap between the decisive-stratum label columns is the signal that matters. A gap between the bucket columns says the feature may be a bucket detector; the M4 test decides. Constant on dev, to be dropped at M4: clarify_by_prompt.
