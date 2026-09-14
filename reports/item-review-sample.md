# Item review sample: 10 per bucket

Drawn with seed 42 per bucket from the items not held back for blind labelling.
Mark each keep, fix, or drop. Fixes are applied before the split is made.

## answerable

### q0006

question: In the handbook's life-cycle cost example, by how many percentage points does the share of life-cycle cost committed by the design exceed the share of cost actually spent during design?

gold answer: 60 percentage points
aliases: 60; sixty; 60%; 60 percent; about 60 percentage points; sixty percentage points

evidence (page 12): "For example, the figure shows that during design, only about 15% of the costs might be expended, but the design itself will commit about 75% of the life cycle costs."

notes: Calculator item: section 2.5 gives about 15% expended and about 75% committed during design; 75 - 15 = 60. Answering '75%' or '15%' alone is wrong because the question asks for the gap. A ratio answer such as '5 times' is a different computation and should not be credited. Figure 2.5-1 on page 13 shows other percentages (8%, 20%, 45%, 90%) that are not the inputs the text uses.

verdict (keep / fix / drop):

### q0017

question: In which project phase does the handbook say software for a planetary probe might still be written and uplinked to the spacecraft during flight?

gold answer: Phase E
aliases: Phase E, Operations and Sustainment; Operations and Sustainment; the operations and sustainment phase; Phase E (Operations and Sustainment)

evidence (page 31): "Additionally, software development may continue well into Phase E. For example, software for a planetary probe may be developed and uplinked while in-flight."

notes: Section 3.8 gives the planetary-probe example as an illustration of software development continuing into Phase E. Phase D or Phase F would be wrong; the letter E must survive normalisation.

verdict (keep / fix / drop):

### q0020

question: Which two life-cycle reviews does the handbook give as an example of reviews a small project might merge into one without needing a waiver from the SE NPR?

gold answer: the SRR and the SDR (or MDR)
aliases: SRR and SDR; System Requirements Review and System Definition Review; SRR and SDR/MDR; SRR and MDR; System Requirements Review and Mission Definition Review; the System Requirements Review and the System Definition Review (or Mission Definition Review)

evidence (page 37): "A small project may decide to combine the SRR and the SDR (or Mission Definition Review (MDR)) for example."

notes: Two-part answer from section 3.11.4.3; naming only one review is partial. SDR and MDR are presented as alternatives, so either paired with SRR is acceptable.

verdict (keep / fix / drop):

### q0021

question: In the handbook's example program/project types table, how many years wide is the primary baseline mission lifetime range given for a Type B mission?

gold answer: 3 years
aliases: 3; three; three years; 3 yr

evidence (page 38): "Criteria Type A Type B Type C Type D Type E Type F"
evidence (page 38): "Mission Lifetime (Primary Baseline Mission) Long. >5 years Medium. 2–5 years Short. <2 years Short. <2 years N/A N/A"

notes: Calculator item: Type B lifetime is Medium, 2–5 years, so the range spans 5 minus 2 = 3 years. Answering '2–5 years' restates the inputs without the subtraction and should be treated as partial; '5' (the upper bound alone) is wrong.

verdict (keep / fix / drop):

### q0024

question: Across which range of project phases are the system design processes primarily used, according to the handbook?

gold answer: Pre-Phase A through Phase C
aliases: Pre-Phase A to Phase C; from Pre-Phase A through Phase C; Pre-Phase A, Phase A, Phase B, and Phase C; Pre-Phase A until Phase C

evidence (page 45): "These system design processes are primarily applied in Pre-Phase A and continue through Phase C."

notes: Stated in chapter 4's introduction. An answer that gives only Pre-Phase A, or that ends at Phase B, is partial or wrong; both endpoints are needed.

verdict (keep / fix / drop):

### q0038

question: In which project phase does the handbook say the system definition is formalized into a baseline?

gold answer: Phase B
aliases: B; in Phase B; phase B

evidence (page 72): "This tendency is formalized at some point (in Phase B) by defining a baseline system definition."

notes: Stated parenthetically in 4.4.1.2.5 (Increase the Resolution of the Design). A grader must not accept Phase A, which page 64 gives for baselining a single architecture; this question is about the baseline system definition.

verdict (keep / fix / drop):

### q0041

question: How many interdependent processes make up the product realization side of the SE engine?

