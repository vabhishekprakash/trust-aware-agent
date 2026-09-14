# Item drafting

How the candidate items were produced and filtered. Every number here comes from
the scripts and workflow runs of 2026-09-09.

## Counts

drafted 252, kept 244, rejected 8
kept per bucket: ambiguous 45, answerable 91, false_premise 48, unanswerable 60
drafted per bucket: ambiguous 48, answerable 96, false_premise 48, unanswerable 60
drafted per agent: ambiguous:1 8, ambiguous:2 8, ambiguous:3 8, ambiguous:4 8, ambiguous:5 8, ambiguous:6 8, answerable:1 8, answerable:10 8, answerable:11 8, answerable:12 8, answerable:2 8, answerable:3 8, answerable:4 8, answerable:5 8, answerable:6 8, answerable:7 8, answerable:8 8, answerable:9 8, false_premise:1 8, false_premise:2 8, false_premise:3 8, false_premise:4 8, false_premise:5 8, false_premise:6 8, unanswerable:1 10, unanswerable:2 10, unanswerable:3 10, unanswerable:4 10, unanswerable:5 10, unanswerable:6 10
verifier verdicts: keep 188, fix 30, drop 3
fixed items whose new quote failed the page check: 0
candidates after verification per bucket: answerable 94, ambiguous 39, unanswerable 59, false_premise 26
targets for the final set (240 if the buckets allow, else 200): answerable 84 or 70, ambiguous 48 or 40, unanswerable 60 or 50, false_premise 48 or 40
candidates: 218; held back for the blind item check: 40; in items_candidates.jsonl: 178
passed the code checks but not yet verified (verifier batches that did not run): 23, kept in data/eval/items_unverified.jsonl until they are; per bucket: answerable 0, ambiguous 0, unanswerable 0, false_premise 23

Nothing is locked. The final 200 or 240 are chosen, and the dev and test split is
made, only after the owner has returned the blind item sheet and the review sample.

## Limitations, stated plainly

The items were drafted by language model agents, checked by other language model
agents, and the agent's answers will be graded by a language model judge. The only
human checks are the owner's two 40-item samples: the blind item labels against the
drafted labels, and the blind grades of 40 model drafts against the judge. The code
checks (quote on the stated page, record shape, duplicates) are mechanical and do not
judge whether a question is good. Readers of the final report should weigh every
number with that in mind.

## Method

Thirty drafting agents each worked from the cleaned page text: twelve wrote
answerable items over fixed page ranges, six wrote ambiguous items by theme across
the whole book, six wrote unanswerable items by theme and had to record the search
that found nothing, and six wrote false-premise items over page ranges. Code then
rejected any item whose quote was not on its stated page, whose record broke the
guide's shape, or whose question repeated an earlier one. A second set of agents
checked the survivors five at a time, bucket by bucket, trying to find the answer to
each unanswerable question, a dominant reading for each ambiguous one, a premise the
text does not contradict, or a gold answer its quote does not support. Items were
selected to target with seed 42, keep verdicts before fixes; ids run in bucket and
page order; the blind 40 and the review sample of 10 per bucket were drawn with seed 42.

## Blind hold-back

ids: q0004, q0005, q0012, q0014, q0015, q0018, q0029, q0032, q0036, q0055, q0070, q0076, q0082, q0087, q0096, q0100, q0101, q0102, q0103, q0109, q0110, q0112, q0135, q0140, q0141, q0142, q0148, q0149, q0151, q0174, q0181, q0189, q0193, q0196, q0197, q0200, q0201, q0213, q0214, q0217

## Dropped by the verifiers

- [ambiguous] Who is in control of the allocated baseline?
    - The two 'readings' are two places in the handbook (CM chapter page 147 vs glossary page 176), not two meanings a user could intend by 'Who is in control of the allocated baseline?'. The question has one obvious reading, and page 147 itself reconciles the two statements: 'NASA control of the allocated baseline occurs through review of the engineering deliveries as data items.' There is no natural clarifying question to ask; this is a combined-answer answerable item or a handbook-inconsistency item, not an ambiguous one.
- [ambiguous] Which process is responsible for the bidirectional traceability of requirements?
    - Not genuinely ambiguous. The handbook assigns bidirectional traceability outright to Requirements Management: page 132 lists 'Maintain bidirectional traceability between requirements' as a key activity and devotes subsection 6.2.1.2.3 'Conduct Expectations and Requirements Traceability' to it. The page 60 passage for reading 1 is a step in requirements validation where reviewers 'check that the requirement statements (a) have bidirectional traceability'; checking a property during validation is not being the process 'responsible for' traceability, and no reader asking this question would mean Technical Requirements Definition. Rule (4) applies: one reading is clearly what any reader means. Could be recast as an answerable item with gold 'Requirements Management' (aliases 'Requirements Management Process') and the existing page 132 quote as evidence; the fixed schema has no 'expected' field, so I am dropping rather than switching bucket.
- [ambiguous] Which process evaluates and approves change requests against the baseline?
    - The two answers do not really differ. For the requirements-baseline reading the handbook itself routes approval through Configuration Management: page 133 says that after SRR 'any changes to the requirements should be approved by a Configuration Control Board (CCB) or equivalent authority' and that assessing requirement changes 'is normally accomplished through the use of the Configuration Management Process'; page 132 says Requirements Management evaluates change requests and makes changes only 'if approved by change board'. So an agent answering 'Configuration Management / the CCB' is supported for both readings, contradicting the notes' claim that this misses the requirements-baseline reading. The page 135 quote shows RM issues approved changes as an output, not that RM approves them. Check (3) fails.

## Late verification

The verifier batches that had hit the session limit were resumed. Of the 23 items
they covered, 23 were kept (1 with a fix) and 0 dropped; 0 remain unverified. The kept items were appended with ids from
q0219 on; no existing id changed. Candidates in items_candidates.jsonl per bucket, blind
hold-back excluded: answerable 80, ambiguous 31, unanswerable 49, false_premise 41.

