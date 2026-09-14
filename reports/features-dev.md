# Feature table, dev with the paid signals

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
| lp_mean | mean token log-probability of the draft (regenerated with logprobs on) | yes, from the run |
| lp_min | minimum token log-probability of the draft | yes, from the run |
| lp_p10 | 10th percentile of the token log-probabilities | yes, from the run |
| lp_share_below_1 | share of tokens with log-probability below -1 (probability under 0.37) | yes, from the run |
| lp_first | log-probability of the first token | yes, from the run |
| lp_tokens | number of tokens in the draft | yes, from the run |
| lp_same_text | 1 when the regenerated draft matched the trace's draft exactly | yes, from the run |
| vc_confidence | the number the model gave when asked, with the passages and its answer in view, how likely its answer is correct (0 to 100; 50 when it gave none) | yes, from the run |
| vc_parsed | 1 when the reply held a number from 0 to 100 | yes, from the run |
| vc_round | 1 when the number is a multiple of 10, the clustering small models show | yes, from the run |
| sa_mean_pairwise | mean content-word Jaccard between pairs of the k samples | yes, from the run |
| sa_min_pairwise | minimum pairwise Jaccard among the k samples | yes, from the run |
| sa_mean_to_draft | mean Jaccard between each sample and the graded draft; the label belongs to the draft | yes, from the run |
| sa_min_to_draft | minimum Jaccard between a sample and the graded draft | yes, from the run |
| sa_max_to_draft | maximum Jaccard between a sample and the graded draft | yes, from the run |
| sa_abstain_share | share of samples that abstain (grader's abstain pattern) | yes, from the run |
| sa_form_agree | share of samples whose abstain-or-not form matches the graded draft | yes, from the run |
| sa_samples | number of samples (k) | yes, from the run |

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
| lp_mean | -0.136 (sd 0.135) | -0.228 (sd 0.175) | -0.180 (sd 0.126) | -0.188 (sd 0.154) | -0.194 (sd 0.141) | -0.253 (sd 0.198) | -0.077 (sd 0.115) | -0.250 (sd 0.183) |  |
| lp_min | -1.268 (sd 1.199) | -1.629 (sd 1.085) | -1.780 (sd 1.083) | -1.376 (sd 1.075) | -1.682 (sd 1.105) | -1.887 (sd 0.964) | -0.595 (sd 0.946) | -1.778 (sd 1.090) |  |
| lp_p10 | -0.517 (sd 0.558) | -0.821 (sd 0.652) | -0.617 (sd 0.493) | -0.679 (sd 0.666) | -0.679 (sd 0.549) | -0.768 (sd 0.567) | -0.357 (sd 0.574) | -0.952 (sd 0.701) |  |
| lp_share_below_1 | 0.045 (sd 0.057) | 0.072 (sd 0.078) | 0.060 (sd 0.055) | 0.057 (sd 0.064) | 0.066 (sd 0.064) | 0.078 (sd 0.095) | 0.020 (sd 0.047) | 0.081 (sd 0.077) |  |
| lp_first | -0.119 (sd 0.228) | -0.227 (sd 0.258) | -0.162 (sd 0.236) | -0.276 (sd 0.282) | -0.206 (sd 0.276) | -0.357 (sd 0.242) | -0.059 (sd 0.148) | -0.167 (sd 0.231) |  |
| lp_tokens | 25.543 (sd 22.834) | 31.266 (sd 26.006) | 34.667 (sd 21.163) | 26.353 (sd 16.248) | 30.710 (sd 20.953) | 46.778 (sd 34.931) | 13.147 (sd 15.414) | 35.069 (sd 28.491) |  |
| lp_same_text | 0.714 (sd 0.455) | 0.625 (sd 0.488) | 0.606 (sd 0.496) | 0.588 (sd 0.507) | 0.613 (sd 0.491) | 0.333 (sd 0.500) | 0.882 (sd 0.327) | 0.655 (sd 0.484) |  |
| vc_confidence | 56.929 (sd 48.209) | 74.219 (sd 38.237) | 100.000 (sd 0.000) | 83.235 (sd 33.863) | 86.290 (sd 31.152) | 98.333 (sd 5.000) | 7.353 (sd 17.975) | 77.586 (sd 36.219) |  |
| vc_parsed | 1.000 (sd 0.000) | 0.984 (sd 0.125) | 1.000 (sd 0.000) | 1.000 (sd 0.000) | 0.984 (sd 0.127) | 1.000 (sd 0.000) | 1.000 (sd 0.000) | 1.000 (sd 0.000) |  |
| vc_round | 0.986 (sd 0.120) | 0.891 (sd 0.315) | 1.000 (sd 0.000) | 0.941 (sd 0.243) | 0.952 (sd 0.216) | 0.889 (sd 0.333) | 1.000 (sd 0.000) | 0.862 (sd 0.351) |  |
| sa_mean_pairwise | 0.615 (sd 0.284) | 0.440 (sd 0.245) | 0.529 (sd 0.237) | 0.538 (sd 0.278) | 0.520 (sd 0.264) | 0.318 (sd 0.102) | 0.705 (sd 0.303) | 0.416 (sd 0.207) |  |
| sa_min_pairwise | 0.445 (sd 0.375) | 0.241 (sd 0.286) | 0.352 (sd 0.274) | 0.318 (sd 0.330) | 0.333 (sd 0.307) | 0.145 (sd 0.076) | 0.539 (sd 0.447) | 0.216 (sd 0.249) |  |
| sa_mean_to_draft | 0.687 (sd 0.252) | 0.472 (sd 0.267) | 0.603 (sd 0.230) | 0.531 (sd 0.314) | 0.561 (sd 0.273) | 0.423 (sd 0.147) | 0.775 (sd 0.260) | 0.461 (sd 0.231) |  |
| sa_min_to_draft | 0.471 (sd 0.363) | 0.252 (sd 0.284) | 0.396 (sd 0.273) | 0.321 (sd 0.324) | 0.354 (sd 0.306) | 0.182 (sd 0.086) | 0.553 (sd 0.434) | 0.231 (sd 0.253) |  |
| sa_max_to_draft | 0.889 (sd 0.180) | 0.709 (sd 0.283) | 0.851 (sd 0.184) | 0.703 (sd 0.309) | 0.782 (sd 0.254) | 0.742 (sd 0.288) | 0.931 (sd 0.171) | 0.717 (sd 0.264) |  |
| sa_abstain_share | 0.466 (sd 0.453) | 0.362 (sd 0.368) | 0.048 (sd 0.087) | 0.165 (sd 0.226) | 0.181 (sd 0.280) | 0.111 (sd 0.267) | 0.935 (sd 0.145) | 0.407 (sd 0.357) |  |
| sa_form_agree | 0.926 (sd 0.149) | 0.794 (sd 0.259) | 0.952 (sd 0.087) | 0.765 (sd 0.310) | 0.852 (sd 0.237) | 0.889 (sd 0.267) | 0.935 (sd 0.145) | 0.793 (sd 0.217) |  |
| sa_samples | 5.000 (sd 0.000) | 5.000 (sd 0.000) | 5.000 (sd 0.000) | 5.000 (sd 0.000) | 5.000 (sd 0.000) | 5.000 (sd 0.000) | 5.000 (sd 0.000) | 5.000 (sd 0.000) | yes |

## Cost of the paid signals, per item

| run | signal | items | seconds per item | wall clock | calls from cache |
|---|---|---|---|---|---|
| dev-v1check-signals | logprobs | 100 | 12.44 | 1244 s | 1 |
| dev-v1check-signals | verbalized | 100 | 2.75 | 275 s | 67 |
| dev-v1check-signals | samples (k=5) | 100 | 23.19 | 2319 s | 0 |
| dev-reserve-signals | logprobs | 34 | 14.56 | 495 s | 0 |
| dev-reserve-signals | verbalized | 34 | 8.14 | 277 s | 0 |
| dev-reserve-signals | samples (k=5) | 34 | 22.71 | 772 s | 0 |

Sampling agreement is lexical (the grader's normalise, stopwords and stems), so paraphrases read as disagreement and the signal partly measures lexical variance; the raw samples are stored so M4 can try another agreement function without resampling. The confidence follow-up sees the passages and the draft. The log-probability sequence is stored raw per draft.

A gap between the decisive-stratum label columns is the signal that matters. A gap between the bucket columns says the feature may be a bucket detector; the M4 test decides. Constant on dev, to be dropped at M4: clarify_by_prompt, sa_samples.
