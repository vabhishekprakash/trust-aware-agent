# Ambiguous pass: dominant-reading check

Every ambiguous candidate was tested against one question: would a person asking this
question have both readings in mind? Items with one natural reading move to answerable
or are dropped; duplicates the code check missed are dropped. The verifiers that produced
the bucket were language model agents, and so is the author of this pass, so the twelve
closest calls are left to the owner. Write keep, move or drop after 'decision:' and run
scripts/apply_ambiguous_pass.py with --owner-decisions.

- kept: 20
- moved to answerable: 4 (q0109, q0110, q0112, q0124)
- dropped: 3 (q0098, q0105, q0121)
- awaiting the owner's decision: 12 (q0095, q0097, q0104, q0106, q0108, q0111, q0114, q0115, q0117, q0119, q0123, q0132)
- ambiguous items in the pool now: 32, of which 12 pending
- candidates in the pool: 238 (blind hold-back merged back in; blind40_key.jsonl keeps the drafted record)

## The owner's calls

### q0095

question: How many times does the systems engineering engine get run over the course of a project?

reading 1: the technical development processes (steps 1 through 9) of the SE engine -> five times, Pre-Phase A through Phase D (page 9)
reading 2: the technical management processes (steps 10 through 17) of the SE engine -> seven times, Pre-Phase A through Phase F (page 9)

my lean: keep. The handbook states 'the SE engine cycles five times' outright and gives seven only for the technical management half. A user asking how often the engine runs 'over the course of a project' may well mean through Phase F, which is the seven. Close.

decision (keep / move / drop):

### q0097

question: At which life-cycle review does the SEMP get baselined?

reading 1: SEMP of a project, tightly coupled program, or single-project program -> at the SRR (page 19)
reading 2: SEMP of an uncoupled or loosely coupled program -> at the MDR/SDR (page 19)

my lean: keep. SRR for projects and tightly coupled programs, MDR/SDR for uncoupled programs. Most people asking mean a project, which makes SRR dominant, but the handbook's own footnote makes the answer conditional.

decision (keep / move / drop):

### q0104

question: Who has to agree on what level of risk is acceptable for a project?

reading 1: the risk posture that has to be understood before tailoring the SE requirements -> the project, the customer/stakeholder, Center management, and independent reviewers (page 34)
reading 2: 'acceptable risk' as the handbook defines the term -> the program/project, the governing authority, the mission directorate, and other customer(s) (page 176)

my lean: drop. The two lists of who agrees on acceptable risk are two passages that disagree, not two readings of the question. A user has one question in mind and the handbook is inconsistent. That is a candidate for answerable with the union, or for dropping.

decision (keep / move / drop):

### q0106

question: Who signs off on tailoring of the SE NPR requirements when it is submitted through a Compliance Matrix?

reading 1: a Center tailoring the NPR requirements for standard use across the Center (Appendix H.1) -> the Office of the Chief Engineer (OCE) (page 40)
reading 2: a program or project delegated to a Center seeking a waiver or deviation (Appendix H.2) -> the Center Director or designee (page 40)

my lean: keep. OCE for a Center tailoring for standard use, Center Director for a project seeking a waiver. Someone submitting through the matrix is usually a project, which makes the Center Director dominant, but the question does not say.

decision (keep / move / drop):

### q0108

question: Which team is responsible for producing the operations concept?

reading 1: the Concept of Operations (ConOps) developed early in Pre-Phase A -> the technical team (page 51)
reading 2: the Operations Concept describing how flight and ground systems are used together -> the operational team (page 51)

my lean: move. The question says 'operations concept', which is the handbook's own name for the operational team's document, so that reading is arguably dominant. But the owner's blind label on q0109 shows a reader hears ConOps. If moved, gold is 'the operational team' with the page 51 quote.

decision (keep / move / drop):

### q0111

question: Who owns the requirements a project has to meet and therefore approves waivers against them?

reading 1: programmatic requirements imposed by the mission directorate or program -> the program or project (page 57)
reading 2: technical requirements invoked by OCE, OSMA and OCHMO directives, technical standards and Center institutional requirements -> the Technical Authority (page 57)

my lean: keep. Program or project owns programmatic requirements, the Technical Authority owns technical ones; the question says 'the requirements a project has to meet', which covers both kinds. Real in the handbook, but a user may simply mean 'who signs waivers'.