gold answer: five
aliases: 5; five processes; 5 processes; five interdependent processes; 5 interdependent processes

evidence (page 77): "In the product realization side of the SE engine, five interdependent processes result in systems that meet the design specifications and stakeholder expectations."

notes: Count stated directly in the chapter 5 introduction (page 77) and repeated on page 78 ('five product realization processes'); page 5 lists the five and figure 2.1-1 (page 6) numbers them 5 through 9 (Implementation, Integration, Verification, Validation, Transition). A grader should not accept 17 (the total common technical processes) or 9 (the number of steps in the SE engine figure). Confuser: the glossary entry 'Product Realization' on page 189 says 'the four product realization processes'; that count is inconsistent with the SE engine figure and chapter 5, and four is wrong for this question, which asks about the SE engine.

verdict (keep / fix / drop):

### q0045

question: For a small project that does not need a separate integration plan, where does the handbook say the integration planning can be captured?

gold answer: in the SEMP
aliases: SEMP; the Systems Engineering Management Plan; Systems Engineering Management Plan; as part of the SEMP

evidence (page 85): "Small projects and activities may be able to include this as part of their SEMP."

notes: The same page also allows capturing it under a sponsoring program's integration plan, which is a reasonable additional mention but the SEMP is the direct answer for a small project. Appendix H is the outline for a separate plan, not the answer.

verdict (keep / fix / drop):

### q0065

question: According to the handbook, what defines the operational environment when the product is software?

gold answer: the operational platform
aliases: operational platform; its operational platform; the platform it operates on

evidence (page 127): "For software, the environment is defined by the operational platform."

notes: From the 'Environments' box; the same passage says space for space flight hardware/software, which is the trap answer. 'Relevant environment' is a different defined term and not the answer.

verdict (keep / fix / drop):

### q0083

question: In the handbook's example operational definitions for a normalization scale, how many percentage points lie between the threshold for 'high' and the threshold for 'low'?

gold answer: 34
aliases: thirty-four; 34 percentage points; 34 percent; 34 points

evidence (page 169): "For example, “high” could mean “a probability of 67 percent and above.” “Low” could mean “a probability of 33 percent and below.”"

notes: Calculator item: high threshold 67 percent, low threshold 33 percent, difference 34. Restating the two thresholds without subtracting is partial; 33 or 67 alone is wrong. The quote uses curly quotation marks exactly as in the page text.

verdict (keep / fix / drop):

## ambiguous

### q0095

question: How many times does the systems engineering engine get run over the course of a project?

reading 1: the technical development processes (steps 1 through 9) of the SE engine -> five times, Pre-Phase A through Phase D (page 9)
reading 2: the technical management processes (steps 10 through 17) of the SE engine -> seven times, Pre-Phase A through Phase F (page 9)

evidence (page 9): "The SE engine cycles five times from Pre-Phase A through Phase D."
evidence (page 9): "The SE engine cycles the technical management processes seven times from Pre-Phase A through Phase F."

notes: The handbook gives two different cycle counts on the same page depending on which half of the SE engine is meant; a bare 'five' or 'seven' answers only one reading. A grader should not accept 'five' as complete just because it is the first number stated.

verdict (keep / fix / drop):

### q0099

question: What reviews does a program go through once it is in its Implementation phase?

reading 1: an uncoupled or loosely coupled program -> Program Status Reviews / Program Implementation Reviews (PSR/PIR) (page 21)
reading 2: a single-project or tightly coupled program -> reviews synonymous with the project life-cycle reviews through Phase D (page 21)

evidence (page 21): "Satisfy program Implementation reviews’ entrance/success criteria from NPR 7123.1 Reviews • PSR/PIR (uncoupled and loosely coupled programs only)"
evidence (page 21): "Reviews synonymous (not duplicative) with the project reviews in the project life cycle (see FIGURE 3.0-4) through Phase D (single-project and tightly coupled programs only)"

notes: The handbook says the program life cycle has two implementation paths with different major reviews depending on program type, and the question does not name the type. An answer of just 'PSR/PIR' covers only uncoupled and loosely coupled programs.

verdict (keep / fix / drop):

### q0104

question: Who has to agree on what level of risk is acceptable for a project?

reading 1: the risk posture that has to be understood before tailoring the SE requirements -> the project, the customer/stakeholder, Center management, and independent reviewers (page 34)
reading 2: 'acceptable risk' as the handbook defines the term -> the program/project, the governing authority, the mission directorate, and other customer(s) (page 176)

