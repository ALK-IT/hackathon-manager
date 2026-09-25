import type { SubmissionWithTask } from './api/evaluationsApi'

export const submission: SubmissionWithTask = {
  public_id: 'submission-1',
  task: { public_id: 'task-1', title: 'Zadanie API', criteria: [
    { name: 'Jakość', description: 'Jakość rozwiązania', max_points: 100 },
    { name: 'Pomysł', description: 'Oryginalność', max_points: 100 },
  ] },
  team: { public_id: 'team-1', name: 'Drużyna Alfa' },
  github_url: 'https://github.com/example/solution',
  submitted_by: null,
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-01-01T10:00:00Z',
  evaluation: null,
}

export const evaluation = {
  score: 0,
  criterion_scores: [{ criterion_index: 0, points: 0 }, { criterion_index: 1, points: 0 }],
  feedback: 'Do poprawy', evaluated_by: null, evaluated_at: '2026-01-02T10:00:00Z',
}
