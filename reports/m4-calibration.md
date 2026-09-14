# M4 calibration on dev

134 dev items, stratified 5-fold cross-validation with seed 42; every number is out of fold. Intervals are 95 percent bootstrap over items, 1000 resamples. Strata: pooled (134), answerable (62), decisive (50: answerable with the evidence chunk retrieved, 33 right against 17 wrong). The decisive stratum is the real test: retrieval is held fixed there and the model's judgement decides the outcome. With dev this size the conclusions are directional, not precise. The test split was not read.

## Leakage list

Features admitted, all computed from the run (trace and retrieved chunk texts), each computable at inference time on a question with no known answer. Ground truth kept out: bucket, evidence retrieved and rank, calculator flags, gold answer, expected action. Constant on dev and dropped: clarify_by_prompt, sa_samples.

- action_answer [action]: trace.action == ANSWER
- action_abstain [action]: trace.action == ABSTAIN
- action_clarify [action]: trace.action == CLARIFY
- abstain_by_prompt [action]: trace.abstain_by is prompt or both
- readings_count: trace.readings.parsed, how many readings the readings step listed
- readings_fired [action]: trace.readings.fired
- calc_lines: trace.draft.calc, how many CALC lines the draft issued
- calc_uncomputable: trace.draft.calc, how many of them the calculator refused
- calc_round: trace.calls has a draft_after_calc step
- response_words: word count of trace.response
- response_content_words: content words in trace.response after the grader's normalise and stopword drop
- response_hedges: count of hedge words in trace.response (may, typically, about, ...)
- response_abstain_phrase [action]: trace.response matches the grader's abstain pattern
- response_form_answer [action]: grader classify_form of trace.response is ANSWER (text only, no hint)
- draft_changed_by_calc: trace.draft.raw differs from trace.draft.final
- best_score: trace.retrieval[0].score, cosine of the query to the best chunk
- score_gap: best score minus the second score
- score_mean_k: mean score over the k hits
- score_spread: best score minus the kth score
- distinct_pages_k: number of distinct start pages among the k hits
- page_span_k: max minus min numeric start page among the k hits (0 when fewer than two numeric)
- top3_same_page: the top three hits share one start page
- lexical_support_top1: share of the response's content words found in the best chunk (grader's stems and prefixes)
- lexical_support_max: the same, maximum over the k chunks
- cosine_top1: bge cosine between the response and the best chunk
- cosine_max: bge cosine, maximum over the k chunks
- nli_entail_top1: NLI cross-encoder P(entailment) with the best chunk as premise and the response as hypothesis
- nli_entail_max: the same, maximum over the k chunks
- nli_contradict_max: NLI P(contradiction), maximum over the k chunks
- lp_mean [logprob]: mean token log-probability of the draft (regenerated with logprobs on)
- lp_min [logprob]: minimum token log-probability of the draft
- lp_p10 [logprob]: 10th percentile of the token log-probabilities
- lp_share_below_1 [logprob]: share of tokens with log-probability below -1 (probability under 0.37)
- lp_first [logprob]: log-probability of the first token
- lp_tokens [logprob]: number of tokens in the draft
- lp_same_text [logprob]: 1 when the regenerated draft matched the trace's draft exactly
- vc_confidence: the number the model gave when asked, with the passages and its answer in view, how likely its answer is correct (0 to 100; 50 when it gave none)
- vc_parsed: 1 when the reply held a number from 0 to 100
- vc_round: 1 when the number is a multiple of 10, the clustering small models show
- sa_mean_pairwise: mean content-word Jaccard between pairs of the k samples
- sa_min_pairwise: minimum pairwise Jaccard among the k samples
- sa_mean_to_draft: mean Jaccard between each sample and the graded draft; the label belongs to the draft
- sa_min_to_draft: minimum Jaccard between a sample and the graded draft
- sa_max_to_draft: maximum Jaccard between a sample and the graded draft
- sa_abstain_share: share of samples that abstain (grader's abstain pattern)
- sa_form_agree: share of samples whose abstain-or-not form matches the graded draft

## Results, out of fold

Lower is better for ECE, Brier and AURC; higher for AUROC. The base rate row is a constant prediction at the dev label rate.

### full (46 features)

| fit | stratum | ECE | Brier | AUROC | AURC |
|---|---|---|---|---|---|
| base rate | pooled | 0.000 [0.000, 0.097] | 0.249 [0.246, 0.253] | 0.500 [0.500, 0.500] | 0.397 [0.357, 0.594] |
| base rate | answerable | 0.058 [0.006, 0.171] | 0.247 [0.242, 0.253] | 0.500 [0.500, 0.500] | 0.380 [0.254, 0.601] |
| base rate | decisive | 0.138 [0.018, 0.258] | 0.243 [0.238, 0.250] | 0.500 [0.500, 0.500] | 0.333 [0.180, 0.527] |
| logistic | pooled | 0.173 [0.124, 0.253] | 0.226 [0.179, 0.275] | 0.731 [0.642, 0.815] | 0.298 [0.210, 0.400] |
| logistic | answerable | 0.241 [0.175, 0.377] | 0.256 [0.184, 0.337] | 0.690 [0.544, 0.814] | 0.269 [0.155, 0.422] |
| logistic | decisive | 0.259 [0.181, 0.366] | 0.217 [0.140, 0.291] | 0.763 [0.621, 0.899] | 0.177 [0.072, 0.317] |
| logistic+isotonic | pooled | 0.089 [0.070, 0.186] | 0.213 [0.184, 0.244] | 0.724 [0.634, 0.805] | 0.300 [0.210, 0.406] |
| logistic+isotonic | answerable | 0.131 [0.099, 0.269] | 0.229 [0.184, 0.275] | 0.668 [0.530, 0.797] | 0.280 [0.168, 0.434] |
| logistic+isotonic | decisive | 0.159 [0.108, 0.279] | 0.211 [0.165, 0.260] | 0.695 [0.534, 0.843] | 0.203 [0.091, 0.355] |

Largest coefficients of the full-dev logistic fit (standardised features): lp_tokens +1.15, lp_min -0.82, sa_mean_to_draft +0.80, response_words -0.80, sa_mean_pairwise -0.80, nli_entail_max +0.72, readings_count -0.62, response_content_words -0.57.

### minus_actions (39 features)

| fit | stratum | ECE | Brier | AUROC | AURC |
|---|---|---|---|---|---|
| base rate | pooled | 0.000 [0.000, 0.097] | 0.249 [0.246, 0.253] | 0.500 [0.500, 0.500] | 0.397 [0.357, 0.594] |
| base rate | answerable | 0.058 [0.006, 0.171] | 0.247 [0.242, 0.253] | 0.500 [0.500, 0.500] | 0.380 [0.254, 0.601] |
| base rate | decisive | 0.138 [0.018, 0.258] | 0.243 [0.238, 0.250] | 0.500 [0.500, 0.500] | 0.333 [0.180, 0.527] |
| logistic | pooled | 0.147 [0.102, 0.236] | 0.227 [0.183, 0.276] | 0.727 [0.636, 0.809] | 0.296 [0.206, 0.401] |
| logistic | answerable | 0.258 [0.177, 0.383] | 0.272 [0.202, 0.347] | 0.656 [0.508, 0.788] | 0.277 [0.164, 0.419] |
| logistic | decisive | 0.229 [0.159, 0.355] | 0.238 [0.168, 0.311] | 0.726 [0.570, 0.859] | 0.180 [0.083, 0.315] |
| logistic+isotonic | pooled | 0.072 [0.060, 0.169] | 0.207 [0.177, 0.239] | 0.733 [0.647, 0.814] | 0.290 [0.207, 0.387] |
| logistic+isotonic | answerable | 0.123 [0.097, 0.260] | 0.233 [0.186, 0.284] | 0.664 [0.515, 0.790] | 0.274 [0.161, 0.428] |
| logistic+isotonic | decisive | 0.159 [0.101, 0.291] | 0.216 [0.166, 0.270] | 0.710 [0.556, 0.852] | 0.189 [0.089, 0.337] |

Largest coefficients of the full-dev logistic fit (standardised features): lp_tokens +0.97, readings_count -0.88, sa_mean_to_draft +0.86, lp_min -0.79, sa_mean_pairwise -0.79, response_words -0.75, nli_entail_max +0.56, cosine_max -0.54.

### minus_logprobs (39 features)

| fit | stratum | ECE | Brier | AUROC | AURC |
|---|---|---|---|---|---|
| base rate | pooled | 0.000 [0.000, 0.097] | 0.249 [0.246, 0.253] | 0.500 [0.500, 0.500] | 0.397 [0.357, 0.594] |
| base rate | answerable | 0.058 [0.006, 0.171] | 0.247 [0.242, 0.253] | 0.500 [0.500, 0.500] | 0.380 [0.254, 0.601] |
| base rate | decisive | 0.138 [0.018, 0.258] | 0.243 [0.238, 0.250] | 0.500 [0.500, 0.500] | 0.333 [0.180, 0.527] |
| logistic | pooled | 0.140 [0.111, 0.246] | 0.239 [0.194, 0.289] | 0.685 [0.589, 0.775] | 0.322 [0.232, 0.422] |
| logistic | answerable | 0.185 [0.142, 0.333] | 0.265 [0.203, 0.333] | 0.633 [0.497, 0.768] | 0.306 [0.174, 0.470] |
| logistic | decisive | 0.186 [0.128, 0.327] | 0.236 [0.173, 0.309] | 0.656 [0.472, 0.810] | 0.226 [0.100, 0.388] |
| logistic+isotonic | pooled | 0.098 [0.069, 0.185] | 0.219 [0.189, 0.251] | 0.700 [0.607, 0.786] | 0.313 [0.227, 0.420] |
| logistic+isotonic | answerable | 0.127 [0.084, 0.257] | 0.239 [0.197, 0.285] | 0.621 [0.473, 0.762] | 0.308 [0.181, 0.472] |
| logistic+isotonic | decisive | 0.178 [0.115, 0.312] | 0.219 [0.178, 0.263] | 0.634 [0.446, 0.798] | 0.243 [0.112, 0.420] |

Largest coefficients of the full-dev logistic fit (standardised features): sa_min_to_draft +0.79, readings_count -0.60, sa_mean_pairwise -0.60, nli_entail_max +0.57, calc_uncomputable +0.54, score_gap +0.49, sa_mean_to_draft +0.48, cosine_top1 -0.41.

## Reliability, logistic+isotonic, full variant

pooled:

| bin | n | mean confidence | accuracy |
|---|---|---|---|
| 0.0 to 0.1 | 1 | 0.0 | 0.0 |
| 0.1 to 0.2 | 12 | 0.156 | 0.333 |
| 0.2 to 0.3 | 16 | 0.279 | 0.125 |
| 0.3 to 0.4 | 4 | 0.375 | 0.25 |
| 0.4 to 0.5 | 24 | 0.436 | 0.5 |
| 0.5 to 0.6 | 36 | 0.545 | 0.611 |
| 0.6 to 0.7 | 17 | 0.656 | 0.647 |
| 0.7 to 0.8 | 7 | 0.771 | 0.429 |
| 0.8 to 0.9 | 11 | 0.853 | 0.818 |
| 0.9 to 1.0 | 6 | 0.991 | 1.0 |

answerable:

| bin | n | mean confidence | accuracy |
|---|---|---|---|
| 0.0 to 0.1 | 1 | 0.0 | 0.0 |
| 0.1 to 0.2 | 6 | 0.162 | 0.5 |
| 0.2 to 0.3 | 8 | 0.279 | 0.25 |
| 0.3 to 0.4 | 2 | 0.375 | 0.5 |
| 0.4 to 0.5 | 10 | 0.441 | 0.7 |
| 0.5 to 0.6 | 18 | 0.535 | 0.556 |
| 0.6 to 0.7 | 8 | 0.654 | 0.75 |
| 0.7 to 0.8 | 2 | 0.785 | 0.0 |
| 0.8 to 0.9 | 2 | 0.864 | 1.0 |
| 0.9 to 1.0 | 5 | 0.989 | 1.0 |

decisive:

| bin | n | mean confidence | accuracy |
|---|---|---|---|
| 0.0 to 0.1 | 1 | 0.0 | 0.0 |
| 0.1 to 0.2 | 4 | 0.156 | 0.25 |
| 0.2 to 0.3 | 5 | 0.286 | 0.4 |
| 0.3 to 0.4 | 1 | 0.375 | 1.0 |
| 0.4 to 0.5 | 8 | 0.439 | 0.875 |
| 0.5 to 0.6 | 15 | 0.532 | 0.6 |
| 0.6 to 0.7 | 8 | 0.654 | 0.75 |
| 0.7 to 0.8 | 1 | 0.792 | 0.0 |
| 0.8 to 0.9 | 2 | 0.864 | 1.0 |
| 0.9 to 1.0 | 5 | 0.989 | 1.0 |

## Bucket-detector test

A multinomial logistic fit from the full feature vector to the bucket, out of fold: accuracy 0.59 [0.5, 0.672] against a majority-bucket prior of 0.463. Per-bucket recall: answerable 0.661, ambiguous 0.111, unanswerable 0.794, false_premise 0.345.

If the features predict the bucket well and the pooled calibration numbers do not survive inside the decisive stratum, the calibrator is a bucket detector.

