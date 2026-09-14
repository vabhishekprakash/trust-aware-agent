# 03. The agent loop

The agent is the thing being measured, so it has to be able to do what the
question set tests. A model that can only ever answer fails every ambiguous,
unanswerable and false-premise item the same way, and the confidence score
would then measure a missing feature. So the loop has three real actions of
its own: ANSWER, CLARIFY and ABSTAIN. The later policy layer adds VERIFY and
ESCALATE on top, from the confidence score.

Each question goes through the same steps. Retrieve the eight nearest
chunks. Ask the model one narrow thing first: do these passages answer the
question in more than one way? It lists the readings and their answers, and
code decides: two readings with different answers means CLARIFY. Then the
model drafts an answer from the passages. If the draft needs arithmetic it
writes a calculator line, the calculator runs, and the model finishes with
the result. If the draft says the handbook does not say, the action is
ABSTAIN. Otherwise the draft is the answer. The best retrieval score is
kept as a signal only; on dev it did not separate right from wrong.

Every step is written to a trace: the chunks and their scores, the readings
listed, the draft, the calculator calls, and which path decided the action,
prompt or rule. The next milestone's signals read that trace, not the answer.

A common misconception: a model told to look for two readings will only
find real ones. It finds distinctions everywhere, so the loop measures how
often the step fires on answerable questions, the false-clarify rate.

Summary: the loop retrieves, checks for readings, drafts, calculates when
asked, decides between the three actions, and traces every step.
