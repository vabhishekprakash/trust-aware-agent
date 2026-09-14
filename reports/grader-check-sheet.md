# Blind grader check

40 drafts written by qwen2.5:3b-instruct for handbook questions, in a mixed order.
For each one, read the question and the reference, then grade the draft CORRECT, PARTIAL
or WRONG by the rules in docs/annotation-guide.md, and write it after 'grade:'. Do not
open data/eval/grader_check_key.jsonl until the sheet is done. The judge's grades sit
there, and scripts/compare_grader_check.py reports agreement on the binary label.

The drafts come from three conditions the model does not know it is in: the item's own
evidence passage, no passage, and a passage from a different item. That is how the set
spans correct, wrong and borderline without anyone picking drafts by hand.

### 1

question: In what year did the Space Shuttle Program, whose Transition Management Plan is given as a closeout example, fly its last mission?

reference: the handbook does not answer this question

draft: The passage does not provide information about when the Space Shuttle Program's last mission flew.

grade:

### 2

question: In what month and year did NASA change its risk management approach to make it more proactive?

reference: reference answer: December 2008
reference: acceptable forms: 2008; December of 2008; Dec 2008; December, 2008

draft: NASA changed its risk management approach in December of 2008 to make it more proactive.

grade:

### 3

question: What joint cost and schedule confidence level must the Agency Baseline Commitment be funded to at KDP C?

reference: the handbook does not answer this question

draft: The passage does not provide information about joint cost and schedule confidence levels, nor does it mention anything related to Agency Baseline Commitments or KDP C.

grade:

### 4

question: Which Department of Defense acquisition milestones correspond to NASA's Key Decision Points?

reference: the handbook does not answer this question

draft: NASA's Key Decision Points (KDPs) are analogous to certain Department of Defense acquisition milestones, though they do not exactly match all DoD-specific stages. The closest equivalents in terms of major decision points and risk acceptance would be considered the Program Review and System Definition Reviews for NASA.

grade:

### 5

question: What minimum mass margin percentage should a hardware project be holding at PDR?

reference: the handbook does not answer this question

draft: The passage does not provide information about the minimum mass margin percentage or any details related to PDR (Pre-Development Review) for hardware projects.

grade:

### 6

question: Which milestone review is the verification plan baselined at?

reference: reference answer: PDR
reference: acceptable forms: Preliminary Design Review; the Preliminary Design Review (PDR); at PDR

draft: The verification plan is baselined at the Preliminary Design Review (PDR).

grade:

### 7

question: What name does the handbook give to the formal practice of rerunning earlier acceptance tests, mostly for software, to check that a fix has not broken something that previously worked?

reference: reference answer: regression testing
reference: acceptable forms: regression test; regression tests; regression

draft: The NASA Systems Engineering Handbook does not provide a specific name for the formal practice of rerunning earlier acceptance tests, especially for software.

grade:

### 8

question: Which commercial software package does the handbook recommend purchasing for configuration status accounting?

reference: the handbook does not answer this question

draft: The NASA Systems Engineering Handbook does not specifically recommend a commercial software package for configuration status accounting; it provides guidance on best practices rather than specific tool recommendations.

grade:

### 9

question: The handbook wants technology assessment to keep running from concept development all the way through the Critical Design Review. Where does it say the technology development lessons learned should be captured after that point?

reference: the question's assumption is false; the handbook says: The handbook says technology assessment should play a role from concept development through the Preliminary Design Review (PDR), not the Critical Design Review; the lessons learned are captured in the final phase of the program.

draft: The NASA Systems Engineering Handbook does not specify where technology development lessons learned should be captured after the Critical Design Review.

grade:

### 10

question: Which NASA requirements document says data management planning has to appear either in the program/project plan, in the CM plan, or as a standalone document?

reference: reference answer: NPR 7120.5
reference: acceptable forms: NPR7120.5; 7120.5; NASA Procedural Requirements 7120.5