evidence (page 34): "To accomplish this, an acceptable risk posture must be understood and agreed upon by the project, customer/stakeholder, Center management, and independent reviewers."
evidence (page 176): "Acceptable Risk: The risk that is understood and agreed to by the program/project, governing authority, mission directorate, and other customer(s) such that no further specific mitigating action is required."

notes: The tailoring chapter and the glossary each list who must agree to acceptable risk, and the lists differ (Center management and independent reviewers versus governing authority and mission directorate). A grader should not treat the two lists as the same set just because both start with the project.

verdict (keep / fix / drop):

### q0107

question: Who is the customer whose expectations a systems engineer has to capture at the start of the design processes?

reading 1: a systems engineer working at the top level of the Product Breakdown Structure -> the person or organization purchasing the product (page 46)
reading 2: a systems engineer working several levels down in the Product Breakdown Structure -> the leader of the team that takes the element and integrates it into a larger assembly (page 46)

evidence (page 46): "For example, at the topmost level, the customer may be the person or organization that is purchasing the product."
evidence (page 46): "For a systems engineer working three or four levels down in the PBS, the customer may be the leader of the team that takes the element and integrates it into a larger assembly."

notes: The handbook says outright that the customer varies with where in the PBS the engineer works, so the question cannot be answered without knowing the level. A grader should not accept 'the purchaser' alone; both readings sit on the same page.

verdict (keep / fix / drop):

### q0108

question: Which team is responsible for producing the operations concept?

reading 1: the Concept of Operations (ConOps) developed early in Pre-Phase A -> the technical team (page 51)
reading 2: the Operations Concept describing how flight and ground systems are used together -> the operational team (page 51)

evidence (page 51): "Concept of Operations Developed early in Pre-Phase A by the technical team, describes the overall high-level concept of how the system will be used to meet stakeholder expectations, usually in a time sequenced manner."
evidence (page 51): "It is typically developed by the operational team. (See NPR 7120.5.)"

notes: The handbook deliberately distinguishes 'Concept of Operations' from 'Operations Concept' as two documents with different authors, and a user typing 'operations concept' could mean either. A grader should not treat 'technical team' as simply correct because ConOps is the more common term.

verdict (keep / fix / drop):

### q0123

question: Which key decision point does a successful System Definition Review lead up to?

reading 1: the SDR of a project (or single-project program), held in Phase A -> KDP B (page 161)
reading 2: the SDR held during program Formulation -> KDP I (page 20)

evidence (page 161): "The MDR/SDR is conducted during the concept development phase (Phase A) prior to KDP B and the start of preliminary design."
evidence (page 20): "Major reviews leading to approval at KDP I are the SRR, SDR, PDR, and governing Program Management Council (PMC) review."

notes: The handbook has an SDR in both the project life cycle (before KDP B) and the program Formulation phase (leading to KDP I); the question does not say which. A bare 'KDP B' answers only the project reading.

verdict (keep / fix / drop):

### q0124

question: Which Phase D review signs off that the system is ready?

reading 1: ready to be accepted and shipped to the launch site or operational facility -> the System Acceptance Review (SAR) or pre-Ship Review (page 162)
reading 2: ready for a safe and successful flight or launch -> the Flight Readiness Review (FRR) (Mission Readiness Review for some missions) (page 163)

evidence (page 162): "It also ensures that the system has sufficient technical maturity to authorize its shipment to the designated operational facility or launch site."
evidence (page 163): "The FRR examines tests, demonstrations, analyses, and audits that determine the system’s readiness for a safe and successful flight or launch and for subsequent flight operations."

notes: Phase D holds several readiness-type reviews (page 30 lists TRRs, SAR or pre-Ship Review, and ORR; page 29 says Phase D activities focus on preparing for the FRR/MRR), each confirming readiness for a different step, so 'ready' has no single referent. The SAR authorizes shipment (page 162); the FRR authorizes flight or launch (page 163); the ORR (page 163) confirms readiness for normal operations. Listing all of them is a valid response; a lone 'FRR' or 'SAR' answers one reading.

verdict (keep / fix / drop):

### q0126

question: What does the readiness review have to show the system is ready for?

reading 1: Operational Readiness Review (ORR) -> to assume normal operations (page 163)
reading 2: Flight Readiness Review (FRR) -> a safe and successful flight or launch and subsequent flight operations (page 163)

