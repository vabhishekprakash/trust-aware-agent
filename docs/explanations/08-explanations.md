# 08. Explaining a confidence score

A probability without a reason is hard to act on. When the dashboard says
41 percent and flags the answer, the reader should see why: which signals
pushed the score up, which down, and by how much. The calibrator is a
logistic regression on standardised features, so that has an exact
answer. Each feature's contribution is its coefficient times its
standardised value, the contributions add up to the log-odds, and the
log-odds pass through the isotonic step to become the probability shown.

The explanation layer reads the fitted artifact and one run's feature
vector and returns the contributions in log-odds units, sorted by size,
each with its raw value and dev mean so a reader can tell "0.2" is low.
A phrase table turns feature names into plain language: lexical support
becomes "share of the answer's words found in the best passage". The
breakdown is the top pushes up, the top pushes down, then the rest.

Two limits are stated with every explanation. The contributions are
exact for the log-odds, not for the final probability, because the
isotonic step is a monotone bend that keeps order but not distances. And
a contribution says what moved the score on this run, not that the
feature causes correctness.

A common misconception: the biggest coefficient is the most important
feature. Importance on a given item is coefficient times how unusual the
value is, so a modest coefficient on an extreme value can dominate.

Summary: contributions are coefficient times standardised value, add up
to the log-odds, and the breakdown names the largest in plain words.
