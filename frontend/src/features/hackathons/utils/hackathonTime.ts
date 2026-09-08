export function isHackathonInProgress(
  startDate: string,
  endDate: string,
  now = Date.now(),
): boolean {
  const start = Date.parse(startDate)
  const end = Date.parse(endDate)

  return Number.isFinite(start) && Number.isFinite(end) && start <= now && now < end
}
