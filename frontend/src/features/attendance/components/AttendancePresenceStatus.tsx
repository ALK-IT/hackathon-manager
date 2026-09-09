interface AttendancePresenceStatusProps {
  isPresent: boolean
}

export function AttendancePresenceStatus({
  isPresent,
}: AttendancePresenceStatusProps) {
  return (
    <span
      className={`attendance-presence ${isPresent ? 'is-present' : 'is-absent'}`}
    >
      {isPresent ? (
        <svg
          className="attendance-presence-icon"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <circle cx="10" cy="10" r="9" />
          <path d="m6 10 2.5 2.5L14 7" />
        </svg>
      ) : (
        <span className="attendance-presence-dot" aria-hidden="true" />
      )}
      {isPresent ? 'Obecny' : 'Nieobecny'}
    </span>
  )
}
