# Dry run on dev (not the test read)

Preregistered in reports/m8-preregistration.md. Frozen: {"agent_commit": "85db315", "artifact_sha256": "58f3f3d1cba468861b8b5094dae334b270c7fbbdff946fac1a801ad3e1d90116", "policy_sha256": "767fea22e942067807041787901d05347959d921a32c66365fc496b2e3bc3821", "split_sha256": "b3180fd19227df17e81dbbf9ca3300f6b230aee370af63afc9de6ee0cd69d4f0", "grader": "grader-v13", "grader_sha256": "a2eb938e82b0b63fa8a00c834e0569924e80b0a966ac1663b2ed9ca4986ad485"}.
134 items; strata counts {'pooled': 134, 'answerable': 62, 'decisive': 50}; correct per stratum {'pooled': 70, 'answerable': 36, 'decisive': 33}. Wall clock 177 s (loop 4, confidence 0, sampling 0, grading 0).

Attempts (a crashed attempt leaves a start line and replays from the cache): 0.

## Audit, run regardless of band

- Provenance: every feature name in the rows is in the provenance lists and none is a ground-truth field (asserted).
- Split: seed 42, scripts/lock_and_split.py, stratified by bucket, halves per bucket; test counts found {'answerable': 62, 'ambiguous': 9, 'unanswerable': 34, 'false_premise': 29}, expected {'answerable': 46, 'ambiguous': 9, 'unanswerable': 25, 'false_premise': 20}.
- Near-duplicates across dev and test (Jaccard >= 0.6, cosine >= 0.9, or same evidence page with cosine >= 0.8): 18 flagged.
  - q0011 / q0096 (same evidence page and cosine >= 0.8 with q0096): "For space flight projects, into how many incremental phases are the Formulation and Implementation life-cycle phases broken down?" against "How many phases make up the NASA life cycle?"
  - q0032 / q0209 (cosine 0.90 with q0209; same evidence page and cosine >= 0.8 with q0209): "Into how many steps does the handbook break the validation of technical requirements?" against "The handbook breaks requirements validation into four steps; what does the fourth and final step check for?"
  - q0046 / q0216 (same evidence page and cosine >= 0.8 with q0216): "In the comparison of verification and validation testing, which document does validation testing trace back to?" against "The handbook ties verification testing back to the ConOps document, so which document does it tie validation testing back to?"
  - q0053 / q0221 (same evidence page and cosine >= 0.8 with q0221): "For a system with several production units, what does the handbook say should be used instead of continued verification and validation to make sure the units after the first one meet stakeholder expectations?" against "For a system with several production units, the handbook says to keep running the full verification and validation processes on every unit after the first deliverable. What does it give as the reason for repeating them?"
  - q0058 / q0224 (same evidence page and cosine >= 0.8 with q0224): "In the handbook's description of technical planning, what is the SEMP's standing relative to the project plan?" against "Because the project plan is a subordinate document to the SEMP, what does the handbook say the project plan is allowed to define on its own?"
  - q0068 / q0077 (same evidence page and cosine >= 0.8 with q0077): "Once the requirements baseline is under formal configuration control after the SRR, what body must approve a change to it?" against "Who normally approves a change to project information that is held under configuration control?"
  - q0096 / q0011 (same evidence page and cosine >= 0.8 with q0011): "How many phases make up the NASA life cycle?" against "For space flight projects, into how many incremental phases are the Formulation and Implementation life-cycle phases broken down?"
  - q0209 / q0032 (cosine 0.90 with q0032; same evidence page and cosine >= 0.8 with q0032): "The handbook breaks requirements validation into four steps; what does the fourth and final step check for?" against "Into how many steps does the handbook break the validation of technical requirements?"
  - q0221 / q0053 (same evidence page and cosine >= 0.8 with q0053): "For a system with several production units, the handbook says to keep running the full verification and validation processes on every unit after the first deliverable. What does it give as the reason for repeating them?" against "For a system with several production units, what does the handbook say should be used instead of continued verification and validation to make sure the units after the first one meet stakeholder expectations?"
  - q0224 / q0058 (same evidence page and cosine >= 0.8 with q0058): "Because the project plan is a subordinate document to the SEMP, what does the handbook say the project plan is allowed to define on its own?" against "In the handbook's description of technical planning, what is the SEMP's standing relative to the project plan?"
  - q0227 / q0063 (same evidence page and cosine >= 0.8 with q0063): "Given that the verification plan is baselined at the Critical Design Review, what kinds of updates to it are allowed after that point?" against "Which milestone review is the verification plan baselined at?"
  - q0051 / q0218 (same evidence page and cosine >= 0.8 with q0218): "How many major steps make up the Product Validation Process according to the handbook?" against "The handbook breaks product validation into three major steps. Which of the three involves writing the validation report?"
  - q0063 / q0227 (same evidence page and cosine >= 0.8 with q0227): "Which milestone review is the verification plan baselined at?" against "Given that the verification plan is baselined at the Critical Design Review, what kinds of updates to it are allowed after that point?"
  - q0077 / q0068 (same evidence page and cosine >= 0.8 with q0068): "Who normally approves a change to project information that is held under configuration control?" against "Once the requirements baseline is under formal configuration control after the SRR, what body must approve a change to it?"
  - q0187 / q0188 (same evidence page and cosine >= 0.8 with q0188): "In what year was NPR 7123.1 first put into effect?" against "In what year was NPR 7123.1, NASA Systems Engineering Processes and Requirements, first issued?"
  - q0188 / q0187 (same evidence page and cosine >= 0.8 with q0187): "In what year was NPR 7123.1, NASA Systems Engineering Processes and Requirements, first issued?" against "In what year was NPR 7123.1 first put into effect?"
  - q0216 / q0046 (same evidence page and cosine >= 0.8 with q0046): "The handbook ties verification testing back to the ConOps document, so which document does it tie validation testing back to?" against "In the comparison of verification and validation testing, which document does validation testing trace back to?"
  - q0218 / q0051 (same evidence page and cosine >= 0.8 with q0051): "The handbook breaks product validation into three major steps. Which of the three involves writing the validation report?" against "How many major steps make up the Product Validation Process according to the handbook?"