evidence (page 163): "As a result of successful ORR completion, the system is ready to assume normal operations."
evidence (page 163): "The FRR examines tests, demonstrations, analyses, and audits that determine the system’s readiness for a safe and successful flight or launch and for subsequent flight operations."

notes: The handbook defines several readiness reviews (TRR, ORR, FRR, MRR) with different objects of readiness, so 'the readiness review' is underdetermined; ORR and FRR are the two closest in timing. A grader should not accept an answer about test readiness (TRR) or launch alone as covering the question.

verdict (keep / fix / drop):

### q0128

question: Which review checks that the system is ready to be disposed of?

reading 1: the review near the end of mission operations that assesses readiness for decommissioning and disposal -> the Decommissioning Review (DR) (page 164)
reading 2: the review held when major assets are ready for final disposal -> the Disposal Readiness Review (DRR) (page 164)

evidence (page 164): "The DR confirms the decision to terminate or decommission the system and assesses the readiness of the system for the safe decommissioning and disposal of system assets."
evidence (page 164): "A DRR confirms the readiness for the final disposal of the system assets. The DRR is held as major assets are ready for final disposal."

notes: Both the DR (Phase E) and the DRR (Phase F) are described as assessing readiness for disposal of system assets, so 'disposal' readiness maps to two reviews. The similar acronyms make it easy for a grader to accept one as the other.

verdict (keep / fix / drop):

### q0132

question: What TRL has a piece of technology reached once it has been shown to work in a relevant environment?

reading 1: a component or breadboard validated in a relevant environment -> TRL 5 (page 211)
reading 2: a system/subsystem model or prototype demonstrated in a relevant environment -> TRL 6 (page 211)

evidence (page 211): "TRL 5 Component and/or breadboard validation in relevant __ environment"
evidence (page 211): "TRL 6 System/subsystem model or prototype demonstration __ in a relevant environment (ground or space)"

notes: 'Relevant environment' appears in both the TRL 5 and TRL 6 definitions; what separates them is the fidelity of the unit (breadboard vs prototype), which the question leaves open. The glossary line on page 195 ('a TRL of 6, i.e., technology demonstrated in a relevant environment') could tempt a grader to accept 'TRL 6' alone, but the TRL 5 reading is equally supported. The '__' characters are extraction artifacts present in the page text.

verdict (keep / fix / drop):

## unanswerable

### q0136

question: What share of a project's total budget should be set aside for the systems engineering effort?

evidence (page 12): "For example, the figure shows that during design, only about 15% of the costs might be expended, but the design itself will commit about 75% of the life cycle costs."

notes: Searched 'percent of', 'percentage of cost', 'systems engineering cost/effort/budget', 'rule of thumb', 'budget', 'cost estimat', 'UFE'; the handbook never gives a fraction of project cost for SE. The 15%/75% figures on p. 12 describe cost expended versus committed during design, not an SE budget share, and a grader should reject '15%'. Table 3.11-1 (p. 38) gives LCC ranges by mission type, also not an SE share.

verdict (keep / fix / drop):

### q0143

question: How many working days before a milestone review does the handbook say the review data package must be delivered to the board members?

evidence (page 37): "For large projects, it might be appropriate to conduct a very formal review with a formal Review Item Discrepancy (RID)/Request for Action (RFA) process, a summary, and detailed presentations to a wide audience including boards and pre-boards over several weeks."

notes: Searched 'data package', 'review package', 'review material', 'in advance', 'prior to the review', 'lead time', 'working days', 'days', 'RID', 'RFA'. The closest text says a large-project review may run over several weeks and a small one in a few hours, which is the length of the review itself, not a delivery deadline for the package. No lead time in days is given.

verdict (keep / fix / drop):

### q0144

question: What led NASA to cancel the JIMO project that appears among the Type A mission examples?

evidence (page 38): "Examples HST, Cassini, JIMO, JWST, MPCV, SLS, ISS MER, MRO, Discovery payloads, ISS Facility Class payloads, Attached ISS payloads"

notes: Searched 'JIMO' (p. 38 only, in the examples row of Table 3.11-1), 'Jupiter' and 'Icy' (0 relevant hits; the acronym is never expanded), 'Prometheus' (0), 'cancel' (pp. 104, 206, 273, none about JIMO). The handbook lists JIMO only as a Type A example and says nothing about its history or status; the question's premise that it was cancelled is itself not stated in the handbook, so the agent should abstain rather than confirm or explain it.

