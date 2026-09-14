# Test split results, read once

Preregistered in reports/m8-preregistration.md. Frozen: {"agent_commit": "85db315", "artifact_sha256": "58f3f3d1cba468861b8b5094dae334b270c7fbbdff946fac1a801ad3e1d90116", "policy_sha256": "767fea22e942067807041787901d05347959d921a32c66365fc496b2e3bc3821", "split_sha256": "3c344521a08865da402a50558c8fbb8eab1b5b0098799b1ba93e84db1f18ad1c", "grader": "grader-v13", "grader_sha256": "a2eb938e82b0b63fa8a00c834e0569924e80b0a966ac1663b2ed9ca4986ad485"}.
100 items; strata counts {'pooled': 100, 'answerable': 46, 'decisive': 36}; correct per stratum {'pooled': 50, 'answerable': 26, 'decisive': 26}. Wall clock 6490 s (loop 2344, confidence 254, sampling 1815, grading 1958).

Attempts (a crashed attempt leaves a start line and replays from the cache): 1.

## Audit, run regardless of band

- Provenance: every feature name in the rows is in the provenance lists and none is a ground-truth field (asserted).
- Split: seed 42, scripts/lock_and_split.py, stratified by bucket, halves per bucket; test counts found {'answerable': 46, 'ambiguous': 9, 'unanswerable': 25, 'false_premise': 20}, expected {'answerable': 46, 'ambiguous': 9, 'unanswerable': 25, 'false_premise': 20}.
- Near-duplicates across dev and test (Jaccard >= 0.6, cosine >= 0.9, or same evidence page with cosine >= 0.8): 15 flagged.
  - q0006 / q0196 (same evidence page and cosine >= 0.8 with q0196): "In the handbook's life-cycle cost example, by how many percentage points does the share of life-cycle cost committed by the design exceed the share of cost actually spent during design?" against "The handbook's life-cycle cost curve shows roughly 75% of a project's cost already spent by the time design is done; what share of the total does it say those design decisions commit?"
  - q0026 / q0207 (same evidence page and cosine >= 0.8 with q0207): "According to the handbook's definitions of needs, goals and objectives, how many criteria should an objective generally satisfy?" against "Since the handbook says objectives are derived from the baselined requirements set, what four criteria should those objectives meet?"
  - q0036 / q0212 (same evidence page and cosine >= 0.8 with q0212): "Up to which milestone review does the handbook say technology assessment should stay involved in the design and development process, starting from concept development?" against "The handbook wants technology assessment to keep running from concept development all the way through the Critical Design Review. Where does it say the technology development lessons learned should be captured after that point?"
  - q0066 / q0229 (same evidence page and cosine >= 0.8 with q0229): "In which project phase does the handbook say issuing technical work directives to cost account managers is essential?" against "Since issuing technical work directives to the Cost Account Managers is described as essential during Phase D, what three things does that step produce?"
  - q0067 / q0068 (same evidence page and cosine >= 0.8 with q0068): "After which review are a project's requirements put under formal configuration control?" against "Once the requirements baseline is under formal configuration control after the SRR, what body must approve a change to it?"
  - q0072 / q0231 (same evidence page and cosine >= 0.8 with q0231): "In what month and year did NASA change its risk management approach to make it more proactive?" against "According to the handbook, Continuous Risk Management is applied first to establish the baseline performance requirements and Risk-Informed Decision Making then manages the risks during development and implementation; in what year did NASA adopt this two-process approach?"
  - q0097 / q0120 (jaccard 0.60 with q0120; same evidence page and cosine >= 0.8 with q0198): "At which life-cycle review does the SEMP get baselined?" against "At which life cycle review does the baseline get established?"
  - q0108 / q0027 (same evidence page and cosine >= 0.8 with q0027): "Which team is responsible for producing the operations concept?" against "In the handbook's distinction between a concept of operations and an operations concept, which team normally produces the operations concept?"
  - q0117 / q0209 (same evidence page and cosine >= 0.8 with q0051, q0218): "What is being checked when the handbook talks about validation?" against "The handbook breaks requirements validation into four steps; what does the fourth and final step check for?"
  - q0124 / q0126 (same evidence page and cosine >= 0.8 with q0126): "Which Phase D review signs off that the system is ready?" against "What does the readiness review have to show the system is ready for?"
  - q0139 / q0179 (cosine 0.92 with q0179): "What joint cost and schedule confidence level must the Agency Baseline Commitment be funded to at KDP C?" against "What joint cost and schedule confidence level does a project's baseline have to reach before it can pass KDP C?"
  - q0141 / q0143 (same evidence page and cosine >= 0.8 with q0143): "How many days before a life cycle review like PDR does the handbook say the review material has to be delivered to the board?" against "How many working days before a milestone review does the handbook say the review data package must be delivered to the board members?"
  - q0203 / q0019 (same evidence page and cosine >= 0.8 with q0019): "The handbook defines tailoring as modifying the recommended SE practices used to accomplish the SE requirements; where does it say significant tailoring of that kind should be documented?" against "What term does the handbook introduce for modifying the recommended SE practices that are used to meet the SE requirements, as opposed to seeking relief from the requirements themselves?"
  - q0234 / q0079 (cosine 0.92 with q0079; same evidence page and cosine >= 0.8 with q0079): "Since the handbook makes the manager of the technical data management system solely responsible for entering data into it, how are the people who originate the data supposed to hand it over?" against "According to the handbook, who is solely responsible for entering data into the technical data management system?"
  - q0240 / q0130 (same evidence page and cosine >= 0.8 with q0130): "Because the final Technology Maturity Assessment is carried out just before the Critical Design Review, which report does it provide the basis for?" against "When in the life cycle is the Technology Maturity Assessment carried out?"

