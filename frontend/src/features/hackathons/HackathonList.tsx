import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface Hackathon {
  id: number
  name: string
}

// Minimalny widok - tylko id + name, bez stylowania/paginacji/obsługi błędów.
// Celowo tak proste: reszta (UI, wyszukiwanie, szczegóły) to zadanie dla studentów.
export function HackathonList() {
  const [hackathons, setHackathons] = useState<Hackathon[]>([])

  useEffect(() => {
    fetch(`${API_URL}/api/hackathons`)
      .then((res) => res.json())
      .then(setHackathons)
      .catch(() => {
        // Brak obsługi błędów w UI - celowo, patrz SPEC-002 "poza zakresem".
      })
  }, [])

  return (
    <section>
      <h2>Hackathony</h2>
      <ul>
        {hackathons.map((h) => (
          <li key={h.id}>
            #{h.id} — {h.name}
          </li>
        ))}
      </ul>
    </section>
  )
}
