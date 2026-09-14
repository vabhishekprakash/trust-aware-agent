# 01. The question set and the grader

Everything in this project is measured against questions whose correct
outcome we already know. That set is the ruler. If the ruler is bent, every
number we report is bent with it, and nothing downstream can fix that.

Each question is labeled with what should happen. Answerable: the handbook
states the answer, recorded with its page. Ambiguous: two readings that the
handbook answers differently, so the right move is to ask which is meant.
Unanswerable: it sounds like a handbook question, but the handbook never
says. False premise: it assumes something the handbook contradicts, and the
right move is to say so. The last two exist because an agent that is never
asked the impossible never has to admit uncertainty, which is the point.

The grader is the rule that decides whether an answer was right. Free text
cannot be compared letter by letter: "the Program Manager" and "the manager
of the program" are the same answer. So the grader checks for a refusal or
a clarifying question, then tries a cheap exact match. Only then does it ask
a language model fixed yes-or-no questions about the draft, each yes backed
by words copied from it. A rule turns the answers into a grade, and the
grades feed the calibrator as ones and zeros. A lenient grader flatters the
agent, a harsh one punishes it, so the owner signs off on the examples first.

A common misconception: a bigger question set fixes a bad grader. It does
not. It produces more wrong labels, faster.

Summary: the question set is the ruler and the grader is how we read it.
Both are fixed and checked before the agent is measured, because errors here
are invisible later.
