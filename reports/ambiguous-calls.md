# Ambiguous pass: dominant-reading check

Every ambiguous candidate was tested against one question: would a person asking this
question have both readings in mind? Items with one natural reading move to answerable
or are dropped; duplicates the code check missed are dropped. The verifiers that produced
the bucket were language model agents, and so is the author of this pass, so the twelve
closest calls are left to the owner. Write keep, move or drop after 'decision:' and run
scripts/apply_ambiguous_pass.py with --owner-decisions.

- kept: 24
- moved to answerable: 10 (q0095, q0108, q0109, q0110, q0111, q0112, q0117, q0119, q0124, q0132)
- dropped: 5 (q0098, q0104, q0105, q0115, q0121)
- awaiting the owner's decision: 0 (none)
- ambiguous items in the pool now: 24, of which 0 pending
- candidates in the pool: 236 (blind hold-back merged back in; blind40_key.jsonl keeps the drafted record)

## The owner's calls


## Every call

- q0095: owner (lean keep). The handbook states 'the SE engine cycles five times' outright and gives seven only for the technical management half. A user asking how often the engine runs 'over the course of a project' may well mean through Phase F, which is the seven. Close.
    - owner's decision: move
    - owner's words: move (disagree with keep) The exact wording on p. 9 settles it: "The SE engine cycles five times from Pre-Phase A through Phase D" is unqualified, while the seven is explicitly scoped: "The SE engine cycles the technical management processes seven times from Pre-Phase A through Phase F." Someone typing "the SE engine" is treating it as one object. Knowing it has two halves that cycle different numbers of times is the definition of a careful-reader distinction. Gold: five, with seven accepted only if the answer scopes it to the technical management processes.
- q0096: keep. Two major phases against seven lettered phases, on one page. The owner labelled it ambiguous blind.
- q0097: owner (lean keep). SRR for projects and tightly coupled programs, MDR/SDR for uncoupled programs. Most people asking mean a project, which makes SRR dominant, but the handbook's own footnote makes the answer conditional.
    - owner's decision: keep
    - owner's words: keep (agree) A project person and an uncoupled-program person both type this sentence, and each knows which they are. The footnote is itself written as a conditional, so a complete answer names both branches regardless of who's asking.
- q0098: drop. Duplicate of q0097 with the SEMP spelled out; the code dedup missed it because the words differ.
- q0099: keep. Program Implementation reviews differ by program type and the question names a program without saying which.
- q0100: keep. Owner labelled it ambiguous blind; Pre-Phase A baseline against the glossary's Phase A to B transition.
- q0101: keep. Owner labelled it ambiguous blind and found a third phase (Appendix R). The three-way reading should be reflected: add Phase A from page 10 as a third reading before the set is locked.
- q0102: keep. Owner labelled it ambiguous blind; Phase B preliminary plan against the Phase E plan that Phase F implements.
- q0103: keep. Owner labelled it ambiguous blind; CDR for an end item against PRR for a production run.
- q0104: owner (lean drop). The two lists of who agrees on acceptable risk are two passages that disagree, not two readings of the question. A user has one question in mind and the handbook is inconsistent. That is a candidate for answerable with the union, or for dropping.
    - owner's decision: drop
    - owner's words: drop (agree) These aren't two readings, they're two passages about different things: p. 34 is risk posture as a precondition for tailoring, p. 176 is the defined term. One caution on the alternative you floated: don't make the gold a union. Nobody would write that answer, and grading against it punishes correct responses. If you keep it, make it answerable on the glossary list alone.
- q0105: drop. Duplicate of q0106 (waiver approval through the compliance matrix).
- q0106: owner (lean keep). OCE for a Center tailoring for standard use, Center Director for a project seeking a waiver. Someone submitting through the matrix is usually a project, which makes the Center Director dominant, but the question does not say.
    - owner's decision: keep
    - owner's words: keep (agree, narrowly) Both branches sit on p. 40 and both are compliance-matrix submissions, so neither is stated as the general case. That's what separates it from q0095. But I'd rewrite rather than just label it: as typed, a model answering "OCE" is correct about the document and will score as wrong against a Center-Director gold.
- q0107: keep. The handbook says outright that the customer depends on the level of the product breakdown structure; a clarifying question is the natural response.
- q0108: owner (lean move). The question says 'operations concept', which is the handbook's own name for the operational team's document, so that reading is arguably dominant. But the owner's blind label on q0109 shows a reader hears ConOps. If moved, gold is 'the operational team' with the page 51 quote.
    - owner's decision: move
    - owner's words: move (agree), with a collision to fix The ConOps/Operations Concept split is the clearest careful-reader case in the set; the handbook devoted a box on p. 51 to it precisely because people conflate the two, which means the ordinary asker holds one reading, not both. Gold: the operational team. The problem is q0109, "Who is responsible for writing the ops concept?", whose gold came out as the systems engineer via p. 4. Two near-identical questions, two contradictory golds. Fix one before either ships.