## Headline: the confirmed vector

| stratum | n | correct | AUROC | Brier | ECE (10 bins) | AURC |
|---|---|---|---|---|---|---|
| pooled | 134 | 70 | 0.818 [0.753, 0.878] | 0.185 [0.164, 0.206] | 0.081 [0.041, 0.151] | 0.208 [0.168, 0.328] |
| answerable | 62 | 36 | 0.785 [0.683, 0.879] | 0.199 [0.166, 0.232] | 0.124 [0.045, 0.223] | 0.192 [0.124, 0.365] |
| decisive | 50 | 33 | 0.838 [0.728, 0.938] | 0.182 [0.147, 0.216] | 0.179 [0.090, 0.290] | 0.129 [0.056, 0.269] |

With the flagged near-duplicate items removed:

| stratum | AUROC | Brier |
|---|---|---|
| pooled | 0.827 [0.749, 0.889] | 0.181 [0.158, 0.205] |
| answerable | 0.794 [0.683, 0.898] | 0.191 [0.156, 0.226] |
| decisive | 0.845 [0.708, 0.959] | 0.168 [0.136, 0.205] |

Policy on the 70 answered items (36 correct):

| operating point | coverage % | risk % |
|---|---|---|
| show everything | 100 | 49 [37, 60] |
| frozen thresholds, escalate below 0.35 | 70 [59, 80] | 39 [26, 53] |
| ANSWER band only, at or above 0.58 | 57 [46, 69] | 30 [17, 45] |

## Baselines (fitted on dev, applied here)

| system | pooled AUROC | answerable AUROC | decisive AUROC | pooled Brier |
|---|---|---|---|---|
| verbalized alone | 0.629 [0.544, 0.708] | 0.356 [0.242, 0.464] | 0.441 [0.321, 0.553] | 0.228 [0.207, 0.251] |
| agreement alone | 0.742 [0.663, 0.824] | 0.659 [0.502, 0.798] | 0.666 [0.482, 0.839] | 0.200 [0.172, 0.226] |
| free signals alone | 0.831 [0.761, 0.891] | 0.786 [0.677, 0.888] | 0.801 [0.672, 0.918] | 0.173 [0.151, 0.197] |
| confirmed minus_logprobs (frozen artifact) | 0.818 [0.753, 0.878] | 0.785 [0.683, 0.879] | 0.838 [0.728, 0.938] | 0.185 [0.164, 0.206] |

