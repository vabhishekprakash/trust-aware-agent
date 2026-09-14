# Blind labelling sheet: 40 items

For each question decide, from the handbook alone, which bucket it belongs to
(answerable, ambiguous, unanswerable, false_premise) and write the short answer,
the two readings, or the corrected premise as the bucket requires, with a page.
Do not open data/eval/blind40_key.jsonl until this sheet is done. The key holds
the drafted labels; agreement between the two is reported in the final report.

## 1. q0004

Across the project life cycle, how many more times does the SE engine cycle its technical management processes than its technical development processes?

bucket:answerable

answer / readings / correction:Two more times. The engine cycles the technical development processes (steps 1 through 9) five times, Pre-Phase A through Phase D, and cycles the technical management processes (steps 10 through 17) seven times, Pre-Phase A through Phase F.

page:9

## 2. q0005

When a product is validated, which document do the validation activities trace back to?

bucket:answerable

answer / readings / correction:The ConOps. The verification/validation comparison box states that validation relates back to the ConOps document, in contrast to verification testing, which relates back to the approved requirements set such as an SRD.

page:89 (reinforced on 99 and 102, where validation confirms conformance to stakeholder expectations as captured in the MOEs, MOPs, and ConOps)

## 3. q0012

During program Formulation, which major reviews lead up to approval at KDP I?

bucket:answerable

answer / readings / correction:The SRR, SDR, PDR, and the governing Program Management Council (PMC) review.

page:20 The sidebar box on the same page lists program Formulation reviews as MCR (marked pre-Formulation), SRR, and SDR, which is a shorter list. I kept this as answerable rather than ambiguous because the body sentence is phrased as the question is ("Major reviews leading to approval at KDP I are…"), so there's a directly responsive statement rather than two competing ones.

## 4. q0014

At what life-cycle cost does the commitment made at the end of Phase B have to be made with Congress and the Office of Management and Budget?

bucket:answerable

answer / readings / correction:A life-cycle cost greater than $250 million. Above that threshold the end-of-Phase-B commitment is made with Congress and OMB, and that external commitment is the Agency Baseline Commitment.

page:25

## 5. q0015

Which readiness reviews are the Phase D activities of a space flight project aimed at preparing for?

bucket:answerable

answer / readings / correction:The Flight Readiness Review (FRR) / Mission Readiness Review (MRR)

page:29. Same near-call shape as q0012: the Phase D box on p. 30 lists TRRs, SAR or pre-Ship Review, and ORR as the phase's reviews. But the question asks what the activities are aimed at preparing for, and p. 29 says exactly that about the FRR/MRR.

## 6. q0018

How high above the Earth does the handbook place geostationary satellites when explaining why they are boosted to a higher orbit instead of deorbited?

bucket:answerable

answer / readings / correction:35,790 km above the Earth. GEO satellites at that altitude can't practically be deorbited, so they're boosted to a higher orbit well beyond the crowded operational GEO belt.

page:33

## 7. q0029

In the handbook's thrust vector controller example, the force requirement carries a tolerance. What is that tolerance as a percentage of the nominal force?

bucket:answerable

answer / readings / correction:1.25 percent. The requirement reads "The TVC shall provide a force of 40,000 pounds, ± 500 pounds," and 500 / 40,000 = 0.0125.

page:56. The handbook gives the tolerance in pounds, not as a percentage, so this needs one division. I'm treating derived-by-arithmetic as answerable, consistent with how q0021 (the $400M Type C/D gap) was scored.

## 8. q0032

Into how many steps does the handbook break the validation of technical requirements?

bucket: answerable

answer / readings / correction:Six steps. They begin with "Are the Requirements Written Correctly?" and run through checking that requirements are complete, satisfy stakeholders, are feasible, and so on.

page:60

## 9. q0036

Up to which milestone review does the handbook say technology assessment should stay involved in the design and development process, starting from concept development?

bucket:answerable

answer / readings / correction:The Preliminary Design Review (PDR). Technology assessment should play a role throughout the design and development process from concept development through PDR, with lessons learned captured in the final phase of the program.

