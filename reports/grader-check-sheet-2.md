# Blind grader check

25 drafts written by qwen2.5:3b-instruct for handbook questions, in a mixed order.
For each one, read the question and the reference, then grade the draft CORRECT, PARTIAL
or WRONG by the rules in docs/annotation-guide.md, and write it after 'grade:'. Do not
open data/eval/grader_check_key.jsonl until the sheet is done. The judge's grades sit
there, and scripts/compare_grader_check.py reports agreement on the binary label.

The drafts come from three conditions the model does not know it is in: the item's own
evidence passage, no passage, and a passage from a different item. That is how the set
spans correct, wrong and borderline without anyone picking drafts by hand.

### 1

question: According to the handbook, what are Measures of Performance derived from?

reference: reference answer: Measures of Effectiveness (MOEs)
reference: acceptable forms: MOEs; MOE; Measures of Effectiveness; the MOEs; measures of effectiveness

draft: Measures of Performance (MOPs) are derived from Measures of Excellence (MOEs).

grade:

### 2

question: NPR 7123.1 groups its common technical processes into three sets. What are they?

reference: reference answer: system design, product realization, and technical management
reference: acceptable forms: system design processes, product realization processes, and technical management processes; system design; product realization; technical management; design, realization, and technical management

draft: The NPR 7123.1 categorizes its common technical processes into three main sets: System Definition, System Design, and System Development.

grade:

### 3

question: For a mission that has to follow NPR 7120.5, what does the handbook suggest using as the starting point for deciding how formal the verification approach should be?

reference: reference answer: NASA payload classification (NPR 8705.4)
reference: acceptable forms: NASA payload classification; payload classification; NPR 8705.4; Risk Classification for NASA Payloads; the A-D payload classification; A–D payload classification; NPR 8705.4 payload classification guidelines

draft: The NASA Systems Engineering Handbook does not say anything about performance metrics addressing the level of formality in verification approaches for missions following NPR 7120.5.

grade:

### 4

question: What characteristic makes a requirement count as a key driving requirement?

reference: reference answer: it can have a large impact on cost or schedule when implemented
reference: acceptable forms: large impact on cost or schedule; can have a large impact on cost or schedule; large cost or schedule impact; big impact on cost or schedule when implemented

draft: A requirement is considered a key driving requirement if it significantly impacts mission success, safety, cost, schedule, and/or technical performance, often serving as the primary basis for design decisions.

grade:

### 5

question: With the project manager leading the technical team, what does the handbook say the systems engineer concentrates on instead?

reference: the question's assumption is false; the handbook says: The handbook says the technical team is led by the systems engineer, while the project manager concentrates on managing the overall project life cycle.

draft: The handbook suggests that with a strong project manager and technical team leadership, the systems engineer focuses on strategic planning, risk management, integration of subsystems, and ensuring compliance with system requirements throughout the lifecycle.

grade:

### 6

question: What workforce rate should be applied to direct labor hours when building the baseline budget from the WBS?

reference: the handbook does not answer this question

draft: The passage does not provide information about workforce rates or how to apply them to direct labor hours for building a baseline budget from the WBS.

grade:

### 7

question: NPD 8010.3 is the directive the handbook cites for removing robotic satellites from orbit at the end of their useful life; what does it say to do with satellites in geostationary orbit?

reference: the question's assumption is false; the handbook says: The handbook cites NPR 8715.6, NASA Procedural Requirements for Limiting Orbital Debris, for removing Earth-orbiting robotic satellites at end of life; NPD 8010.3 concerns notification of intent to decommission or terminate operating space systems.

draft: NPD 8010.3 directs that robotic satellites be deorbited to ensure they do not pose a reentry hazard, while for satellites in geostationary orbit, the directive emphasizes careful and controlled disposal or deorbiting to prevent environmental contamination of sensitive regions on Earth's surface.

grade:

### 8

question: Which verification methods does the handbook's requirements metadata table list under the verification method entry?

reference: reference answer: test, inspection, analysis, demonstration
reference: acceptable forms: test, inspection, analysis, and demonstration; test, analysis, inspection, demonstration; inspection, analysis, demonstration, test; testing, inspection, analysis, demonstration

draft: The handbook does not say which verification methods the requirements metadata table lists under the verification method entry.

grade:

### 9

question: Who signs off on tailoring of the SE NPR requirements when it is submitted through a Compliance Matrix?

reference: reading 1: a Center tailoring the NPR requirements for standard use across the Center (Appendix H.1) -> the Office of the Chief Engineer (OCE) (page 40)
reference: reading 2: a program or project delegated to a Center seeking a waiver or deviation (Appendix H.2) -> the Center Director or designee (page 40)

draft: The final approval for tailoring of the System Engineering (SE) NPR requirements, when submitted via a Compliance Matrix, typically comes from the appropriate level of management or the project manager who has overall responsibility for the compliance and implementation of these requirements.

grade:

### 10

question: After an end product is built, what does it have to be shown to satisfy before it moves on?

reference: reading 1: Product Verification -> all of its specified requirements (page 90)
reference: reading 2: Product Validation -> stakeholder expectations (MOEs) in the intended operational environment (page 100)

draft: The end product has to be shown to satisfy its stakeholders' expectations within the intended operational environments before moving on.

grade:

### 11