## Headline: the confirmed vector

| stratum | n | correct | AUROC | Brier | ECE (10 bins) | AURC |
|---|---|---|---|---|---|---|
| pooled | 100 | 50 | 0.657 [0.555, 0.756] | 0.252 [0.217, 0.290] | 0.148 [0.077, 0.244] | 0.402 [0.265, 0.525] |
| answerable | 46 | 26 | 0.588 [0.435, 0.738] | 0.281 [0.232, 0.333] | 0.222 [0.138, 0.362] | 0.420 [0.196, 0.559] |
| decisive | 36 | 26 | 0.490 [0.288, 0.717] | 0.306 [0.245, 0.366] | 0.295 [0.197, 0.442] | 0.340 [0.100, 0.515] |

With the flagged near-duplicate items removed:

| stratum | AUROC | Brier |
|---|---|---|
| pooled | 0.669 [0.557, 0.773] | 0.252 [0.216, 0.292] |
| answerable | 0.584 [0.397, 0.759] | 0.286 [0.226, 0.350] |
| decisive | 0.503 [0.277, 0.750] | 0.311 [0.247, 0.386] |

Policy on the 54 answered items (24 correct):

| operating point | coverage % | risk % |
|---|---|---|
| show everything | 100 | 56 [43, 70] |
| frozen thresholds, escalate below 0.35 | 72 [61, 85] | 64 [49, 80] |
| ANSWER band only, at or above 0.58 | 56 [43, 70] | 53 [36, 73] |

## Baselines (fitted on dev, applied here)

| system | pooled AUROC | answerable AUROC | decisive AUROC | pooled Brier |
|---|---|---|---|---|
| verbalized alone | 0.665 [0.570, 0.753] | 0.385 [0.290, 0.472] | 0.481 [0.438, 0.500] | 0.224 [0.202, 0.250] |
| agreement alone | 0.706 [0.601, 0.799] | 0.642 [0.477, 0.788] | 0.617 [0.417, 0.797] | 0.229 [0.192, 0.267] |
| free signals alone | 0.696 [0.585, 0.800] | 0.634 [0.482, 0.788] | 0.579 [0.382, 0.794] | 0.231 [0.189, 0.276] |
| confirmed minus_logprobs (frozen artifact) | 0.657 [0.555, 0.756] | 0.588 [0.435, 0.738] | 0.490 [0.288, 0.717] | 0.252 [0.217, 0.290] |

## Escalation precision and recall (answered items; wrong = label 0)

