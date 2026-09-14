# The premise step: a negative result

Every reader of the dev numbers will ask the same question. The
false-premise bucket sat at zero correct answers in 20. Why not build the
obvious fix? We did, and it made the system worse on every measure. This
note records what was built, what it did, and why it is switched off.

## What was built

A step in the loop with the same shape as the readings step. After
retrieval the model is asked one narrow thing: does the question take
something for granted that the passages contradict? It replies NO
CONTRADICTION or one line naming the assumption in the question's words,
the passage number, and the correction in the passage's words. Code then
gates the claim before it becomes a REJECT action. At least two content
words and 60 percent of the assumption must come from the question. The
correction must be grounded in the cited passage by two words not in the
question, and it must share a word with the assumption. The draft prompt
also gained one sentence asking the model to say so when a question
assumes something the passages contradict. The step ran ahead of CLARIFY
and ABSTAIN. Everything in it is in src/agent/loop.py behind the
premise_check flag, with tests.

## What it did on the full dev set

Same 100 items, same retrieval, same grader (v13). Run v1 is the loop
without the step; run v2 is the loop with it (reports/dev-run-v1.md,
reports/dev-run-v2.md).

| bucket | n | correct, v1 | correct, v2 | REJECTs in v2 | REJECTs graded CORRECT |
|---|---|---|---|---|---|
| answerable | 46 | 29 | 23 | 6 | 0 |
| ambiguous | 9 | 2 | 0 | 5 | 0 |
| unanswerable | 25 | 23 | 18 | 4 | 0 |
| false premise | 20 | 0 | 0 | 4 | 0 |
| all | 100 | 54 | 41 | 19 | 0 |

The gate did work. On answerable and unanswerable items the model claimed
a contradiction 34 times in 71 and the gate let 10 through. That is a
false-fire rate of 14 percent, under the one-fifth bar set for the
readings step. On false-premise items it claimed 8 in 20 and the gate
passed 4. Every one of the 19 rejections that passed was wrong, including
the four on the bucket the step was built for. The extra prompt sentence
also moved three correct answerable answers to abstentions, and REJECT
sitting ahead of CLARIFY took five of the nine ambiguous items. Net: 13
correct labels lost, 1 gained.

## The four corrections that passed the gate on false-premise items

Each is the model's own text. None states the correction the item records.

- q0198. Assumption named: the handbook ties the baseline to a specific
  Phase B review. Correction offered: "Establishment of baselines implies
  the implementation of configuration management procedures. Phase B
  culminates in a series of PDRs." The handbook's correction: the SEMP is
  baselined in Phase A, at the SRR.
- q0208. Assumption named: the technical team does not start the concept
  of operations until Phase B. Correction offered: "Technical planning in
  Phase E generally focuses on the management..." The handbook's
  correction: the concept of operations is developed in Pre-Phase A.
- q0224. Assumption named: the project plan is allowed to define what the
  SEMP defines. Correction offered: "A key document capturing and updating
  the details from the technical planning..." The handbook's correction:
  the SEMP is subordinate to the project plan.
- q0227. Assumption named: the verification plan is baselined at the
  Critical Design Review. Correction offered: "Updates to verification
  planning continue throughout logical decomposition and design
  development..." The handbook's correction: it is baselined at PDR.

In each case the model found the right assumption, or nearly, and then
quoted a passage sentence on the same topic that does not contradict it.
The gate checks that the correction is grounded and on topic. It cannot
check that it contradicts, and that is the judgement the step needed.

## Cost

The step added 1,492 s to the dev run, 53 percent of a 2,842 s wall clock,
one model call per item.

## Conclusion

Premise rejection is a judgement this model does not have at 3B. It can
restate the assumption; it cannot tell that a passage contradicts it, and
no code gate on word overlap can supply that. The step is off, the prompts
are byte-identical to run v1, and the false-premise bucket stays at zero
with the limitation stated in the annotation guide.

Testing this properly would take a larger model for the premise step
alone, or a small classifier fine-tuned on premise-contradiction pairs
built from this corpus. Both were out of scope. The project runs on a 4 GB
card where a 7B model does not fit alongside the judge, and a fine-tuned
classifier needs labelled pairs this project has no budget to produce.