decision (keep / move / drop):

### q0114

question: What are the results of testing the end product judged against?

reading 1: verification testing under the Product Verification Process -> the approved requirements set, such as the System Requirements Document (page 89)
reading 2: validation testing under the Product Validation Process -> the ConOps, i.e. effectiveness and suitability for use in mission operations by typical users (page 11)

my lean: keep. Verification testing against requirements, validation testing against the ConOps. 'Testing the end product' usually means verification, which makes the requirements reading dominant, but the handbook names both.

decision (keep / move / drop):

### q0115

question: After an end product is built, what does it have to be shown to satisfy before it moves on?

reading 1: Product Verification -> all of its specified requirements (page 90)
reading 2: Product Validation -> stakeholder expectations (MOEs) in the intended operational environment (page 100)

my lean: keep. Same verification against validation split as q0114, phrased as 'shown to satisfy before it moves on'. Keep one of q0114 and q0115, not both.

decision (keep / move / drop):

### q0117

question: What is being checked when the handbook talks about validation?

reading 1: product validation (the Product Validation Process) -> that the realized end product fulfills its intended use in its intended environment and meets stakeholder expectations (page 100)
reading 2: requirements validation (during Technical Requirements Definition) -> that the requirements themselves are written correctly, technically correct, satisfy stakeholders, feasible, verifiable and not redundant (page 60)

my lean: move. Product validation against requirements validation. The owner's ruling on q0112 read 'validation' as product validation, which by the same logic makes this answerable with the product reading. If moved, gold is 'that the realized end product meets stakeholder expectations in its intended environment' with the page 100 quote.

decision (keep / move / drop):

### q0119

question: Which document do all of a project's plans have to comply with?

reading 1: the technical plans (verification, validation, CM, risk, etc.) -> the project SEMP (page 123)
reading 2: the whole planning hierarchy including the SEMP itself -> the project plan (page 116)

my lean: move. 'All of a project's plans' points at the project plan, the top of the hierarchy, which makes that reading dominant; the SEMP is senior only to the technical plans. If moved, gold is 'the project plan' with the page 116 quote.

decision (keep / move / drop):

### q0123

question: Which key decision point does a successful System Definition Review lead up to?

reading 1: the SDR of a project (or single-project program), held in Phase A -> KDP B (page 161)
reading 2: the SDR held during program Formulation -> KDP I (page 20)

my lean: keep. Project SDR leads to KDP B, program SDR to KDP I. Most people asking mean a project, but the program SDR is a real second reading on page 20.

decision (keep / move / drop):

### q0132

question: What TRL has a piece of technology reached once it has been shown to work in a relevant environment?

reading 1: a component or breadboard validated in a relevant environment -> TRL 5 (page 211)
reading 2: a system/subsystem model or prototype demonstrated in a relevant environment -> TRL 6 (page 211)

my lean: move. TRL 5 and TRL 6 both use 'relevant environment', but the glossary itself says 'a TRL of 6, i.e., technology demonstrated in a relevant environment', which makes 6 the dominant answer. If moved, gold is 'TRL 6' with the glossary quote from page 195.

decision (keep / move / drop):


## Every call

- q0095: owner (lean keep). The handbook states 'the SE engine cycles five times' outright and gives seven only for the technical management half. A user asking how often the engine runs 'over the course of a project' may well mean through Phase F, which is the seven. Close.
- q0096: keep. Two major phases against seven lettered phases, on one page. The owner labelled it ambiguous blind.
- q0097: owner (lean keep). SRR for projects and tightly coupled programs, MDR/SDR for uncoupled programs. Most people asking mean a project, which makes SRR dominant, but the handbook's own footnote makes the answer conditional.
- q0098: drop. Duplicate of q0097 with the SEMP spelled out; the code dedup missed it because the words differ.
- q0099: keep. Program Implementation reviews differ by program type and the question names a program without saying which.
- q0100: keep. Owner labelled it ambiguous blind; Pre-Phase A baseline against the glossary's Phase A to B transition.
- q0101: keep. Owner labelled it ambiguous blind and found a third phase (Appendix R). The three-way reading should be reflected: add Phase A from page 10 as a third reading before the set is locked.
- q0102: keep. Owner labelled it ambiguous blind; Phase B preliminary plan against the Phase E plan that Phase F implements.
- q0103: keep. Owner labelled it ambiguous blind; CDR for an end item against PRR for a production run.
- q0104: owner (lean drop). The two lists of who agrees on acceptable risk are two passages that disagree, not two readings of the question. A user has one question in mind and the handbook is inconsistent. That is a candidate for answerable with the union, or for dropping.
- q0105: drop. Duplicate of q0106 (waiver approval through the compliance matrix).
- q0106: owner (lean keep). OCE for a Center tailoring for standard use, Center Director for a project seeking a waiver. Someone submitting through the matrix is usually a project, which makes the Center Director dominant, but the question does not say.
- q0107: keep. The handbook says outright that the customer depends on the level of the product breakdown structure; a clarifying question is the natural response.
- q0108: owner (lean move). The question says 'operations concept', which is the handbook's own name for the operational team's document, so that reading is arguably dominant. But the owner's blind label on q0109 shows a reader hears ConOps. If moved, gold is 'the operational team' with the page 51 quote.
- q0109: move. Owner's blind label: answerable, the systems engineer or technical team leads the ConOps.
- q0110: move. Owner's blind label: answerable, the Stakeholder Expectations Definition Process, which produces the MOEs; 'does what it needs to' maps to the MOE wording.
- q0111: owner (lean keep). Program or project owns programmatic requirements, the Technical Authority owns technical ones; the question says 'the requirements a project has to meet', which covers both kinds. Real in the handbook, but a user may simply mean 'who signs waivers'.
- q0112: move. Owner's blind label: answerable, the realized end product is what validation compares against stakeholder expectations.
- q0113: keep. Trade studies are the core step of Design Solution Definition and a method of Decision Analysis, and the handbook points from one to the other.
- q0114: owner (lean keep). Verification testing against requirements, validation testing against the ConOps. 'Testing the end product' usually means verification, which makes the requirements reading dominant, but the handbook names both.
- q0115: owner (lean keep). Same verification against validation split as q0114, phrased as 'shown to satisfy before it moves on'. Keep one of q0114 and q0115, not both.
- q0116: keep. Once per design for qualification, once per unit for acceptance; 'the test program' does not pick.
- q0117: owner (lean move). Product validation against requirements validation. The owner's ruling on q0112 read 'validation' as product validation, which by the same logic makes this answerable with the product reading. If moved, gold is 'that the realized end product meets stakeholder expectations in its intended environment' with the page 100 quote.
- q0118: keep. The handbook states both recipients in one sentence and the question does not say which level of the product hierarchy is meant.
- q0119: owner (lean move). 'All of a project's plans' points at the project plan, the top of the hierarchy, which makes that reading dominant; the SEMP is senior only to the technical plans. If moved, gold is 'the project plan' with the page 116 quote.
- q0120: keep. 'The baseline' has four senses set at different reviews.
- q0121: drop. Duplicate of q0120 (baseline established at which review).
- q0122: keep. Two adjacent sentences split the responsibility between the Center and the project manager.
- q0123: owner (lean keep). Project SDR leads to KDP B, program SDR to KDP I. Most people asking mean a project, but the program SDR is a real second reading on page 20.
- q0124: move. Owner's grade on grader check sheet 19 treated the FRR as the natural answer to 'signs off that the system is ready'; moved on that basis.
- q0125: keep. Verification plans are approved at both CDR and SIR against different baselines; the handbook is genuinely two-valued here.
- q0126: keep. 'The readiness review' names no review; ORR and FRR have different objects.
- q0127: keep. ORR before launch and PLAR after both end with the system ready to assume operations.
- q0128: keep. DR and DRR both assess readiness for disposal.
- q0129: keep. Functional and physical configuration audits compare against different things and the question says 'a configuration audit'.
- q0130: keep. Initial and final Technology Maturity Assessments at different points.
- q0131: keep. TRL 6 and TRL 7 are both system prototype demonstrations differing only in environment.
- q0132: owner (lean move). TRL 5 and TRL 6 both use 'relevant environment', but the glossary itself says 'a TRL of 6, i.e., technology demonstrated in a relevant environment', which makes 6 the dominant answer. If moved, gold is 'TRL 6' with the glossary quote from page 195.
- q0133: keep. The human-rating report appears at three successive reviews; the question does not say which phase.