verdict (keep / fix / drop):

### q0145

question: Which requirements management tool does the handbook recommend a project select for capturing and tracing its requirements?

evidence (page 52): "The use of a requirements management tool or model or other application is particularly useful in capturing and tracing expectations and requirements."

notes: The handbook tells projects to select 'an appropriate requirements management tool' (pp. 15, 52, 58, 134, 135) but never names a product. Searched 'requirements management tool' (5 pages, all generic), 'requirements database' (pp. 62, 132, pointers to the NEN repository), 'DOORS', 'Cradle', 'Jama' (0 hits each). Vendor names appear only in the reference lists, never as a recommendation: 'IBM Rational' white paper (p. 271), 'Rational Unified Process' (p. 277), Vitech 'CORE' training materials (pp. 268, 277), Telelogic 'Rhapsody' white paper (p. 275); the p. 150 'rational' hit is a typo for 'rationale'. A grader should not accept any product name, including Rational, CORE, or Rhapsody drawn from the bibliography.

verdict (keep / fix / drop):

### q0146

question: How much schedule slack, as a share of the total duration, should be built into the need dates for enabling products?

evidence (page 74): "Need dates for the enabling products should be realistically identified on the project schedules, incorporating appropriate schedule slack."

notes: Searched 'schedule slack', 'schedule margin', 'schedule reserve', 'slack', 'float', 'reserve' with digits; the handbook says only 'appropriate schedule slack' (p. 74), defines float in the glossary (p. 182), and lists slack/float as a schedule trend metric (p. 231). No amount or percentage is given anywhere.

verdict (keep / fix / drop):

### q0155

question: What percentage of schedule reserve does the handbook recommend a project carry when it reaches PDR?

evidence (page 133): "Project reserves are used to mitigate the appropriate risk. Analyses of the reserves available versus the needs identified by the threats list assist in the prioritization for reserve use."

notes: Searched 'schedule reserve', 'reserves', 'schedule margin', 'schedule slack', 'float', 'contingency', 'percent' and '%'. Reserves are discussed only qualitatively in the risk management section, and a reference entry cites an external paper on reserve guidelines without giving its numbers. The handbook gives no percentage for schedule reserve at PDR or any other milestone.

verdict (keep / fix / drop):

### q0156

question: By what percentage are baselined requirements allowed to grow before the project is supposed to take corrective action?

evidence (page 134): "The tendency for the set of requirements is to relentlessly increase in size during the course of development, resulting in a system that is more expensive and complex than originally intended."

notes: Searched 'requirements creep', 'percent growth', 'number of requirements', 'threshold', 'TBD', 'trigger'; requirement 'percent growth' is listed as a trend metric to consider (p. 231) and creep is discussed qualitatively (p. 134), but no growth limit or trigger value is stated. Risk thresholds are left to the risk plan (p. 143), so nothing can be combined into a number.

verdict (keep / fix / drop):

### q0158

question: For how many years after a system is retired must its technical data be kept?

evidence (page 151): "Data Management (DM) includes the development, deployment, operations and support, eventual retirement, and retention of appropriate technical, to include mission and science, data beyond system retirement as required by NPR 1441.1, NASA Records Retention Schedules."

notes: The handbook defers retention periods to NPR 1441.1 and never states a duration. Searched 'retention' (pp. 151, 153), 'retain' (pp. 129, 156, 181, 185, none with a period), '1441.1' (p. 151 plus two bibliography entries), 'years' near the DM pages (no hits). Naming NPR 1441.1 is not an answer to the question; a number of years would be fabricated.

verdict (keep / fix / drop):

### q0176

question: What percentage of mass margin does the handbook expect a hardware project to be carrying at PDR?

evidence (page 231): "The performance metrics need to address the minimally required TPMs as defined in NPR 7123.1. These include: 1. Mass margins for projects involving hardware [SE-62]. 2. Power margins for projects that are powered [SE-63]."

notes: Searched 'mass margin', 'power margin', 'mass growth', 'contingency', 'margin' with digits and every '%'/'percent' figure in the text; the handbook only names mass margin as a minimally required TPM (p. 231) and never gives a target or threshold percentage at any review. The only percentages near design are the 15%/75% cost-commitment curve on p. 12, which is about cost, not mass; a grader should not accept any number.

