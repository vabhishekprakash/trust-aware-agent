# Final blind grader check: real agent outputs from dev

20 outputs of the agent on development questions (answerable 10, ambiguous 1, unanswerable 5, false_premise 4), in a shuffled order. Grade each CORRECT, PARTIAL or WRONG by the rules in docs/annotation-guide.md and write it after 'grade:'. A clarifying question that names both readings of an ambiguous item is CORRECT; a bare abstention on a false premise is PARTIAL. Do not open data/eval/final_blind_key.jsonl until the sheet is done. scripts/compare_grader_check.py reports the agreement; that number is the grader's signed-off figure in the report.

### 1

question: How many months does the handbook expect Phase B, preliminary design and technology completion, to last for a Type A mission?

reference: the handbook does not answer this question

output: The NASA Systems Engineering Handbook does not specify the duration of Phase B (Preliminary Design and Technology Completion) in terms of months for any type of mission. Therefore, the answer is: The handbook does not say.

grade:CORRECT

### 2

question: Which group usually sets up the communication links between the parties responsible for systems that interface with each other?

reference: reference answer: Interface Working Group (IWG)
reference: acceptable forms: IWG; Interface Working Group; an Interface Working Group; the IWG

output: The handbook does not say.

grade:WRONG

### 3

question: Which NASA procedural requirements document defines the life cycle for information technology projects?

reference: reference answer: NPR 7120.7
reference: acceptable forms: 7120.7; NPR 7120.7, NASA Information Technology and Institutional Infrastructure Program and Project Management Requirements; NASA Information Technology and Institutional Infrastructure Program and Project Management Requirements

output: The handbook does not say.

grade:WRONG

### 4

question: How much schedule slack, as a share of the total duration, should be built into the need dates for enabling products?

reference: the handbook does not answer this question

output: The handbook does not say.

grade:CORRECT

### 5

question: When in the life cycle is the Technology Maturity Assessment carried out?

reference: reading 1: the initial TMA that sets the baseline maturity -> at program/project outset (page 207)
reference: reading 2: the final TMA that feeds the Technology Readiness Assessment Report -> just prior to the PDR (page 207)

output: The Technology Maturity Assessment (TMA) is performed at two key points in the life cycle: initially, as a baseline maturity of the system's required technologies at program/project outset; and secondly, just prior to the Preliminary Design Review (PDR).

grade:CORRECT

### 6

question: The end-product verification plan is written inside the Product Verification Process itself, so during which of that process's five major activities is it produced?

reference: the question's assumption is false; the handbook says: The verification plan is generated through the Technical Planning Process and baselined before product verification starts; it enters the Product Verification Process as an input rather than being produced by one of its activities.

output: The product verification plan is generated as part of the "prepare to conduct product verification" activity within the five major activities in the Product Verification Process.

grade:WRONG

### 7

question: In the handbook's example table of tailoring NPR 7120.5 project products, which product is fully compliant for Type A projects but not applicable for every other project type?

reference: reference answer: Human Rating Certification Package
reference: acceptable forms: the Human Rating Certification Package; human rating certification package; Human Rating Certification

output: Type A projects are fully compliant for Design Documentation, while it is not applicable for all other types (B, C, D, E, F). Therefore, the answer is: Design Documentation.

grade:WRONG

### 8

question: Above what contract value does a project have to run Earned Value Management?

reference: the handbook does not answer this question

output: The handbook does not say.

grade:CORRECT

### 9

question: What kind of board do large projects typically set up during production to decide whether nonconforming components get accepted, reworked, or scrapped?

reference: reference answer: Material Review Board
reference: acceptable forms: MRB; MRBs; Material Review Boards; a Material Review Board (MRB)

output: Large projects typically use Material Review Boards (MRBs) to review any nonconformance to specifications and determine the disposition of the components.

grade:CORRECT

### 10

question: The handbook's definition of life cycle cost leaves out the launch vehicle; where does it say the launch cost should be accounted for instead?

reference: the question's assumption is false; the handbook says: The handbook's glossary states that the LCC includes the cost of the launch vehicle; what it excludes is Pre-Phase A and extended operations.