draft: The NASA Systems Engineering Handbook (SEH) requires that data management planning be included in the Program/Project Plan, the Configuration Management Plan, or as a separate document. This is outlined in the SEH guidelines for ensuring comprehensive and integrated project management practices.

grade:

### 11

question: What kind of hardware unit matches the flight unit in form, fit, function and components but gets exposed to environmental extremes and is usually not flown?

reference: reference answer: qualification unit
reference: acceptable forms: Qualification Unit; a qualification unit; qual unit

draft: The hardware unit that matches a flight unit in form, fit, and function but is subjected to environmental extremes and is typically not flown is called a Ground Test Unit (GTU).

grade:

### 12

question: Which two life-cycle reviews does the handbook give as an example of reviews a small project might merge into one without needing a waiver from the SE NPR?

reference: reference answer: the SRR and the SDR (or MDR)
reference: acceptable forms: SRR and SDR; System Requirements Review and System Definition Review; SRR and SDR/MDR; SRR and MDR; System Requirements Review and Mission Definition Review; the System Requirements Review and the System Definition Review (or Mission Definition Review)

draft: The NASA Systems Engineering Handbook suggests that for small projects, certain high-level reviews such as System Requirements Review (SRR) and Preliminary Design Review (PDR) could be merged into a single review to streamline processes while still maintaining essential oversight.

grade:

### 13

question: What example does the handbook give of an enabling product whose use a project would acquire during the test phase of a space flight system?

reference: reference answer: an environmental test chamber
reference: acceptable forms: environmental test chamber; test chamber; an environmental chamber

draft: The handbook does not provide an example of an enabling product for the test phase in the context of space flight systems.

grade:

### 14

question: How many members does a Standing Review Board normally have?

reference: the handbook does not answer this question

draft: The passage does not provide information about the number of members in a Standing Review Board.

grade:

### 15

question: Which review does the handbook say is typically held so stakeholders can comment on and agree to the requirement set before it gets baselined?

reference: reference answer: System Requirements Review (SRR)
reference: acceptable forms: SRR; System Requirements Review; the SRR; a System Requirements Review

draft: The System Requirements Review (SRR) is typically held according to the NASA Systems Engineering Handbook.

grade:

### 16

question: The handbook lists five key steps for carrying out functional analysis when decomposing requirements. What does the fifth step involve?

reference: the question's assumption is false; the handbook says: The handbook gives three key steps for functional analysis: translating top-level requirements into functions, decomposing and allocating the functions to lower levels of the product breakdown structure, and identifying and describing functional and subsystem interfaces.

draft: The passage provided does not contain information about functional analysis or any specific steps involved in it.

grade:

### 17

question: Which contractor was handling the NOAA N-Prime spacecraft when the mishap covered by the cited investigation report happened?

reference: the handbook does not answer this question

draft: The passage does not provide information about which contractor handled the NOAA N-Prime spacecraft or details of a specific mishap investigation.

grade:

### 18

question: What is the dollar cost cap on projects selected through an Announcement of Opportunity in an uncoupled program?

reference: the handbook does not answer this question

draft: The passage does not provide information about the dollar cost cap on projects selected through an Announcement of Opportunity in an uncoupled program.

grade:

### 19

question: Which Phase D review signs off that the system is ready?

reference: reading 1: ready to be accepted and shipped to the launch site or operational facility -> the System Acceptance Review (SAR) or pre-Ship Review (page 162)
reference: reading 2: ready for a safe and successful flight or launch -> the Flight Readiness Review (FRR) (Mission Readiness Review for some missions) (page 163)

draft: The FRR (Flight Readiness Review) phase signs off that the system is ready.

grade:

### 20

question: Since MOPs are the stakeholder-facing measures written from the customer's point of view, what does the handbook call the more technical, supplier-oriented measures that get derived from them?

reference: the question's assumption is false; the handbook says: MOPs are themselves derived from the MOEs and are stated in more technical terms from the supplier's point of view; the MOEs are the higher-level stakeholder measures, and TPMs are the critical subset established from the MOPs.