verdict (keep / fix / drop):

### q0183

question: Who was serving as NASA Administrator when Revision 2 of this handbook was issued?

evidence (page 274): "Griffin, Michael D., NASA Administrator. “System Engineering and the Two Cultures of Engineering.” Boeing Lecture, Purdue University, March 28, 2007"

notes: Searched 'Administrator' (pp. 3, 18, 20, 161, 174, 260, 274; only Griffin is named, always as author of the March 28, 2007 Purdue speech), 'Griffin' (pp. 3, 260, 274), 'Bolden' (0), '2016' (pp. ii, viii, 284; the Rev 2 document number and an Orion test date). The trap is Michael Griffin, whom the handbook labels 'NASA Administrator' in a 2007 citation; the handbook never says who held the office in 2016, so an answer of Griffin relies on a nine-year-old citation and one of anyone else relies on outside knowledge.

verdict (keep / fix / drop):

## false_premise

### q0194

question: According to the handbook, NPR 7123.1 uses the word recursive for reapplying a process to the same product to fix a discovered discrepancy; what word does it use for applying the processes to the next lower layer of the system structure?

premise fix: Reapplying a process to the same product to correct a discrepancy is what NPR 7123.1 calls iterative; recursive is the repeated application of processes to design next lower layer products or realize next upper layer products.

evidence (page 7): "“iterative” is the “application of a process to the same product or set of products to correct a discovered discrepancy or other variation from requirements,” whereas “recursive” is defined as adding value to the system “by the repeated application of processes to design next lower layer system products"

notes: Wrong definition: the two NPR 7123.1 terms are swapped. Both words appear together in one sentence, so a response that names 'iterative' as the answer to the follow-up has accepted the swap and should not pass; the correct response says the premise has the definitions backwards.

verdict (keep / fix / drop):

### q0195

question: Since the handbook says the SE engine's technical development processes cycle seven times from Pre-Phase A through Phase D, which of those phases gets more than one pass?

premise fix: The SE engine's technical development processes cycle five times from Pre-Phase A through Phase D; it is the eight technical management processes that cycle seven times, and that span runs from Pre-Phase A through Phase F.

evidence (page 9): "The SE engine cycles five times from Pre-Phase A through Phase D."
evidence (page 9): "The SE engine cycles the technical management processes seven times from Pre-Phase A through Phase F."

notes: Wrong number: the premise borrows the count seven from the technical management band and attaches it to the technical development band. A grader could be fooled because the number seven really does appear on the same page, just for a different set of processes and a different phase span; the follow-up about a double pass has no basis either.

verdict (keep / fix / drop):

### q0198

question: Given that a project's SEMP is baselined during Phase B, which Phase B review does the handbook tie that baseline to?

premise fix: The SEMP is baselined in Phase A, at the SRR for projects (and at MDR/SDR for uncoupled and loosely coupled programs); Phase B only reviews and updates it.

evidence (page 25): "A Systems Engineering Management Plan (SEMP) is baselined in Phase A to document how NASA systems engineering requirements and practices of NPR 7123.1 will be addressed throughout the program life cycle."
evidence (page 19): "SEMP is baselined at SRR for projects, tightly coupled programs and single-project programs, and at MDR/SDR for uncoupled, and loosely coupled programs."

notes: Wrong phase: the SEMP baseline belongs to Phase A, not Phase B. A grader could be tempted by an answer naming the PDR since Phase B's review list does contain PDR, but the handbook never links the SEMP baseline to it; the Pre-Phase A 'preliminary SEMP' is not a baseline either.

verdict (keep / fix / drop):

### q0199

question: Given that the CDR is the review that closes out Phase C, which review opens Phase D right after it?

premise fix: Phase C culminates with the System Integration Review (SIR), not the CDR; the CDRs are held earlier in Phase C, before fabrication and coding begin.

evidence (page 29): "Phase C culminates with an SIR. Training requirements and preliminary mission operations procedures are created and baselined."
evidence (page 29): "These activities focus on preparing for the CDR, Production Readiness Review (PRR) (if required), and the SIR."

notes: Wrong milestone: the CDR is a Phase C review but not its closing one. A grader may accept the premise because CDR is the best-known Phase C review, and an answer that names a Phase D review such as a TRR without correcting the closing review has built on the false premise.

