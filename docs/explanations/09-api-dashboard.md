# 09. The API and the dashboard

Everything so far runs from scripts over saved traces. The API is the
same system answering one live question at a time, and the dashboard is
one page that shows what it did: the answer, the outcome the policy
chose, the capped confidence, the reasons behind it and the passages it
rested on, from a single request.

A live question runs the measured system, not a cheaper stand-in. The
loop retrieves eight chunks, runs the readings step and drafts, about 20
seconds. The calibrator's vector holds the paid signals, so the page then
makes the confidence call, about 8 seconds, and draws five resampled
drafts, about 23 seconds: roughly 50 seconds per question on the
development card. The free-signals finding is the counterpoint: the
cheapest features carried the most signal.

Three endpoints. Health says whether Ollama answers and the calibrator
loaded. Ask takes a question and returns the outcome, the capped
probability with the sentence about certainty, the family breakdown, the
passages with page numbers and the step timings. Explain returns the
breakdown for a recent run by its id. A gallery tab lists the 134 dev
items with outcome, confidence, grade and bucket from the committed
reports; bucket and grade appear there only, never on the live path.

A common misconception: the page's number is the number the report
measured. It is the shipped artifact's, refit on all of dev and capped;
the report's metrics are out of fold; the page says so.
Summary: one page, three endpoints, the measured system at its real
cost, the report's caveats printed where the number is.