draft: The NASA Systems Engineering Handbook refers to these as "MOMs" (Measurement of Performance), which are the more technical, supplier-oriented measures derived from the MOPs (Measurements of Performance).

grade:

### 21

question: Using the cost guidance in the handbook's example program/project types table, by how many dollars does the top of the Type C life-cycle cost range exceed the top of the Type D range?

reference: reference answer: $400M
reference: acceptable forms: 400M; $400 million; 400 million; 400 million dollars; about $400M; ~$400M

draft: The passage does not provide information about cost guidance for program/project types or specific ranges for life-cycle costs. Therefore, it cannot answer how much one cost range exceeds another.

grade:

### 22

question: In the comparison of verification and validation testing, which document does validation testing trace back to?

reference: reference answer: the ConOps
reference: acceptable forms: ConOps; ConOps document; the Concept of Operations; Concept of Operations; concept of operations document

draft: Validation testing is traced back to requirements documentation, ensuring that the system meets its intended objectives as specified in the requirements.

grade:

### 23

question: In the SAE/EIA-649-2 configuration management requirements NASA has endorsed, how many more underlying principles are there than configuration management functions?

reference: reference answer: 32
reference: acceptable forms: thirty-two; 32 more; 32 more principles than functions

draft: The SAE/EIA-649-2 standard for configuration management includes 13 underlying principles in addition to its specific configuration management functions, which adds up to a total of 18 elements. Therefore, there are 5 additional underlying principles beyond the configuration management functions endorsed by NASA.

grade:

### 24

question: What is the minimum number of alternatives the decision analysis process requires before a trade study can be run?

reference: the handbook does not answer this question

draft: The NASA Systems Engineering Handbook does not specify the minimum number of alternatives required before running a trade study.

grade:

### 25

question: If I need entrance and exit criteria for the milestone reviews of a software project, which NASA document does the SE handbook point me to?

reference: reference answer: NASA-HDBK-2203, NASA Software Engineering Handbook
reference: acceptable forms: NASA-HDBK-2203; NASA HDBK 2203; NASA Software Engineering Handbook; the NASA Software Engineering Handbook (NASA-HDBK-2203)

draft: The NASA Systems Engineering Handbook does not say anything about entrance and exit criteria for milestone reviews in software projects.

grade:

### 26

question: How many months does the handbook expect Phase B, preliminary design and technology completion, to last for a Type A mission?

reference: the handbook does not answer this question

draft: The NASA Systems Engineering Handbook passage does not provide information about the duration of Phase B or any other phases relative to the type of mission.

grade:

### 27

question: For how many years after a system is retired must its technical data be kept?

reference: the handbook does not answer this question

draft: The passage does not provide information about the number of years technical data must be kept after a system is retired.

grade:

### 28

question: Which contractor built the Orion test article used in the water impact test shown on the handbook cover?

reference: the handbook does not answer this question

draft: The passage does not provide information about which contractor built the Orion test article.

grade:

### 29

question: In Phase E, who chairs the Configuration Control Board that oversees the transition of new operational capabilities?

reference: reference answer: the mission operations manager or the project manager
reference: acceptable forms: mission operations manager or project manager; the mission operations manager or project manager; either the mission operations manager or the project manager; the mission operations manager, or the project manager

draft: In Phase E, the Configuration Control Board that oversees the transition of new operational capabilities is chaired by the mission operations manager or the project manager.

grade:

### 30

question: Roughly how much does it cost to advance a critical technology by one TRL step according to the Technology Assessment process?

reference: the handbook does not answer this question

draft: The exact costs can vary significantly depending on many factors, but generally, advancing a critical technology by one Technology Readiness Level (TRL) step through the NASA Technology Assessment process involves substantial investments in research and development.

grade:

### 31

question: Which of the product realization processes comes last, acting as the bridge from one system level up to the next?

reference: reference answer: the Product Transition Process
reference: acceptable forms: Product Transition; Product Transition Process; product transition