## Escalation precision and recall (answered items; wrong = label 0)

- ESCALATE only: precision 0.714, recall 0.441, n 21.
- Flagged (ESCALATE or VERIFY): precision 0.733, recall 0.647, n 30.

## Accuracy at coverage (answered items, tie-aware thresholds nearest the target)

| target | threshold | coverage | accuracy |
|---|---|---|---|
| 0.25 | 0.667 | 0.07 | 1.00 [1.00, 1.00] |
| 0.5 | 0.585 | 0.57 | 0.70 [0.55, 0.83] |
| 0.75 | 0.369 | 0.70 | 0.61 [0.47, 0.74] |
| 1.0 | 0.188 | 1.00 | 0.51 [0.40, 0.63] |

## Risk-coverage, answered population (every reachable threshold)

| threshold | coverage % | risk % |
|---|---|---|
| 1.000 | 6 [1, 11] | 0 [0, 0] |
| 0.667 | 7 [1, 13] | 0 [0, 0] |
| 0.585 | 57 [46, 69] | 30 [17, 45] |
| 0.571 | 63 [51, 74] | 34 [21, 49] |
| 0.562 | 64 [53, 74] | 33 [20, 48] |
| 0.509 | 66 [54, 76] | 35 [21, 49] |
| 0.506 | 67 [56, 77] | 36 [23, 51] |
| 0.500 | 69 [57, 79] | 38 [24, 52] |
| 0.369 | 70 [59, 80] | 39 [26, 53] |
| 0.308 | 93 [86, 99] | 45 [33, 57] |
| 0.188 | 100 [100, 100] | 49 [37, 60] |

## Per bucket: actions, grades, policy outcomes (counts next to rates; ambiguous indicative only)

| bucket | n | actions | grades | outcomes (n, correct) |
|---|---|---|---|---|
| answerable | 62 | {'ANSWER': 44, 'CLARIFY': 6, 'ABSTAIN': 12} | {'CORRECT': 36, 'WRONG': 22, 'PARTIAL': 4} | ANSWER 31/28, VERIFY 3/1, ESCALATE 10/6, ABSTAIN 12/1, CLARIFY 6/0 |
| ambiguous | 9 | {'ANSWER': 8, 'CLARIFY': 1} | {'PARTIAL': 3, 'CORRECT': 2, 'WRONG': 4} | ANSWER 3/0, VERIFY 2/1, ESCALATE 3/0, CLARIFY 1/1 |
| unanswerable | 34 | {'ABSTAIN': 33, 'CLARIFY': 1} | {'PARTIAL': 1, 'CORRECT': 32, 'WRONG': 1} | ABSTAIN 33/32, CLARIFY 1/0 |
| false_premise | 29 | {'ANSWER': 18, 'ABSTAIN': 11} | {'WRONG': 21, 'PARTIAL': 8} | ANSWER 6/0, VERIFY 4/0, ESCALATE 8/0, ABSTAIN 11/0 |

## Confounder: accuracy by whether the evidence chunk was retrieved

| bucket | retrieved: correct/n | not retrieved: correct/n |
|---|---|---|
| answerable | 33/50 (66%) | 3/12 (25%) |
| ambiguous | 2/8 (25%) | 0/1 (0%) |
| unanswerable | 18/19 (95%) | 14/15 (93%) |
| false_premise | 0/26 (0%) | 0/3 (0%) |
| all | 53/103 (51%) | 17/31 (55%) |

## Reliability, pooled (10 bins)

| bin | n | mean confidence | accuracy |
|---|---|---|---|
| 0.0 to 0.1 | 0 |  |  |
| 0.1 to 0.2 | 10 | 0.188 | 0.1 |
| 0.2 to 0.3 | 0 |  |  |
| 0.3 to 0.4 | 34 | 0.309 | 0.206 |
| 0.4 to 0.5 | 1 | 0.463 | 0.0 |
| 0.5 to 0.6 | 73 | 0.58 | 0.63 |
| 0.6 to 0.7 | 7 | 0.662 | 1.0 |
| 0.7 to 0.8 | 0 |  |  |
| 0.8 to 0.9 | 0 |  |  |
| 0.9 to 1.0 | 9 | 1.0 | 1.0 |
