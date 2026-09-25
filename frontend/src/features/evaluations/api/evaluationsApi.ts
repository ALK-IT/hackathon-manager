import { apiRequest } from '../../../lib/api/client'
import type { TaskSubmission, TaskSubmissionEvaluation } from '../../registration/types'

export interface SubmissionWithTask extends TaskSubmission {
  task: { public_id: string; title: string }
}

export interface SubmissionPage {
  items: SubmissionWithTask[]
  total: number
  limit: number
  offset: number
}

export interface SubmissionFilters {
  teamPublicId?: string
  taskPublicId?: string
  evaluated?: boolean
  limit: number
  offset: number
  signal?: AbortSignal
}

export interface LeaderboardEntry {
  rank: number
  team_public_id: string
  team_name: string
  total_score: number
  evaluated_tasks: number
}

export function getSubmissions(id: string, options: SubmissionFilters) {
  const query = new URLSearchParams({ limit: String(options.limit), offset: String(options.offset) })
  if (options.teamPublicId) query.set('team_public_id', options.teamPublicId)
  if (options.taskPublicId) query.set('task_public_id', options.taskPublicId)
  if (options.evaluated !== undefined) query.set('evaluated', String(options.evaluated))
  return apiRequest<SubmissionPage>(
    `/api/hackathons/${encodeURIComponent(id)}/task-submissions?${query}`,
    { signal: options.signal },
  )
}

export function getLeaderboard(id: string, limit: number, signal?: AbortSignal) {
  return apiRequest<{ items: LeaderboardEntry[] }>(
    `/api/hackathons/${encodeURIComponent(id)}/leaderboard?limit=${limit}`,
    { signal },
  )
}

export function setLeaderboardVisibility(id: string, visible: boolean) {
  return apiRequest<{ visible: boolean }>(
    `/api/hackathons/${encodeURIComponent(id)}/leaderboard-visibility`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visible }),
    },
  )
}

export function saveEvaluation(
  hackathonId: string,
  taskId: string,
  submissionId: string,
  payload: { score: number; feedback: string | null },
) {
  return apiRequest<TaskSubmissionEvaluation>(
    `/api/hackathons/${encodeURIComponent(hackathonId)}/tasks/${encodeURIComponent(taskId)}/submissions/${encodeURIComponent(submissionId)}/evaluation`,
    { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) },
  )
}
