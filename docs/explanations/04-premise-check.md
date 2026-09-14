# 04. The premise check

A question can take something for granted that the handbook contradicts:
"given that the SEMP is baselined in Phase B, which review..." The right
move is to say the assumption is wrong and give the correction. In the
first dev run the agent never did that. It built on the false premise in 14
of 20 items and abstained on the rest, so that bucket had no correct
answers at all, and a calibrator trained on it could learn nothing about
when the agent is right there. The fix is a real move in the loop, not a
change to the labels.

The step has the same shape as the readings step. After retrieval the
model is asked one narrow thing: does the question take something for
granted that the passages contradict? It replies either NO CONTRADICTION
or one line naming the assumption in the question's words, the passage
number, and the correction in the passage's words. Code then applies a
gate before it accepts a rejection: most of the assumption's words must
come from the question, and the correction must be about the assumption
and found in the cited passage. If the gate passes, the action is REJECT
and the response states the assumption and the correction with its page.
If it fails, the model's claim is recorded in the trace and nothing changes.

A common misconception: a model told to look for a false assumption will
only find real ones. It will find them in ordinary questions too, so the
step's firing rate on answerable and unanswerable items is measured as a
false-fire rate, against the same one-fifth bar as the readings step.

Summary: the model names a contradicted assumption and its passage, code
checks both against the text, and only then does the agent reject.
