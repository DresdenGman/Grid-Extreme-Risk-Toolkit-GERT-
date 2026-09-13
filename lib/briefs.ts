export const WINTER_BRIEF = {
  id: 'winter-load',
  version: 'winter-load-brief-v1',
  title: "A falling load curve isn't a safety signal.",
  url: 'https://gert-d.vercel.app/briefs/winter-load',
  archiveUrl: 'https://www.ercot.com/files/docs/2021/11/12/Native_Load_2021.zip',
  contextUrl: 'https://www.ercot.com/news/release?id=9c552983-008a-3906-8066-8b76315ed3e7',
  termsUrl: 'https://www.ercot.com/help/terms',
  labPath: '/history?case=winter-2021&capacity=60000&reduction=0',
  blurb: 'Why can electricity use fall during a blackout? GERT offers a short, source-linked exercise using 72 hourly observations from the February 2021 Texas winter storm. Explore the recorded load, distinguish what the curve shows from what it cannot establish, and try a capacity assumption in the Historical Lab. Includes a downloadable chart, original-source links, and a self-check. Free to try, with no account required. This is a historical educational exercise, not a live forecast or an estimate of prevented outages.\n\nhttps://gert-d.vercel.app/briefs/winter-load',
};

export const BRIEF_QUESTIONS = [
  {
    id: 'interpretation',
    prompt: 'The recorded load falls. What can this curve alone establish?',
    options: ['The grid became safer.', 'Electricity demand disappeared.', 'Recorded load fell; unmet demand and reliability remain unresolved.'],
    correctIndex: 2,
    explanation: 'A fall in the observed series is not a measurement of the electricity people would have used without interruptions. Reliability needs additional evidence.',
  },
  {
    id: 'gap',
    prompt: 'In a separate hypothetical one-hour example, load is 65,000 MW and assumed capacity is 60,000 MW. What is the arithmetic gap energy?',
    options: ['5,000 MWh, under those assumptions.', '5,000 MW of proven outage savings.', '65,000 MWh of expected unserved energy.'],
    correctIndex: 0,
    explanation: 'max(0, 65,000 − 60,000) MW × 1 hour = 5,000 MWh. It is a hypothetical calculation, not a measured outage or a probability-weighted reliability metric.',
  },
] as const;

export function exerciseReceipt(answers: number[], createdAt: string) {
  if (answers.length !== BRIEF_QUESTIONS.length || answers.some((value, i) => !Number.isInteger(value) || value < 0 || value >= BRIEF_QUESTIONS[i].options.length)) {
    throw new RangeError('Answer each question before exporting.');
  }
  if (!Number.isFinite(Date.parse(createdAt))) throw new RangeError('Invalid receipt timestamp.');
  return {
    schema: 'gert-self-check-v1',
    brief_version: WINTER_BRIEF.version,
    source_url: WINTER_BRIEF.url,
    generated_at: createdAt,
    responses: BRIEF_QUESTIONS.map((question, i) => ({
      question_id: question.id,
      question: question.prompt,
      initial_answer: question.options[answers[i]],
      correct: answers[i] === question.correctIndex,
    })),
    correct_answers: answers.filter((answer, i) => answer === BRIEF_QUESTIONS[i].correctIndex).length,
    total_questions: BRIEF_QUESTIONS.length,
    limitations: 'Self-reported, client-generated exercise record. Answers and timestamps are not independently verified. This is not a certificate, research assessment, or proof of a unique participant. Nothing is submitted automatically.',
  };
}
