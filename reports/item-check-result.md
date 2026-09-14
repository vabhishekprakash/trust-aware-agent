# Blind item check: result

The owner labelled 40 held-back items from the handbook alone, without the drafted labels.
Bucket agreement is exact. The answer check is a heuristic that sorts the agreed items; the
disagreements are listed in full below for a person to read.

## Bucket agreement per drafted bucket

    drafted bucket   items  bucket agreed  owner's bucket when different
    answerable          14             14  -
    ambiguous            8              5  answerable 3
    unanswerable        10             10  -
    false_premise        8              8  -

overall bucket agreement: 37 of 40 (92 percent)

## Answer check on the items whose bucket agreed

- answerable: matches gold or alias 14
- ambiguous: names both drafted answers 5
- unanswerable: bucket agreed 10
- false_premise: correction shares 20 content words with the drafted fix 1, correction shares 10 content words with the drafted fix 2, correction shares 12 content words with the drafted fix 1, correction shares 14 content words with the drafted fix 2, correction shares 13 content words with the drafted fix 1, correction shares 18 content words with the drafted fix 1

## Bucket disagreements

### q0109: drafted ambiguous, owner answerable

question: Who is responsible for writing the ops concept?

owner: The systems engineer. "The systems engineer usually plays the key role in leading the development of the concept of operations (ConOps) and resulting system architecture, defining boundaries, defining and allocating requirements, evaluating design tradeoffs…"
owner page: 4
Slight looseness: the handbook says the systems engineer leads the development, not that they write it, and hedges with "usually." I'd accept either phrasing.

drafted reading 1: Concept of Operations (ConOps) -> the technical team, early in Pre-Phase A (page 51)
drafted reading 2: Operations Concept -> the operational team (page 51)
drafted notes: The handbook has a dedicated box contrasting Concept of Operations with Operations Concept, and 'ops concept' is a shorthand that fits either; the two documents are written by different teams. A grader may see 'technical team' and stop, but the Operations Concept reading gives a different author.

### q0110: drafted ambiguous, owner answerable

question: Which system design process produces the measures used to judge whether the system does what it needs to?

owner: The Stakeholder Expectations Definition Process, which produces the Measures of Effectiveness (MOEs) — "measures that represent expectations that are critical to the success of the system, and failure to satisfy these measures will cause the stakeholder to deem the system unacceptable." Table 3.0-1 shows MOE definition approved at MCR.
owner page: 52 (also 19, 53)
Near-call: if "does what it needs to" is read as technical performance rather than stakeholder success, the answer becomes MOPs from the Technical Requirements Definition Process (p. 61). I kept it answerable because "does what it needs to" maps to the MOE definition's language about stakeholder acceptability, but the question would be tighter if it said "critical to the success of the system."

drafted reading 1: the stakeholder-level measures whose failure makes the system unacceptable -> Stakeholder Expectations Definition, which outputs the Measures of Effectiveness (MOEs) (page 53)
drafted reading 2: the quantitative, supplier-view measures of the system's performance in its intended environment -> Technical Requirements Definition, which defines the Measures of Performance (MOPs) and TPMs (page 61)
drafted notes: Both MOEs and MOPs are 'measures' that say whether the system meets its need, and each is an output of a different design process. A response naming only one process without asking which kind of measure is meant is one-sided.

### q0112: drafted ambiguous, owner answerable

question: During validation, what is actually being compared against the stakeholder expectations?

owner: The end product itself — each implemented or integrated and verified end product, from the lowest end product in a system structure branch up to the top-level system. The Product Validation Process demonstrates that the end product satisfies its stakeholder expectations (MOEs) within the intended operational environments.
owner page: 100

drafted reading 1: requirements validation in the Technical Requirements Definition Process -> the technical requirements and MOEs, checked for consistency with stakeholder needs (page 61)
drafted reading 2: the Product Validation Process on a realized end product -> the integrated realized end product, checked against the MOEs, MOPs and ConOps (page 99)
drafted notes: The handbook uses 'validation' for two different activities in two processes: validating requirements in Chapter 4 and validating the realized product in Chapter 5. A grader should not accept 'the end product' alone as complete, since a requirements engineer would mean the requirements set.


## Agreed bucket, answer flagged for reading

None.