question: By what percentage are baselined requirements allowed to grow before the project is supposed to take corrective action?

reference: the handbook does not answer this question

draft: The NASA Systems Engineering Handbook does not specify a percentage by which baseline requirements are allowed to grow before corrective action is required.

grade:

### 12

question: When selecting a technical team, which engineering skills do human-rated systems usually require beyond what robotic space missions need?

reference: reference answer: human systems discipline engineering and environmental control and life support subsystem engineering
reference: acceptable forms: human systems engineering and environmental control and life support (ECLS) engineering; human systems and ECLSS engineering; human systems discipline engineering plus environmental control and life support subsystem engineering

draft: The passage does not provide information about the specific engineering skills required for human-rated systems versus robotic space missions.

grade:

### 13

question: Because the handbook treats an authorized waiver as a minor engineering change to the baseline, whose approval does it need when the waiver touches an external interface?

reference: the question's assumption is false; the handbook says: A waiver is a documented agreement releasing a program or project from meeting a requirement, and authorized waivers do not constitute a change to a baseline.

draft: The NASA Systems Engineering Handbook does not specify whose approval an authorized waiver needs when it touches an external interface.

grade:

### 14

question: The handbook breaks product validation into three major steps. Which of the three involves writing the validation report?

reference: the question's assumption is false; the handbook says: The handbook lists five major steps in the validation process: prepare to conduct validation, perform validation, analyze validation results, prepare a validation report, and capture the validation work products.

draft: The passage does not provide information about breaking product validation into specific steps or which step involves writing a validation report.

grade:

### 15

question: Who wrote the original 1995 edition of NASA SP-6105?

reference: the handbook does not answer this question

draft: The passage does not specify who wrote the original 1995 edition of NASA SP-6105.

grade:

### 16

question: Who has to agree on what level of risk is acceptable for a project?

reference: reading 1: the risk posture that has to be understood before tailoring the SE requirements -> the project, the customer/stakeholder, Center management, and independent reviewers (page 34)
reference: reading 2: 'acceptable risk' as the handbook defines the term -> the program/project, the governing authority, the mission directorate, and other customer(s) (page 176)

draft: The passage does not provide information about who agrees on the acceptable level of risk for a project.

grade:

### 17

question: Because the Physical Configuration Audit has to be finished before the Functional Configuration Audit can begin, what documentation does the FCA verify the product against?

reference: the question's assumption is false; the handbook says: The handbook states the reverse order: the FCA precedes the PCA of the configured product, and the FCA checks test results against the functional baseline documentation approved at PDR and CDR.

draft: The passage does not provide information about what documentation the FCA verifies the product against.

grade:

### 18

question: Which NASA official signed NPR 7123.1 into effect?

reference: the handbook does not answer this question

draft: NPR 7123.1, which is a critical document for systems engineering at NASA, was signed into effect by the Associate Administrator for Human Exploration and Operations (HAO).

grade:

### 19

question: How many months before the planned end of mission should the Decommissioning Review be scheduled?

reference: the handbook does not answer this question

draft: The passage does not provide information about when the Decommissioning Review should be scheduled relative to the planned end of mission.

grade:

### 20

question: Because the project plan is a subordinate document to the SEMP, what does the handbook say the project plan is allowed to define on its own?

reference: the question's assumption is false; the handbook says: The handbook says the SEMP is a subordinate document to the project plan, not the other way round.

draft: The NASA Systems Engineering Handbook states that while the project plan is a subordinate document to the System Engineering Management Plan (SEMP), it can define specific project-specific tasks and activities not covered by the broader SEMP.

grade:

### 21

question: How many proficiency levels does NASA's systems engineering competency model attach to each competency?

reference: reference answer: 4
reference: acceptable forms: four; four levels; 4 levels; four proficiency levels; 4 levels of proficiency

draft: The passage does not provide information about how many proficiency levels NASA's systems engineering competency model attaches to each competency.

grade:

### 22

question: Which document do all of a project's plans have to comply with?

reference: reading 1: the technical plans (verification, validation, CM, risk, etc.) -> the project SEMP (page 123)
reference: reading 2: the whole planning hierarchy including the SEMP itself -> the project plan (page 116)

draft: The handbook does not say which document all of a project's plans have to comply with.

grade:

### 23

question: In which project phase does the handbook say issuing technical work directives to cost account managers is essential?

reference: reference answer: Phase B
reference: acceptable forms: B; during Phase B; Phase B of a project

draft: The NASA Systems Engineering Handbook says that issuing technical work directives is essential in Phase B of a project.

grade:

### 24

question: Who is supposed to chair NASA's internal Configuration Control Board?

reference: reference answer: someone with program/project change authority
reference: acceptable forms: a person with program or project change authority; someone who has program/project change authority; a person holding change authority for the program or project

draft: The Configuration Control Board (CCB) at NASA is typically chaired by a senior manager with engineering expertise, often serving as the Chief Engineer or another high-ranking official responsible for overseeing system integrity and compliance.

grade:

### 25

question: What discount rate should be used in the system-level cost-effectiveness model when comparing the life cycle costs of design alternatives?

reference: the handbook does not answer this question

draft: The NASA Systems Engineering Handbook passage does not specify a particular discount rate for use in the system-level cost-effectiveness model.

grade:

