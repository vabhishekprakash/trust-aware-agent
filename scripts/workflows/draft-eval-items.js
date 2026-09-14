export const meta = {
  name: 'draft-eval-items',
  description: 'Draft candidate evaluation items over the NASA SE handbook in four buckets with verbatim page evidence',
  phases: [{ title: 'Draft', detail: '30 drafters: 12 answerable page ranges, 6 ambiguous themes, 6 unanswerable themes, 6 false-premise page ranges' }],
}

const ROOT = args.root
const PAGES = args.pages

const COMMON = `You are drafting evaluation items for a question-answering agent that must answer ONLY from the NASA Systems Engineering Handbook (NASA/SP-2016-6105 Rev 2). The handbook's text is in one file per page under ${PAGES}. Files are named page_<pdf page>_<printed page>.txt and each starts with a header line "printed page: <label>". Use the Read tool to read pages and the Grep tool (with path ${PAGES}) to search across pages. Before drafting, Read ${ROOT}/docs/annotation-guide.md (the sections "The item record" and "The four buckets") and look at three records in ${ROOT}/data/eval/grader_examples.jsonl to see the item format inside the "item" field.

Rules that are not negotiable:
- Every evidence quote is copied exactly, character for character, from a page file: one sentence or one contiguous span of 8 to 60 words. Do not paraphrase, do not stitch two places together, do not fix typos. A quote that cannot be found in the page text with a search makes the item worthless.
- "page" is the printed page label from the file's header line (for example "18" or "iii"), as a string.
- Nothing in an item may rely on knowledge outside the handbook. If you know something from elsewhere, it does not count.
- Questions are phrased the way a user would type them and paraphrase rather than copy the sentence that holds the answer. No yes-or-no questions. No questions about figure numbers, table numbers, page layout or section numbering.
- No two of your items may ask the same thing, and spread them across the material you were given.
- notes: one or two sentences on why the item belongs in its bucket and anything that could fool a grader.
Return only the structured output.`

const ITEM = {
  type: 'object',
  properties: {
    bucket: { type: 'string', enum: ['answerable', 'ambiguous', 'unanswerable', 'false_premise'] },
    question: { type: 'string' },
    gold_answer: { type: ['string', 'null'] },
    gold_aliases: { type: 'array', items: { type: 'string' } },
    readings: { type: 'array', items: { type: 'object', properties: { reading: { type: 'string' }, answer: { type: 'string' }, page: { type: 'string' } }, required: ['reading', 'answer', 'page'] } },
    premise_fix: { type: ['string', 'null'] },
    expected: { type: 'string', enum: ['answer', 'clarify', 'abstain'] },
    evidence: { type: 'array', items: { type: 'object', properties: { page: { type: 'string' }, quote: { type: 'string' } }, required: ['page', 'quote'] } },
    notes: { type: 'string' },
    needs_calculator: { type: 'boolean' },
  },
  required: ['bucket', 'question', 'gold_answer', 'gold_aliases', 'readings', 'premise_fix', 'expected', 'evidence', 'notes', 'needs_calculator'],
}
const ITEMS = { type: 'object', properties: { items: { type: 'array', items: ITEM } }, required: ['items'] }

const RANGES = [[11, 25], [26, 40], [41, 55], [56, 70], [71, 85], [86, 100], [101, 115], [116, 130], [131, 145], [146, 160], [161, 182], [183, 262]]
const pad = n => String(n).padStart(3, '0')
const fileSpan = ([a, b]) => `pdf pages ${a} to ${b} (files page_${pad(a)}_*.txt through page_${pad(b)}_*.txt)`

const AMBIGUOUS_THEMES = [
  'reviews and milestones that recur across phases (SRR, SDR, PDR, CDR, KDPs, ORR) and "which" or "when" questions about them',
  'roles and responsibilities that appear in more than one process or level (who approves, who owns, who chairs), for programs and projects',
  'documents and plans that have program and project variants or per-phase versions (SEMP, plans, baselines, matrices)',
  'terms the handbook uses in more than one sense (baseline, requirement types, verification and validation contexts, margin, interface)',
  'activities, inputs or outputs that exist in more than one of the 17 common technical processes',
  'life-cycle phases, technology readiness levels, and numbers that depend on the level or class (program vs project, mission class, review type)',
]
const UNANSWERABLE_THEMES = [
  'costs, budgets, prices, funding amounts and cost of specific activities or reviews',
  'dates, years, durations, schedule lengths and how long specific activities take',
  'named people, specific missions or spacecraft, specific NASA centers or contractors',
  'quantities the handbook never gives: exact counts, sizes, percentages, thresholds or limits for things it only describes qualitatively',
  'comparisons with other agencies, standards or industries, and the history or authorship of the handbook and the NPRs',
  'specific tools, software products, file formats, templates and technical parameter values',
]

const tasks = []
RANGES.forEach((r, i) => tasks.push({
  label: `answerable:${i + 1}`,
  prompt: `${COMMON}\n\nYour task: draft 8 answerable items from ${fileSpan(r)}. The handbook must state the answer in one passage, or in two passages that sit together on the same or facing pages. Answering may need reading and at most one arithmetic step, never outside knowledge. Keep gold_answer to a phrase or a number. List gold_aliases for every reasonable short form: the acronym and the spelled-out term, the numeral and the word, with and without a unit. If these pages give numbers that support a sum, difference, ratio or percentage, make up to 2 items that need that one arithmetic step, set needs_calculator true, put the computed value in gold_answer, and quote the passage that holds the inputs; otherwise set needs_calculator false everywhere. expected is "answer"; readings is an empty list; premise_fix is null. Spread the 8 items over different sections of the range.`,
}))
AMBIGUOUS_THEMES.forEach((theme, i) => tasks.push({
  label: `ambiguous:${i + 1}`,
  prompt: `${COMMON}\n\nYour task: draft 8 ambiguous items, searching the whole handbook with Grep. Your theme: ${theme}. The question must have two natural readings that the handbook answers differently. Ambiguity must be real: a term used in two senses, a step that exists in more than one phase, a role that appears in more than one process, a document with two variants. For each item record both readings in "readings" as {reading, answer, page}, with the answer for each reading short, and put one exact quote per reading in "evidence" (two quotes per item, each on the page named in its reading). If one reading is clearly what any reader would mean, the item is not ambiguous: drop it and find another. gold_answer null, gold_aliases empty, premise_fix null, expected "clarify", needs_calculator false.`,
}))
UNANSWERABLE_THEMES.forEach((theme, i) => tasks.push({
  label: `unanswerable:${i + 1}`,
  prompt: `${COMMON}\n\nYour task: draft 10 unanswerable items on this theme: ${theme}. Each question must use the handbook's vocabulary and sound like it belongs, but the handbook must not contain the answer, not even by combining passages. Method: pick a topic the handbook covers, ask for a detail of the kind it never gives, then Grep the page files for every key term of your question (at least three searches per item, including synonyms and the acronym) and record in notes exactly which terms you searched and what you found. If any page answers the question, discard the item and draft another. A question that is merely hard is not unanswerable. Evidence: the closest passage, the one a reader would expect to hold the answer, quoted exactly with its printed page, so a reviewer can see the handbook was searched. gold_answer null, gold_aliases empty, readings empty, premise_fix null, expected "abstain", needs_calculator false.`,
}))
for (let i = 0; i < RANGES.length; i += 2) {
  const [a] = RANGES[i]
  const [, b] = RANGES[i + 1]
  tasks.push({
    label: `false_premise:${i / 2 + 1}`,
    prompt: `${COMMON}\n\nYour task: draft 8 false-premise items from ${fileSpan([a, b])}. Find a specific statement (a count, a phase, a role, a sequence, an owner, a definition) and write a question that asserts something the handbook contradicts and then asks about it, in the style of "Since the handbook requires two key decision points per phase, which one comes first?". The false part must be checkable against the text: put the contradicting passage in evidence as an exact quote with its printed page, and write the correction in premise_fix as one sentence stating what the handbook actually says. If the handbook is merely silent on the premise, the item is unanswerable, not false premise: discard it. Vary the kind of false premise across your 8 items (wrong number, wrong phase, wrong owner, wrong order, wrong document, wrong definition). gold_answer null, gold_aliases empty, readings empty, expected "abstain", needs_calculator false.`,
  })
}

phase('Draft')
log(`${tasks.length} drafters`)
const results = await parallel(tasks.map(t => () => agent(t.prompt, { label: t.label, phase: 'Draft', schema: ITEMS, effort: 'high' })))
const items = []
const perAgent = {}
results.forEach((r, i) => {
  const got = r && r.items ? r.items : []
  perAgent[tasks[i].label] = got.length
  got.forEach(it => items.push({ ...it, source: tasks[i].label }))
})
const failed = tasks.filter((t, i) => !results[i]).map(t => t.label)
if (failed.length) log(`drafters that returned nothing: ${failed.join(', ')}`)
log(`${items.length} items drafted`)
return { items, perAgent, failed }