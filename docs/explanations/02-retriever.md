# 02. The retriever

The agent may only answer from the handbook, and the handbook is 119,000
words, far more than the small model can read at once. So every question
first fetches a few passages. Everything downstream rests on whether the
right passage came back: the answer, the signal that measures how well the
passages support it, and the rule that lets the agent say the handbook
does not cover something. The blind checks showed the shape of the risk.
With the right passage in front of it the model answered almost every
answerable item correctly; without it, almost none.

Each of the 773 chunks, about 200 words apiece, is turned once into a vector
by a small sentence-embedding model, bge-small. A question is turned into a
vector the same way, and the chunks whose vectors point most nearly in the
same direction are returned. The index is flat: every search compares the
question against all 773 chunks. At this size that takes milliseconds, and
there is nothing to tune and nothing to go stale. An answer can straddle a
chunk boundary, so the chunks on either side of a hit can be added.

How many chunks to return is measured, not guessed. On the dev items we
check how often the chunk holding the evidence quote sits in the top k, for
several k, and report that next to the context each k costs. The test
items are never used for this.

A common misconception: a bigger k is free. Every extra chunk spends context
the small model does not have and buries the right passage among wrong ones.

Summary: the book becomes vectors once, each question becomes one vector,
the nearest chunks come back, and how many is set from measured recall on dev.