- q0109: move. Owner's blind label: answerable, the systems engineer or technical team leads the ConOps.
- q0110: move. Owner's blind label: answerable, the Stakeholder Expectations Definition Process, which produces the MOEs; 'does what it needs to' maps to the MOE wording.
- q0111: owner (lean keep). Program or project owns programmatic requirements, the Technical Authority owns technical ones; the question says 'the requirements a project has to meet', which covers both kinds. Real in the handbook, but a user may simply mean 'who signs waivers'.
    - owner's decision: move
    - owner's words: move (disagree with keep) Not for the reason the lean gives. Figure 4.2-2 answers the question in one shot: programmatic requirements are owned by the program/project, technical requirements by the Technical Authority. Since the question says "the requirements a project has to meet," which covers both, a single two-part answer satisfies every asker. That's a compound answer, not two competing ones. Gold: both halves.
- q0112: move. Owner's blind label: answerable, the realized end product is what validation compares against stakeholder expectations.
- q0113: keep. Trade studies are the core step of Design Solution Definition and a method of Decision Analysis, and the handbook points from one to the other.
- q0114: owner (lean keep). Verification testing against requirements, validation testing against the ConOps. 'Testing the end product' usually means verification, which makes the requirements reading dominant, but the handbook names both.
    - owner's decision: keep
    - owner's words: keep (agree) Verification and validation are the central distinction in the field, not an internal taxonomy, and the handbook's own p. 89 box exists because both are "testing the end product." Real askers land on either side.
- q0115: owner (lean keep). Same verification against validation split as q0114, phrased as 'shown to satisfy before it moves on'. Keep one of q0114 and q0115, not both.
    - owner's decision: drop
    - owner's words: drop (agree with "keep one," and this is the one to cut) Same split as q0114, worse phrasing. "Before it moves on" is muddier than "judged against," since verification and validation both precede transition and happen in sequence. Also worth knowing: q0115 already appears as item 10 in the batch you had graded, so it's a duplicate across sets, not just within this one.
- q0116: keep. Once per design for qualification, once per unit for acceptance; 'the test program' does not pick.
- q0117: owner (lean move). Product validation against requirements validation. The owner's ruling on q0112 read 'validation' as product validation, which by the same logic makes this answerable with the product reading. If moved, gold is 'that the realized end product meets stakeholder expectations in its intended environment' with the page 100 quote.
    - owner's decision: move
    - owner's words: move (agree, different reasoning) I'd rest it on the question rather than on consistency with the q0112 ruling. "When the handbook talks about validation" points at the process named Validation; requirements validation is a scoped usage inside Technical Requirements Definition. Gold: product validation.
- q0118: keep. The handbook states both recipients in one sentence and the question does not say which level of the product hierarchy is meant.
- q0119: owner (lean move). 'All of a project's plans' points at the project plan, the top of the hierarchy, which makes that reading dominant; the SEMP is senior only to the technical plans. If moved, gold is 'the project plan' with the page 116 quote.
    - owner's decision: move
    - owner's words: move (agree) "All of a project's plans" names the top of the hierarchy. The SEMP reading requires already knowing the SEMP is senior only to the technical plans and subordinate to the project plan, which is the thing being asked. Note this is also a duplicate of graded item 22.
- q0120: keep. 'The baseline' has four senses set at different reviews.
- q0121: drop. Duplicate of q0120 (baseline established at which review).
- q0122: keep. Two adjacent sentences split the responsibility between the Center and the project manager.
- q0123: owner (lean keep). Project SDR leads to KDP B, program SDR to KDP I. Most people asking mean a project, but the program SDR is a real second reading on page 20.
    - owner's decision: keep
    - owner's words: keep (agree) Same structure as q0097, and it earns its keep the same way: program and project are both real askers, and neither reading is the document's internal machinery.
- q0124: move. Owner's grade on grader check sheet 19 treated the FRR as the natural answer to 'signs off that the system is ready'; moved on that basis.
- q0125: keep. Verification plans are approved at both CDR and SIR against different baselines; the handbook is genuinely two-valued here.
- q0126: keep. 'The readiness review' names no review; ORR and FRR have different objects.
- q0127: keep. ORR before launch and PLAR after both end with the system ready to assume operations.
- q0128: keep. DR and DRR both assess readiness for disposal.
- q0129: keep. Functional and physical configuration audits compare against different things and the question says 'a configuration audit'.
- q0130: keep. Initial and final Technology Maturity Assessments at different points.
- q0131: keep. TRL 6 and TRL 7 are both system prototype demonstrations differing only in environment.
- q0132: owner (lean move). TRL 5 and TRL 6 both use 'relevant environment', but the glossary itself says 'a TRL of 6, i.e., technology demonstrated in a relevant environment', which makes 6 the dominant answer. If moved, gold is 'TRL 6' with the glossary quote from page 195.
    - owner's decision: move
    - owner's words: move (agree, with a caveat on the gold) The glossary's unqualified "a TRL of 6 (i.e., technology demonstrated in a relevant environment)" on p. 195 makes 6 dominant. But p. 211 gives TRL 5 as "component and/or breadboard validation in relevant environment," so an answer that says 5 and scopes it to a component or breadboard is right about the document. Let the gold accept that.
- q0133: keep. The human-rating report appears at three successive reviews; the question does not say which phase.