- ESCALATE only: precision 0.333, recall 0.167, n 15.
- Flagged (ESCALATE or VERIFY): precision 0.583, recall 0.467, n 24.

## Accuracy at coverage (answered items, tie-aware thresholds nearest the target)

| target | threshold | coverage | accuracy |
|---|---|---|---|
| 0.25 | 0.591 | 0.09 | 0.60 [0.00, 1.00] |
| 0.5 | 0.585 | 0.56 | 0.47 [0.27, 0.64] |
| 0.75 | 0.341 | 0.74 | 0.38 [0.22, 0.52] |
| 1.0 | 0.188 | 1.00 | 0.44 [0.30, 0.57] |

## Risk-coverage, answered population (every reachable threshold)

| threshold | coverage % | risk % |
|---|---|---|
| 1.000 | 6 [0, 11] | 67 [0, 100] |
| 0.667 | 7 [2, 15] | 50 [0, 100] |
| 0.591 | 9 [2, 18] | 40 [0, 100] |
| 0.585 | 56 [43, 70] | 53 [36, 73] |
| 0.571 | 67 [56, 80] | 61 [46, 78] |
| 0.549 | 68 [56, 82] | 62 [47, 79] |
| 0.547 | 70 [57, 83] | 63 [48, 80] |
| 0.500 | 72 [61, 85] | 64 [49, 80] |
| 0.341 | 74 [63, 85] | 62 [48, 78] |
| 0.308 | 98 [94, 100] | 55 [42, 69] |
| 0.188 | 100 [100, 100] | 56 [43, 70] |

## Per bucket: actions, grades, policy outcomes (counts next to rates; ambiguous indicative only)

| bucket | n | actions | grades | outcomes (n, correct) |
|---|---|---|---|---|
| answerable | 46 | {'ANSWER': 36, 'ABSTAIN': 7, 'CLARIFY': 3} | {'CORRECT': 26, 'WRONG': 18, 'PARTIAL': 2} | ANSWER 20/14, VERIFY 4/0, ESCALATE 12/10, ABSTAIN 7/2, CLARIFY 3/0 |
| ambiguous | 9 | {'ANSWER': 6, 'CLARIFY': 1, 'ABSTAIN': 2} | {'PARTIAL': 5, 'WRONG': 4} | ANSWER 4/0, VERIFY 1/0, ESCALATE 1/0, ABSTAIN 2/0, CLARIFY 1/0 |
| unanswerable | 25 | {'ANSWER': 1, 'ABSTAIN': 24} | {'WRONG': 1, 'CORRECT': 24} | VERIFY 1/0, ABSTAIN 24/24 |
| false_premise | 20 | {'ANSWER': 11, 'ABSTAIN': 5, 'CLARIFY': 4} | {'WRONG': 16, 'PARTIAL': 4} | ANSWER 6/0, VERIFY 3/0, ESCALATE 2/0, ABSTAIN 5/0, CLARIFY 4/0 |

## Confounder: accuracy by whether the evidence chunk was retrieved

| bucket | retrieved: correct/n | not retrieved: correct/n |
|---|---|---|
| answerable | 26/36 (72%) | 0/10 (0%) |
| ambiguous | 0/7 (0%) | 0/2 (0%) |
| unanswerable | 15/16 (94%) | 9/9 (100%) |
| false_premise | 0/18 (0%) | 0/2 (0%) |
| all | 41/77 (53%) | 9/23 (39%) |

## Reliability, pooled (10 bins)

| bin | n | mean confidence | accuracy |
|---|---|---|---|
| 0.0 to 0.1 | 0 |  |  |
| 0.1 to 0.2 | 12 | 0.188 | 0.083 |
| 0.2 to 0.3 | 0 |  |  |
| 0.3 to 0.4 | 19 | 0.309 | 0.632 |
| 0.4 to 0.5 | 1 | 0.484 | 0.0 |
| 0.5 to 0.6 | 60 | 0.576 | 0.517 |
| 0.6 to 0.7 | 4 | 0.654 | 1.0 |
| 0.7 to 0.8 | 0 |  |  |
| 0.8 to 0.9 | 0 |  |  |
| 0.9 to 1.0 | 4 | 1.0 | 0.5 |
