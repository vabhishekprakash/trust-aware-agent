# The trust-aware agent, explained without the jargon

## What it is

A program that answers questions about one long technical document, the
NASA Systems Engineering Handbook, and says how sure it is. It runs on a
small language model on an ordinary graphics card, with no internet. When
it is not sure, it does one of three things instead of answering. It asks
which of two meanings you intended, it says the handbook does not cover
that, or it hands the question to a person. Every number it gives comes
with a plain-language list of the reasons behind it.

## Why that matters

Language models answer confidently whether or not they are right. In a
setting like engineering documentation, a wrong answer delivered with
confidence is worse than no answer. The question this project asked was
narrow: can a small model, looking at its own behaviour, tell when it is
about to be wrong? And can that estimate be trusted enough to act on?

## How it works, in five steps

1. It finds the eight passages of the handbook most like the question.
2. It asks itself one narrow question first: could this question mean two
   different things that the passages answer differently? If so, it asks
   you which.
3. It drafts an answer from the passages. If arithmetic is needed, a
   calculator does it, not the model.
4. It measures thirty-nine things about how that went. How much of the
   answer's wording is in the passages, how similar five re-tries of the
   answer are to each other, what the model says when asked how sure it
   is, and so on. None of those measurements uses the right answer,
   because at the moment of answering nobody knows it. That rule matters
   more than it sounds: if the program could see the correct answer while
   judging its own work, the whole test would prove nothing.
5. A small statistical model, trained on 134 questions with known
   answers, turns those measurements into a probability. A rule then
   shows the answer, shows it with a warning, or withholds it.

## What was found

The honest result is a negative one, and it was written down in advance
how it would be judged. On the 134 training questions the probability
was a weak but real guide to correctness. On 100 fresh questions it
mostly was not. Where it mattered most, on answerable questions where the
right passage had been found, the probability was no better than a coin
toss at telling right answers from wrong ones. With only 36 such
questions, though, the result is too noisy to be sure of either way. The rule
built on the probability withheld ten correct answers out of twelve it
held back. A deployed version would have refused to show answers that
were right.

Three things did hold up. First, whether the right passage was found
decided almost everything: with it, the model was right about three
times in four; without it, never. Second, the cheap measurements, taken
from the record of what the model did at no extra cost, told you as much
or more than the expensive ones. The expensive ones involve asking the model
again and cost thirty seconds a question. Third, the most obvious fix
for the weakest category of question made everything worse. That fix was
a step asking the model whether the question rests on a false
assumption, a judgement the model cannot make at this size.

## What was done to keep the numbers honest

Every answer was graded by a second language model, and that grader was
checked against a person three times without the person seeing its
verdicts; the last check agreed 19 times in 20. The 100 test questions
were locked away and read once, after the whole analysis had been written
down and committed, including what would count as good, bad, or too good
to believe. Seven times during the project a number was wrong or looked
better than it was, and each time two checks disagreed and the error was
found before a released version of the report carried it. All seven are
listed in the report.

## What a reader should take away

Confidence estimates from a small model are not free of cost and not
reliable enough to act on at this data size, and a system that claims
otherwise should be asked how it knows. The project's own dashboard
applies that rule to itself: it never shows a probability of 100 percent,
and it says why.

## Where to look

The report is docs/report.md. The numbered explainers in
docs/explanations walk through each part in under thirty lines each. The
decisions log, docs/decisions.md, records every choice and the reason,
including the ones that turned out wrong.
