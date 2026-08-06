import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface Hackathon {
  public_id: string
  name: string
}

// Minimalny widok bez stylowania, paginacji i logowania po stronie frontendu.
export function HackathonList() {
  const [hackathons, setHackathons] = useState<Hackathon[]>([])

  useEffect(() => {
    fetch(`${API_URL}/api/hackathons`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`API returned ${res.status}`)
        }

        return res.json()
      })
      .then(setHackathons)
      .catch(() => {
        setHackathons([])
      })
  }, [])

  return (
    <section>
      <h2>Hackathony</h2>
      <ul>
        {hackathons.map((h) => (
          <li key={h.public_id}>
            {h.name}
          </li>
        ))}
      </ul>
    </section>
  )
}
