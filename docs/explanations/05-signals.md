# 05. The confidence signals

The calibrator needs numbers that predict whether an answer is right, for
a question nobody has answered yet. That second part is the discipline.
Anything from the item record, such as whether the gold evidence was
retrieved, the bucket, or the gold answer, is ground truth. It would make
the calibrator look excellent and mean nothing, since at inference time
there is no record. So every feature comes from the run alone, with a
note saying where.

The free signals read the trace the agent already wrote. Process signals
are facts about the run: the action and its path, how many readings the
model listed, whether a calculator line was issued and computed, how long
the answer is, whether it hedges. Retrieval signals are facts about the
passages: the best score, the gap to the second, the pages the top chunks
span. Retrieval support asks whether the answer is backed by what was
retrieved, three ways: the share of the answer's words found in a chunk,
the cosine between answer and chunk in the retriever's embedding space,
and a small entailment model's probability that a chunk entails the answer.

The paid signals cost extra model calls: token log-probabilities of the
draft, a follow-up asking for a 0 to 100 confidence while the model still
sees the passages, and five resampled drafts scored for agreement with the
graded draft. They come after a first look at the free table.

A common misconception: a feature that separates right from wrong on dev
is good. Not if it separates the buckets instead; M4 tests that.

Summary: features come from the run, never the item record; free first.