draft: The process that acts as the bridge from one system level up to the next and is typically considered the last of the product realization processes in systems engineering is the System Level Design Review (SLDR).

grade:

### 32

question: What is AS9100 and which industry was it created for?

reference: reference answer: a quality management system developed for the commercial aerospace industry
reference: acceptable forms: a widely adopted and standardized quality management system for the commercial aerospace industry; quality management system; commercial aerospace industry; aerospace quality management system; a quality management system (QMS) developed for the commercial aerospace industry; a QMS for the commercial aerospace industry; QMS; commercial aerospace industry

draft: AS9100, developed by the Aerospace Industries Association (AIA), is a quality management system standard specifically tailored for the aerospace and defense industries to ensure product safety and reliability.

grade:

### 33

question: Since the OCE is the approver for a waiver requested by a project whose responsibility was delegated to a Center, where should the project record the approved tailoring afterwards?

reference: the question's assumption is false; the handbook says: For a program or project delegated to a Center, the Center Director or designee approves the waiver or deviation; the OCE approves Center-level tailoring for standard use at the Center.

draft: The passage does not provide information on where the project should record the approved tailoring after it has been requested and approved by the OCE.

grade:

### 34

question: Which commercial space flight mishaps supplied the lessons learned that fed the Office of the Chief Engineer's systems engineering initiative?

reference: the handbook does not answer this question

draft: The passage does not say anything about commercial space flight mishaps or lessons learned from such incidents. Therefore, it cannot answer which specific mishaps supplied those lessons.

grade:

### 35

question: According to the handbook's definitions of needs, goals and objectives, how many criteria should an objective generally satisfy?

reference: reference answer: 4
reference: acceptable forms: four; four criteria; 4 criteria

draft: The handbook states that each objective should generally satisfy four criteria.

grade:

### 36

question: Who receives an end product when it goes through the Product Transition Process?

reference: reading 1: a lower-level end product being transitioned for integration -> the customer at the next level up in the system structure (page 106)
reference: reading 2: the top-level (final) end product -> the intended end user who will use it in its operational environment (page 108)

draft: The passage does not provide information about who receives an end product during the Product Transition Process.

grade:

### 37

question: Who normally approves a change to project information that is held under configuration control?

reference: reference answer: a Configuration Control Board
reference: acceptable forms: Configuration Control Board; CCB; the CCB; a CCB via a Change Request; Configuration Control Board (CCB)

draft: A Configuration Control Board normally approves changes to project information that is held under configuration control.

grade:

### 38

question: Which review clears the system to start operating?

reference: reading 1: readiness to assume normal operations of the deployed system, checked before flight -> the Operational Readiness Review (ORR) (page 163)
reference: reading 2: readiness to proceed with routine in-space operations after launch and checkout -> the Post-Launch Assessment Review (PLAR) (page 163)

draft: The flight readiness review (FRR) is the final major systems engineering and management process that clears a spaceflight vehicle, its crew, and associated operations for launch after all design, development, manufacturing, integration, test, and verification activities have been completed.

grade:

### 39

question: When a flight-proven heritage unit is reused in a different architecture and environment, by how many TRL levels does its rating initially fall?

reference: reference answer: 4
reference: acceptable forms: four; 4 levels; four levels; from TRL 9 to TRL 5; 9 to 5

draft: When a flight-proven heritage unit is reused in a different architecture and environment, its Technical Readiness Level (TRL) typically falls by one or two TRL levels to account for the potential changes in performance, reliability, and integration challenges.

grade:

### 40

question: Which review checks that the system is ready to be disposed of?

reference: reading 1: the review near the end of mission operations that assesses readiness for decommissioning and disposal -> the Decommissioning Review (DR) (page 164)
reference: reading 2: the review held when major assets are ready for final disposal -> the Disposal Readiness Review (DRR) (page 164)

draft: The passage does not contain information about any review checks for disposing of a system.

grade:

