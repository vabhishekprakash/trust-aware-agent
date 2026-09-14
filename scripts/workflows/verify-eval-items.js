export const meta = {
  name: 'verify-eval-items',
  description: 'Adversarially verify drafted evaluation items against the handbook text, five items per verifier',
  phases: [{ title: 'Verify', detail: 'one verifier per batch of five items, bucket-specific checks' }],
}

const ROOT = args.root
const PAGES = args.pages
const DIR = args.dir
const COUNTS = args.counts
const ORDER = ['answerable', 'ambiguous', 'unanswerable', 'false_premise']

const COMMON = `You are checking candidate evaluation items for a question-answering agent that must answer ONLY from the NASA Systems Engineering Handbook (NASA/SP-2016-6105 Rev 2). The handbook's text is one file per page under ${PAGES}, named page_<pdf page>_<printed page>.txt, each starting with "printed page: <label>". Use Grep (path ${PAGES}) and Read. The item rules are in ${ROOT}/docs/annotation-guide.md, sections "The item record" and "The four buckets"; read them first. Your job is to try to break each item. Be strict: a keep means you searched and found nothing wrong. When something is wrong but fixable with a small change (a better alias, a tighter gold answer, a corrected page, a reworded question), return verdict "fix" with the corrected fields in "fixed" (only the fields that change; any new quote must be copied exactly from a page file). When the item is unsound (the handbook answers an unanswerable question, an ambiguous item has one obvious reading, a false premise is not contradicted by the text, an answerable gold is not supported by its quote, a near-duplicate of another item in your batch), return "drop". Never rely on knowledge outside the handbook. Report only what you verified by reading or searching.`

const CHECKS = {
  answerable: 'Checks: (1) the quote states the gold answer, so that a careful reader would give this answer from that passage alone; (2) the gold answer is short and the aliases cover the acronym, spelled-out form and numeral or word variants; (3) the question is answerable without outside knowledge and is not a copy of the source sentence; (4) Grep the key terms: if another passage gives a different answer to the same question, the item is ambiguous, not answerable (fix the item into an ambiguous one with two readings and two quotes, or drop it); (5) for needs_calculator items, recompute the value from the quoted numbers.',
  ambiguous: 'Checks: (1) both readings are natural readings of the question as a user would type it; (2) each quote supports its reading\'s answer on the stated page; (3) the two answers really differ; (4) if one reading is clearly what any reader would mean, the item is answerable, not ambiguous: drop or fix; (5) the clarifying question a good agent would ask is obvious from the readings.',
  unanswerable: 'Checks: (1) Grep at least three key terms of the question yourself, including synonyms and acronyms, and read the hits: if any page answers the question directly or by combining two passages, the item is answerable and must be dropped (say which page); (2) the question uses handbook vocabulary and sounds like it belongs; (3) the evidence is the closest passage, on the stated page; (4) the notes record a real search.',
  false_premise: 'Checks: (1) the quote contradicts the premise, not merely fails to mention it; (2) premise_fix states what the handbook says, in one sentence, consistent with the quote; (3) the false part is checkable against the text; (4) if the handbook is silent on the premise, the item is unanswerable, not false premise: drop; (5) the question still reads naturally.',
}

const VERDICTS = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          index: { type: 'integer' },
          verdict: { type: 'string', enum: ['keep', 'fix', 'drop'] },
          reason: { type: 'string' },
          fixed: { type: 'object', properties: {
            question: { type: 'string' }, gold_answer: { type: 'string' }, gold_aliases: { type: 'array', items: { type: 'string' } },
            premise_fix: { type: 'string' }, notes: { type: 'string' }, bucket: { type: 'string' },
            readings: { type: 'array', items: { type: 'object', properties: { reading: { type: 'string' }, answer: { type: 'string' }, page: { type: 'string' } }, required: ['reading', 'answer', 'page'] } },
            evidence: { type: 'array', items: { type: 'object', properties: { page: { type: 'string' }, quote: { type: 'string' } }, required: ['page', 'quote'] } },
          } },
        },
        required: ['index', 'verdict', 'reason'],
      },
    },
  },
  required: ['verdicts'],
}

const pad = n => String(n).padStart(2, '0')
const batches = []
for (const bucket of ORDER) {
  const n = COUNTS[bucket] || 0
  for (let i = 0; i < n; i += 5) {
    batches.push({ file: `${DIR}/batch_${pad(batches.length)}_${bucket}.jsonl`, bucket, size: Math.min(5, n - i) })
  }
}
log(`${batches.reduce((n, b) => n + b.size, 0)} items in ${batches.length} batches`)

phase('Verify')
const results = await parallel(batches.map((batch, b) => () =>
  agent(`${COMMON}\n\nBucket: ${batch.bucket}. ${CHECKS[batch.bucket]}\n\nThe ${batch.size} items to check are in the file ${batch.file}, one JSON object per line, each with an "index" field. Read that file first.\n\nAlso check that no two items in this batch ask the same thing; if two do, keep the better one and drop the other.\n\nReturn one verdict per item, using the item's "index" field.`,
    { label: `verify:${batch.bucket}:${b + 1}`, phase: 'Verify', schema: VERDICTS, effort: 'high' })))
const verdicts = []
const failed = []
results.forEach((r, b) => {
  if (!r || !r.verdicts) { failed.push(batches[b].file); return }
  r.verdicts.forEach(v => verdicts.push(v))
})
if (failed.length) log(`batches without verdicts: ${failed.length}`)
const counts = { keep: 0, fix: 0, drop: 0 }
verdicts.forEach(v => { counts[v.verdict] = (counts[v.verdict] || 0) + 1 })
log(`verdicts: keep ${counts.keep}, fix ${counts.fix}, drop ${counts.drop}`)
return { verdicts, failed, counts }