page:69. (Appendix G agrees on p. 207: the final TMA is performed just prior to PDR)

This is the de-trapped version of the earlier item that asserted CDR. Asked neutrally, it has a clean answer.

## 10. q0055

Under which act might environmental documentation or approvals have to be obtained before a site can receive the end product?

bucket: answerable

answer / readings / correction:The National Environmental Policy Act (NEPA). In product transition preparation, NEPA documentation or approvals may need to be obtained prior to receipt of the end product.

page:110

## 11. q0070

When an interface change needs sign-off from every side of the interface, what level of approval does the handbook require?

bucket:answerable

answer / readings / correction:Unanimous approval. For interfaces that require approval from all sides, unanimous approval is required.

page:138

## 12. q0076

What does the handbook call a documented agreement that deliberately releases a program or project from having to meet a requirement?

bucket:answerable

answer / readings / correction:A waiver — "a documented agreement intentionally releasing a program or project from meeting a requirement." The handbook adds that some Centers use deviations before Implementation and waivers during it, and that authorized waivers don't constitute a change to a baseline.

page:149 (glossary entry on 196 is worded slightly differently: a documented authorization releasing a program or project from meeting a requirement after the requirement is put under configuration control)

## 13. q0082

A Production Readiness Review is held when a project is building or buying more than how many similar systems?

bucket:answerable

answer / readings / correction:: More than three. The PRR is for projects developing or acquiring multiple or similar systems greater than three, or as determined by the project.

