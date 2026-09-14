# Sample explanations on dev

Calibrator minus_logprobs, logistic plus isotonic, the artifact fitted on all of dev. The explanation uses that artifact; the metrics in the report use out-of-fold scores. Across the 134 dev items the artifact's probability differs from the out-of-fold one by 0.096 on average (max 0.415), as expected for a model that has now seen every item.

## ANSWER band

### q0003 (answerable, graded CORRECT)

Question: What is AS9100 and which industry was it created for?

Answer: AS9100 is a quality management system that is widely adopted and standardized in the commercial aerospace industry.

Confidence 67 percent, so the policy says ANSWER. By signal family, in log-odds: retrieval scores and spread +2.42; the answer's length and hedging +0.22; the readings step -0.22; agreement among resampled answers -0.20. Single features pushing up most: gap between the best and second passage scores (0.07, well above the usual); mean retrieval score of the passages (0.57, well below the usual); retrieval score of the best passage (0.65, well below the usual). Pushing down most: entailment of the answer by any passage (0.12, below the usual); readings the model listed for the question (1, about average for this agent); similarity between the answer and the best passage (0.75, above the usual). Everything else together moved the log-odds by +1.34; the starting point was +0.05. These amounts are exact for the log-odds, not for the percentage; correlated features inside a family can take opposite signs, so the family sums are the steadier reading; and they say what moved the score on this run, not what causes a correct answer.

### q0013 (answerable, graded WRONG)

Question: After the MCR, what happens to the preliminary mission descope options that the project team prepared as a gate product?

Answer: The preliminary descope options are kept in the documentation archive in case they are needed later in the life cycle. There is no indication of what happens to them after being developed as a gate product for the MCR.

Confidence 58 percent, so the policy says ANSWER. By signal family, in log-odds: support from the passages -0.90; the readings step +0.74; retrieval scores and spread +0.55; agreement among resampled answers -0.28. Single features pushing up most: readings the model listed for the question (0, below the usual); gap between the best and second passage scores (0.05, above the usual); spread of retrieval scores across the passages (0.11, well above the usual). Pushing down most: entailment of the answer by any passage (0.06, below the usual); similarity between the answer and the best passage (0.84, above the usual); agreement of the resampled answers with this answer (0.37, below the usual). Everything else together moved the log-odds by -0.00; the starting point was +0.05. These amounts are exact for the log-odds, not for the percentage; correlated features inside a family can take opposite signs, so the family sums are the steadier reading; and they say what moved the score on this run, not what causes a correct answer.

## VERIFY band

### q0023 (answerable, graded WRONG)

Question: In the handbook's example table of tailoring NPR 7120.5 project products, which product is fully compliant for Type A projects but not applicable for every other project type?

Answer: Type A projects are fully compliant for Design Documentation, while it is not applicable for all other types (B, C, D, E, F). Therefore, the answer is: Design Documentation.

Confidence 57 percent, so the policy says VERIFY. By signal family, in log-odds: retrieval scores and spread -0.86; agreement among resampled answers +0.40; the readings step -0.22; the model's stated confidence +0.15. Single features pushing up most: entailment of the answer by any passage (0.44, above the usual); agreement among five resampled answers (0.27, below the usual); share of resamples that abstained (0, below the usual). Pushing down most: lowest agreement of a resample with this answer (0.14, below the usual); agreement of the resampled answers with this answer (0.28, below the usual); gap between the best and second passage scores (0.01, below the usual). Everything else together moved the log-odds by -0.49; the starting point was +0.05. These amounts are exact for the log-odds, not for the percentage; correlated features inside a family can take opposite signs, so the family sums are the steadier reading; and they say what moved the score on this run, not what causes a correct answer.

### q0037 (answerable, graded WRONG)

Question: What term does the handbook use for a feasible solution that minimizes or maximizes the objective function?

Answer: The handbook uses the term "optimal solution" for a feasible solution that minimizes or maximizes the objective function.

Confidence 57 percent, so the policy says VERIFY. By signal family, in log-odds: the readings step -1.18; agreement among resampled answers +0.57; the answer's length and hedging +0.20; the model's stated confidence +0.15. Single features pushing up most: agreement of the resampled answers with this answer (0.87, above the usual); share of resamples that abstained (0, below the usual); share of resamples that took the same form as this answer (1, above the usual). Pushing down most: readings the model listed for the question (2, well above the usual); agreement among five resampled answers (0.73, above the usual); gap between the best and second passage scores (0.01, below the usual). Everything else together moved the log-odds by +0.63; the starting point was +0.05. These amounts are exact for the log-odds, not for the percentage; correlated features inside a family can take opposite signs, so the family sums are the steadier reading; and they say what moved the score on this run, not what causes a correct answer.

## ESCALATE band

### q0011 (answerable, graded CORRECT)

Question: For space flight projects, into how many incremental phases are the Formulation and Implementation life-cycle phases broken down?

Answer: For space flight projects, the Formulation and Implementation life-cycle phases are broken down into seven incremental pieces. This information is provided in the passage starting from page 17 to 18 of the given text.

Confidence 31 percent, so the policy says ESCALATE. By signal family, in log-odds: support from the passages -1.17; retrieval scores and spread -0.32; agreement among resampled answers +0.28; the readings step -0.22. Single features pushing up most: share of resamples that abstained (0, below the usual); share of resamples that took the same form as this answer (1, above the usual); distinct pages among the passages (8, above the usual). Pushing down most: similarity between the answer and the best passage (0.83, above the usual); retrieval score of the best passage (0.82, well above the usual); lowest agreement of a resample with this answer (0.23, about average for this agent). Everything else together moved the log-odds by -0.89; the starting point was +0.05. These amounts are exact for the log-odds, not for the percentage; correlated features inside a family can take opposite signs, so the family sums are the steadier reading; and they say what moved the score on this run, not what causes a correct answer.

### q0043 (answerable, graded CORRECT)

Question: Which NASA requirements document must software development follow when the technical team makes or codes a product?

Answer: The technical team should ensure that software development follows NPR 7150.2 when making or coding a product.

Confidence 31 percent, so the policy says ESCALATE. By signal family, in log-odds: retrieval scores and spread -1.87; agreement among resampled answers +0.27; support from the passages -0.26; the answer's length and hedging +0.23. Single features pushing up most: calculator lines that could not be computed (1, well above the usual); agreement among five resampled answers (0.13, below the usual); share of resamples that abstained (0, below the usual). Pushing down most: the top three passages share a page (1, well above the usual); lowest agreement of a resample with this answer (0, below the usual); calculator lines the draft issued (1, well above the usual). Everything else together moved the log-odds by -2.63; the starting point was +0.05. These amounts are exact for the log-odds, not for the percentage; correlated features inside a family can take opposite signs, so the family sums are the steadier reading; and they say what moved the score on this run, not what causes a correct answer.

