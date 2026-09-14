# 07. The decision policy

A probability on its own is not a decision. The policy turns the
calibrated probability into one of three outcomes for an answer the
agent produced: ANSWER, show it; VERIFY, show it with a flag that it
needs checking; ESCALATE, withhold it and hand the question to a person
with the trace attached. The agent's own CLARIFY and ABSTAIN stand as
they are, and a confident abstention passes through as the answer "the
handbook does not say".

VERIFY is a flag, not a verification loop. The problem statement asked
for tool-based verification; it is not implemented, for two reasons.
Retrieval recall on dev is the same at k=10 as at k=8, so re-retrieving
buys little, and a second draft from the same model mostly repeats the
first. And the premise step is the precedent: a second model pass built
to fix a measured gap made every bucket worse.

The two thresholds were set on dev as a coverage choice, not a risk
guarantee: no error target of 10 to 25 percent was reachable with useful
coverage, so the owner chose to escalate about the bottom quarter of
answered items and flag the middle tertile. Above the upper threshold the
answer is shown; below the lower one it is escalated; between, flagged.

A common misconception: high coverage at low risk means the policy works.
Not if the covered items are the easy abstentions on unanswerable
questions while every hard answer is escalated; that bucket is reported
on its own.

Summary: three outcomes from two thresholds chosen on dev for coverage;
VERIFY is a flag; the unanswerable bucket is reported on its own.