page:188 (the life-cycle chart footnote on p. 18 adds that a PRR is needed only when there are multiple copies of systems and doesn't require an SRB)

## 14. q0087

When writing requirements, what does using the word 'should' signify according to the handbook's checklist?

bucket:answerable

answer / readings / correction:A goal. The Appendix C checklist gives the convention as: shall = requirement, will = facts or declaration of purpose, should = goal.

page:197

## 15. q0096

How many phases make up the NASA life cycle?

bucket:ambiguous

answer / readings / correction:Reading 1 — the major life-cycle phases: two. NPR 7120.5 defines the major NASA life cycle phases as Formulation and Implementation.
Reading 2 — the incremental project phases: seven. For space flight systems projects, Formulation and Implementation divide into seven incremental pieces: Pre-Phase A (Concept Studies), Phase A, Phase B, Phase C, Phase D, Phase E, and Phase F.

page:18 (both readings sit in the same paragraph)

## 16. q0100

By when does a project need to have its Technology Development Plan in place?

bucket:ambiguous

answer / readings / correction:Reading 1 — by KDP A (end of Pre-Phase A): The Pre-Phase A activity box lists "Develop and baseline Technology Development Plan" (p. 22), and Table G.1-1 states that at KDP A the "Technology Development Plan is baselined that identifies technologies to be developed, heritage systems to be modified, alternative paths…" (p. 207). At KDP B it is only updated.
Reading 2 — by KDP B (transition from Phase A to Phase B): The glossary defines it as "a document required for transition from Phase A to Phase B" (p. 194).

page:22, 207, 194

Reading 1 has two independent supports and Reading 2 has one, so if you want a single scored answer I'd make Reading 1 primary. But the glossary genuinely says something different, so a response citing p. 194 isn't wrong about the document.

## 17. q0101

When is the concept of operations baselined?

bucket:ambiguous

answer / readings / correction:adings:

Pre-Phase A: the activity box lists "Develop and baseline the Concept of Operations" (p. 22).
Phase A: Phase A takes the concepts and draft requirements validated in Pre-Phase A and fleshes them out "to become the set of baseline system requirements and ConOps" (p. 10).
Phase B: Appendix R's HSI activity table lists ConOps as Preliminary in Pre-Phase A, initial in Phase A, and baseline in Phase B (p. 250).

page:22, 10, 250

This one is worse than a two-way split — the handbook gives three different phases. Appendix R is the most granular and is internally consistent (preliminary → initial → baseline), but it contradicts the Pre-Phase A box outright. Worth deciding how you want to score it before it goes in the set.

## 18. q0102

In which project phase is the decommissioning plan developed?

bucket:ambiguous

answer / readings / correction:Reading 1 — Phase E: Phase F's purpose is "to implement the systems decommissioning/disposal plan developed in Phase E" (Table 2.2-1, p. 9; repeated p. 33).
Reading 2 — Phase B, baselined in Phase D: The Phase B box lists "Develop preliminary plans >> Decommissioning Plan" (p. 26). Table 3.0-1 shows decommissioning plans as Preliminary at PDR, CDR, and SIR, then Baseline at ORR (p. 19), and Appendix K's plan table shows Approach at PDR and Baseline at ORR (p. 235).

page:9 and 33, versus 26, 19, and 235

The tension is real: the Phase F purpose statement says Phase E, but three separate maturity tables put development in Phase B and baselining in Phase D.

## 19. q0103

Which review has to be completed before hardware production can begin in Phase C?

bucket:ambiguous

answer / readings / correction:Reading 1 — CDR: "A CDR for each end item should be held prior to the start of fabrication/production for hardware and prior to the start of coding of deliverable software products" (p. 29).
Reading 2 — PRR: "If there is a production run of products, a PRR will be performed to ensure the production plans, facilities, and personnel are ready to begin production" (p. 29).

page:29 (both sentences, same paragraph)

CDR is the general gate; PRR is the conditional one that applies only when there's a production run of more than three similar systems. Both are stated as preceding production.

## 20. q0109

Who is responsible for writing the ops concept?

bucket:answerable

answer / readings / correction:The systems engineer. "The systems engineer usually plays the key role in leading the development of the concept of operations (ConOps) and resulting system architecture, defining boundaries, defining and allocating requirements, evaluating design tradeoffs…"

page:4

Slight looseness: the handbook says the systems engineer leads the development, not that they write it, and hedges with "usually." I'd accept either phrasing.

## 21. q0110

Which system design process produces the measures used to judge whether the system does what it needs to?

bucket:answerable

answer / readings / correction:The Stakeholder Expectations Definition Process, which produces the Measures of Effectiveness (MOEs) — "measures that represent expectations that are critical to the success of the system, and failure to satisfy these measures will cause the stakeholder to deem the system unacceptable." Table 3.0-1 shows MOE definition approved at MCR.

page:52 (also 19, 53)

Near-call: if "does what it needs to" is read as technical performance rather than stakeholder success, the answer becomes MOPs from the Technical Requirements Definition Process (p. 61). I kept it answerable because "does what it needs to" maps to the MOE definition's language about stakeholder acceptability, but the question would be tighter if it said "critical to the success of the system."

## 22. q0112

During validation, what is actually being compared against the stakeholder expectations?

bucket:answerable

answer / readings / correction:The end product itself — each implemented or integrated and verified end product, from the lowest end product in a system structure branch up to the top-level system. The Product Validation Process demonstrates that the end product satisfies its stakeholder expectations (MOEs) within the intended operational environments.

page:100

## 23. q0135

Which NASA Centers have chosen to certify to the AS9100 quality system?

bucket:unanswerable

answer / readings / correction:No Centers are named. Page 8 says only that "Some NASA Centers have chosen to certify to the AS9100 quality system and may require their contractors to follow NPR 7123.1."

page:8(the closest passage, which stops short of the answer)

## 24. q0140

When was the Mars Science Laboratory, one of the large traditional projects the tailoring discussion contrasts with small projects, launched?

bucket:unanswerable

answer / readings / correction:No launch date is given. MSL appears once, on p. 34, in a list of large traditional projects (alongside the Shuttle, ISS, and Hubble) that small projects are contrasted with, and once as a Type A example in Table 3.11-1. No dates attached.

page:34 (nearest mention)

## 25. q0141

How many days before a life cycle review like PDR does the handbook say the review material has to be delivered to the board?

bucket:unanswerable

answer / readings / correction:No delivery deadline is stated. The handbook discusses review preparation and points to NPR 7123.1 for entrance and success criteria, but gives no number of days for getting material to the board.

page:Not available

## 26. q0142

How many slides are in the milestone review presentation templates that the NASA Engineering Network SE Community of Practice provides?

bucket:unanswerable

answer / readings / correction:No slide count. Page 1 says the NEN SE Community of Practice site "includes many resources useful to systems engineers, including document templates for many of the work products and milestone review presentations required by NPR 7123.1," and stops there.

page:1 (nearest mention)

## 27. q0148

What fraction of a project's total cost is typically consumed by verification activities?

bucket:unanswerable

answer / readings / correction:No fraction or percentage is given. Page 91 says verification activities "can be significant drivers of a project's cost and schedule" and that the implications should be considered early, but quantifies nothing.

page:91 (nearest mention)

## 28. q0149

What proportion of a project's requirements should be verified by test rather than by analysis?

bucket:unanswerable

answer / readings / correction:No proportion is given. The handbook lists the verification methods (analysis, inspection, demonstration, test) and says method selection depends on life-cycle phase, position in the system structure, and the form of the product, but never prescribes a test-versus-analysis split.

page:93 and 123 (nearest discussion)

## 29. q0151

What scheduling software does the handbook suggest using to build and maintain a project's network schedule?

bucket:unanswerable

answer / readings / correction:No software is named. Page 121 says only that "use of a scheduling tool may facilitate the development and maintenance of the schedule," and refers the reader to NASA/SP-2010-3403, NASA Schedule Management Handbook, for more on scheduling.

page:121 (nearest mention)

## 30. q0174

How many degrees beyond the expected flight temperature range must a qualification unit be tested?

bucket:unanswerable

answer / readings / correction:No temperature figure is given. The Types of Hardware box says a qualification unit "will be exposed to the extremes of the environmental criteria (thermal, vibration, etc.)" and that it typically isn't flown, and Appendix I says the V&V plan should describe how minimum and maximum extremes will be determined for various test types — but the handbook sets no degree margin itself.

page:124 (also 218)

## 31. q0181

How many processes does ANSI/EIA-632 define, and how does that count compare with the 17 processes in NPR 7123.1?

bucket:unanswerable

answer / readings / correction:No process count is given, and no comparison is drawn. ANSI/EIA-632, Processes for Engineering a System (Arlington, VA, 1999), appears only in the bibliography, along with a secondary Martin reference describing the standard. The handbook never states how many processes it defines or relates that number to NPR 7123.1's 17.

page:270 and 278 (the only mentions)

## 32. q0189

What specific systems engineering lesson did NASA take away from the Genesis mission and fold into this handbook?

bucket:unanswerable

answer / readings / correction: No specific lesson is stated. The preface says lessons learned "were garnered from the robotic missions such as Genesis and the Mars Reconnaissance Orbiter as well as from mishaps from ground operations and the commercial space flight industry," and moves on. Genesis appears exactly once in the whole document, in that sentence.
page:viii (the only mention)

## 33. q0193

Since the handbook makes the systems engineer the one responsible for identifying and controlling the project's cost and schedule, what does it leave for the PP&C function to do?

bucket:false_premise

answer / readings / correction:The question reverses the two roles. Page 4: "The Project Planning and Control (PP&C) function is responsible for identifying and controlling the cost and schedules of the project." Systems engineering is "focused on the technical characteristics of decisions including technical, cost, and schedule and on providing these to the project manager." Where SE and PP&C overlap, "SE provides the technical aspects or inputs whereas PP&C provides the programmatic, cost, and schedule inputs." The systems engineer and supporting organization support PP&C with accurate and timely cost and schedule information for the technical activities; they don't own cost and schedule control.

page:4

## 34. q0196

The handbook's life-cycle cost curve shows roughly 75% of a project's cost already spent by the time design is done; what share of the total does it say those design decisions commit?

bucket:false_premise

answer / readings / correction:The two figures are swapped. Page 12: "the figure shows that during design, only about 15% of the costs might be expended, but the design itself will commit about 75% of the life cycle costs." So 75% is the committed share, not the spent share; roughly 15% is spent by that point (8% at the concept stage). The handbook explains the gap: how the system is designed determines how expensive it will be to test, manufacture, integrate, operate, and sustain. It also notes the numbers vary from project to project, and that the figure came from the Defense Acquisition University.

page:12, with Figure 2.5-1 on 13

## 35. q0197

Since NPR 7120.7 is the directive that defines the life cycle for NASA space flight projects, what two major phases does that directive split the life cycle into?

bucket: false_premise

answer / readings / correction:NPR 7120.7 is the directive for information technology, not space flight. Page 16 lists the governing documents: NPR 7120.5 for space flight projects, NPR 7120.7 for information technology, NPR 7120.8 for research and technology, NPR 7150.2 for software. The two major phases are Formulation and Implementation, but that split is NPR 7120.5's, not 7120.7's.

page:16 (governing documents), 18 (Formulation and Implementation)

## 36. q0200

Since the handbook says the system-level CDR is normally held first and the lower-level CDRs follow it, what about the next phase does it say that top-down order reflects?

bucket:false_premise

answer / readings / correction:The order is the other way round. Page 29: "Typically, the sequence of CDRs reflects the integration process that will occur in the next phase; that is, from lower level CDRs to the system-level CDR." So lower-level CDRs come first and the system-level CDR follows. What the order reflects — the part the question actually asks about — is the integration process that will occur in the next phase. The handbook adds that projects should tailor the sequencing to their own needs.

page:29

## 37. q0201

Since the handbook limits the Post-Flight Assessment Review to robotic missions, in which life-cycle phase is that review listed?

bucket:false_premise

answer / readings / correction:The PFAR is limited to human space flight, not robotic missions. The Phase E review list reads "Post-Flight Assessment Review (PFAR) (human space flight only)." The phase itself is right: PFAR is listed under Phase E, Operations and Sustainment, alongside PLAR, CERR, DR, system upgrade review, and safety review.

page:32

## 38. q0213

Since the handbook says the drive toward better design resolution is formalized in Phase C by defining a baseline system definition, what is usually baselined as the requirements portion of that baseline?

bucket:false_premise

answer / readings / correction:It's Phase B, not Phase C. Page 72: "It is reasonable to expect the system to be defined with better resolution as time passes. This tendency is formalized at some point (in Phase B) by defining a baseline system definition." The rest of the question has a real answer: "Usually, the goals, objectives, and constraints are baselined as the requirements portion of the baseline." The entire baseline is then placed under configuration control so subsequent changes are controlled.

page:72

## 39. q0214

Because the handbook makes baselining the design solution the opening step of the Design Solution Definition Process, how does it recommend keeping alternative concepts open after the baseline is set?

bucket:false_premise

answer / readings / correction:Baselining is the last step, not the opening one, so the question's mechanism doesn't arise. Page 74: "While baselining a design is beneficial to the design process, there is a danger if it is exercised too early in the Design Solution Definition Process… Baselining too early takes the inventive nature out of the concept exploration. Therefore, baselining should be one of the last steps in the Design Solution Definition Process." The handbook keeps alternatives open by deferring the baseline, not by any post-baseline mechanism: early exploration of alternative designs should be free and open to a wide range of ideas, concepts, and implementations.

page:74

## 40. q0217

Given that acceptance testing, like qualification, is run only once per design no matter how many flight units are built, what goes into the single Acceptance Data Package for the design?

bucket:false_premise

answer / readings / correction:Acceptance is the per-unit activity; qualification is the once-per-design one. Page 90: "Qualification is performed once regardless of how many flight units may be generated (as long as the design doesn't change)," whereas the selected acceptance activities "are performed on each of the flight units as they are manufactured and readied for flight/use," and "Acceptance testing is performed for each flight unit produced." There is no single Acceptance Data Package per design: "An Acceptance Data Package is prepared for each of the flight units and shipped with the unit." Its purpose is to show that the manufacturing and workmanship of that unit conform to the design previously verified and qualified.

page:90 (the Acceptance Data Package is also referenced at 80, where personnel training is called a key part of it)