output: The handbook says that the LCC (Life Cycle Cost) includes the cost of the launch vehicle. It does not specify an alternative location for accounting for this cost, only stating its inclusion in the LCC definition. Therefore, the answer is: The handbook does not say.

grade:CORRECT

### 11

question: What does the handbook call the events where the decision authority decides whether a program or project is ready to move into the next life-cycle phase?

reference: reference answer: Key Decision Points
reference: acceptable forms: KDPs; KDP; Key Decision Point; key decision points (KDPs)

output: Do you mean The readiness of a project's flight system to execute critical events during flight operation, or An event at which the decision authority determines the readiness of a program/project to progress to the next phase of the life cycle (or to the next KDP)?

grade:WRONG

### 12

question: Which NASA document sets the meanings that terms used in a SEMP are supposed to follow?

reference: reference answer: NPR 7123.1
reference: acceptable forms: NPR 7123.1, Systems Engineering Processes and Requirements; NASA Systems Engineering Processes and Requirements; NPR7123.1; NPR 7123

output: J.2 Terms Used states that terms used in the SEMP should have the same meaning as the terms used in NPR 7123.1, Systems Engineering Processes and Requirements. Therefore, the answer is: NPR 7123.1.

grade:CORRECT

### 13

question: Among verification, qualification, acceptance and certification, which activity is repeated on every flight unit that is manufactured rather than performed once for the design?

reference: reference answer: acceptance
reference: acceptable forms: acceptance testing; the acceptance program; acceptance test; acceptance activities

output: Acceptance is repeated on each of the flight units as they are manufactured and readied for flight/use.

grade:CORRECT

### 14

question: Using the cost guidance in the handbook's example program/project types table, by how many dollars does the top of the Type C life-cycle cost range exceed the top of the Type D range?

reference: reference answer: $400M
reference: acceptable forms: 400M; $400 million; 400 million; 400 million dollars; about $400M; ~$400M

output: The top of the Type C life-cycle cost range exceeds the top of the Type D range by $100 according to the given information, but the exact figure is not provided directly in the passages.

grade:WRONG

### 15

question: How many months before the planned end of mission should the Decommissioning Review be scheduled?

reference: the handbook does not answer this question

output: The handbook does not say.

grade:CORRECT

### 16

question: What does the handbook say measures of effectiveness can be treated as synonymous with?

reference: reference answer: mission/project success criteria
reference: acceptable forms: mission success criteria; project success criteria; success criteria; mission or project success criteria; the mission/project success criteria

output: The handbook says that Measures of Effectiveness (MOEs) are treated as synonymous with mission/project success criteria.

grade:CORRECT

### 17

question: What discount rate should be used in the system-level cost-effectiveness model when comparing the life cycle costs of design alternatives?

reference: the handbook does not answer this question

output: The handbook does not say.

grade:CORRECT

### 18

question: The handbook's life-cycle cost curve shows roughly 75% of a project's cost already spent by the time design is done; what share of the total does it say those design decisions commit?

reference: the question's assumption is false; the handbook says: During design only about 15% of the costs are expended; it is the design that commits about 75% of the life cycle costs.

output: The handbook states that roughly 75% of a project's cost is committed by the time design is done. Therefore, it commits 75% of the total life cycle costs at this stage.

grade:PARTIAL

### 19

question: Which NASA requirements document must software development follow when the technical team makes or codes a product?

reference: reference answer: NPR 7150.2
reference: acceptable forms: NPR 7150.2, NASA Software Engineering Requirements; NASA Software Engineering Requirements; NASA Procedural Requirements 7150.2; 7150.2

output: The technical team should ensure that software development follows NPR 7150.2 when making or coding a product.

grade:CORRECT

### 20

question: Because the handbook treats an authorized waiver as a minor engineering change to the baseline, whose approval does it need when the waiver touches an external interface?

reference: the question's assumption is false; the handbook says: A waiver is a documented agreement releasing a program or project from meeting a requirement, and authorized waivers do not constitute a change to a baseline.

output: Because the handbook treats an authorized waiver as a minor engineering change to the baseline that may affect an external interface, it needs approval from all stakeholders affected. CALC: 1 + 2

grade:WRONG