verdict (keep / fix / drop):

### q0206

question: Since the OCE is the approver for a waiver requested by a project whose responsibility was delegated to a Center, where should the project record the approved tailoring afterwards?

premise fix: For a program or project delegated to a Center, the Center Director or designee approves the waiver or deviation; the OCE approves Center-level tailoring for standard use at the Center.

evidence (page 40): "If a program/project whose responsibility has been delegated to a Center is seeking a waiver/deviation from the NPR requirements, the Compliance Matrix in Appendix H.2 is used. In these cases, the Center Director or designee will approve the waiver/deviation."
evidence (page 40): "If it is a Center that is requesting tailoring of the NPR requirements for standard use at the Center, Appendix H.1 is completed and submitted to the OCE for approval"

notes: Wrong owner: the OCE approves Center-wide tailoring, but project-level waivers go to the Center Director or designee. The OCE does appear on the same page, which could trick a grader into accepting the premise.

verdict (keep / fix / drop):

### q0208

question: The technical team does not start the concept of operations until Phase B according to the handbook, so what is it supposed to describe once it is written?

premise fix: The handbook says the Concept of Operations is developed early in Pre-Phase A by the technical team, not in Phase B.

evidence (page 51): "Concept of Operations Developed early in Pre-Phase A by the technical team, describes the overall high-level concept of how the system will be used to meet stakeholder expectations, usually in a time sequenced manner."

notes: Wrong phase: Pre-Phase A, not Phase B. The second half of the question is answerable from the same passage, so an agent that describes the ConOps without flagging the phase error should not get credit.

verdict (keep / fix / drop):

### q0209

question: The handbook breaks requirements validation into four steps; what does the fourth and final step check for?

premise fix: The handbook breaks requirements validation into six steps, not four, and the last step asks whether the requirements are redundant or over-specified.

evidence (page 60): "Validating requirements can be broken into six steps: 1. Are the Requirements Written Correctly?"

notes: Wrong count: six steps, not four. A grader could be fooled if the agent simply reports step 4 (feasibility) as the answer; that accepts the false count instead of correcting it.

verdict (keep / fix / drop):

### q0212

question: The handbook wants technology assessment to keep running from concept development all the way through the Critical Design Review. Where does it say the technology development lessons learned should be captured after that point?

premise fix: The handbook says technology assessment should play a role from concept development through the Preliminary Design Review (PDR), not the Critical Design Review; the lessons learned are captured in the final phase of the program.

evidence (page 69): "technology assessment needs to play a role throughout the design and development process from concept development through Preliminary Design Review (PDR)."

notes: Wrong milestone: the endpoint named is PDR, not CDR. The follow-up about lessons learned is answered in the next sentence of the same passage, so an agent could reply 'in the final phase of the program' while letting the CDR claim stand.

verdict (keep / fix / drop):

### q0215

question: The end-product verification plan is written inside the Product Verification Process itself, so during which of that process's five major activities is it produced?

premise fix: The verification plan is generated through the Technical Planning Process and baselined before product verification starts; it enters the Product Verification Process as an input rather than being produced by one of its activities.

evidence (page 89): "Verification plan: This plan will have been developed under the Technical Planning Process and baselined before entering this verification."
evidence (page 75): "Product Verification Plan: The end-product verification plan (generated through the Technical Planning Process) provides the content and depth of detail necessary to provide full visibility of all verification activities for the end product."

notes: Wrong owner: the plan belongs to the Technical Planning Process, not the Product Verification Process. The Product Verification Process does have five major activities and one of them is 'prepare to conduct product verification', which could tempt an agent to name it as where the plan is written.

verdict (keep / fix / drop):

### q0218

question: The handbook breaks product validation into three major steps. Which of the three involves writing the validation report?

premise fix: The handbook lists five major steps in the validation process: prepare to conduct validation, perform validation, analyze validation results, prepare a validation report, and capture the validation work products.

evidence (page 100): "There are five major steps in the validation process: (1) preparing to conduct validation, (2) conduct planned validation (perform validation), (3) analyze validation results, (4) prepare a validation report, and (5) capture the validation work products."

notes: Wrong number: the handbook says five steps, not three. A grader should not accept an answer that just says 'the fourth step' or 'prepare a validation report' without rejecting the count of three.

verdict (keep / fix / drop):

