import { useCallback, useEffect, useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import {
  assignParticipantResources,
  getHackathonResources,
  getParticipantResourceAssignments,
  revokeParticipantResource,
} from '../../resources/api/resourceManagementApi'
import type {
  ParticipantResourceAssignment,
  ResourceInventory,
} from '../../resources/types'
import { getResourceErrorMessage } from '../../resources/utils/resourceMessages'
import { ResourcePoolCreator } from '../../resources/components/ResourcePoolCreator'
import { getAttendanceParticipants } from '../api/attendanceApi'
import type { AttendanceParticipant } from '../types'
import { getAttendanceErrorMessage } from '../utils/attendanceMessages'
import { AttendanceTeamGroup } from './AttendanceTeamGroup'

interface AttendanceCheckInListProps {
  hackathonPublicId: string
}

export function AttendanceCheckInList({
  hackathonPublicId,
}: AttendanceCheckInListProps) {
  const [participants, setParticipants] = useState<
    AttendanceParticipant[] | null
  >(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resources, setResources] = useState<ResourceInventory[] | null>(null)
  const [selectedResourcePublicId, setSelectedResourcePublicId] = useState('')
  const [assignments, setAssignments] = useState<
    ParticipantResourceAssignment[]
  >([])
  const [resourceError, setResourceError] = useState<string | null>(null)
  const [resourceMessage, setResourceMessage] = useState<string | null>(null)
  const [isInventoryLoading, setIsInventoryLoading] = useState(true)
  const [isAssignmentsLoading, setIsAssignmentsLoading] = useState(false)
  const [pendingRegistrationIds, setPendingRegistrationIds] = useState(
    new Set<string>(),
  )
  const [isBulkPending, setIsBulkPending] = useState(false)

  const loadCheckIns = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true)
    setError(null)

    try {
      setParticipants(await getAttendanceParticipants(hackathonPublicId, signal))
    } catch (requestError) {
      if (requestError instanceof Error && requestError.name === 'AbortError') {
        return
      }
      setError(
        getAttendanceErrorMessage(
          requestError,
          'Nie udało się pobrać listy uczestników.',
        ),
      )
    } finally {
      if (!signal?.aborted) setIsLoading(false)
    }
  }, [hackathonPublicId])

  useEffect(() => {
    const controller = new AbortController()
    void loadCheckIns(controller.signal)

    return () => controller.abort()
  }, [loadCheckIns])

  const loadResources = useCallback(async (signal?: AbortSignal) => {
    setIsInventoryLoading(true)
    setResourceError(null)
    try {
      const result = await getHackathonResources(hackathonPublicId, signal)
      const individualResources = result.filter(
        (resource) => resource.target === 'individual',
      )
      setResources(individualResources)
      setSelectedResourcePublicId((current) =>
        individualResources.some((resource) => resource.public_id === current)
          ? current
          : (individualResources[0]?.public_id ?? ''),
      )
    } catch (requestError) {
      if (requestError instanceof Error && requestError.name === 'AbortError') {
        return
      }
      setResourceError(
        getResourceErrorMessage(
          requestError,
          'Nie udało się pobrać dostępnych zasobów.',
        ),
      )
    } finally {
      if (!signal?.aborted) setIsInventoryLoading(false)
    }
  }, [hackathonPublicId])

  const loadAssignments = useCallback(
    async (resourcePublicId: string, signal?: AbortSignal) => {
      setIsAssignmentsLoading(true)
      setResourceError(null)
      setAssignments([])
      try {
        setAssignments(
          await getParticipantResourceAssignments(
            hackathonPublicId,
            resourcePublicId,
            signal,
          ),
        )
      } catch (requestError) {
        if (
          requestError instanceof Error &&
          requestError.name === 'AbortError'
        ) {
          return
        }
        setResourceError(
          getResourceErrorMessage(
            requestError,
            'Nie udało się pobrać przydziałów zasobów.',
          ),
        )
      } finally {
        if (!signal?.aborted) setIsAssignmentsLoading(false)
      }
    },
    [hackathonPublicId],
  )

  useEffect(() => {
    const controller = new AbortController()
    void loadResources(controller.signal)
    return () => controller.abort()
  }, [loadResources])

  useEffect(() => {
    if (!selectedResourcePublicId) {
      setAssignments([])
      return
    }
    const controller = new AbortController()
    void loadAssignments(selectedResourcePublicId, controller.signal)
    return () => controller.abort()
  }, [loadAssignments, selectedResourcePublicId])

  const refreshResourceState = useCallback(async () => {
    if (!selectedResourcePublicId) return
    const [resourceResult, assignmentResult] = await Promise.all([
      getHackathonResources(hackathonPublicId),
      getParticipantResourceAssignments(
        hackathonPublicId,
        selectedResourcePublicId,
      ),
    ])
    setResources(
      resourceResult.filter((resource) => resource.target === 'individual'),
    )
    setAssignments(assignmentResult)
  }, [hackathonPublicId, selectedResourcePublicId])

  const assignResources = async (registrationPublicIds: string[]) => {
    if (!selectedResourcePublicId || registrationPublicIds.length === 0) return
    setResourceError(null)
    setResourceMessage(null)
    try {
      await assignParticipantResources(
        hackathonPublicId,
        selectedResourcePublicId,
        registrationPublicIds,
      )
      await refreshResourceState()
      setResourceMessage(
        registrationPublicIds.length === 1
          ? 'Zasób został przydzielony uczestnikowi.'
          : 'Zasoby zostały przydzielone obecnym uczestnikom.',
      )
    } catch (requestError) {
      setResourceError(
        getResourceErrorMessage(
          requestError,
          'Nie udało się przydzielić zasobów.',
        ),
      )
    }
  }

  const handleAssign = async (registrationPublicId: string) => {
    setPendingRegistrationIds((current) =>
      new Set(current).add(registrationPublicId),
    )
    try {
      await assignResources([registrationPublicId])
    } finally {
      setPendingRegistrationIds((current) => {
        const next = new Set(current)
        next.delete(registrationPublicId)
        return next
      })
    }
  }

  const handleRevoke = async (registrationPublicId: string) => {
    if (!selectedResourcePublicId) return
    setPendingRegistrationIds((current) =>
      new Set(current).add(registrationPublicId),
    )
    setResourceError(null)
    setResourceMessage(null)
    try {
      await revokeParticipantResource(
        hackathonPublicId,
        selectedResourcePublicId,
        registrationPublicId,
      )
      await refreshResourceState()
      setResourceMessage('Dostęp uczestnika do zasobu został cofnięty.')
    } catch (requestError) {
      setResourceError(
        getResourceErrorMessage(
          requestError,
          'Nie udało się cofnąć zasobu.',
        ),
      )
    } finally {
      setPendingRegistrationIds((current) => {
        const next = new Set(current)
        next.delete(registrationPublicId)
        return next
      })
    }
  }

  const participantGroups = new Map<
    string,
    { publicId: string; name: string; participants: AttendanceParticipant[] }
  >()
  for (const participant of participants ?? []) {
    const publicId = participant.team?.public_id ?? 'without-team'
    const group = participantGroups.get(publicId) ?? {
      publicId,
      name: participant.team?.name ?? 'Bez drużyny',
      participants: [],
    }
    group.participants.push(participant)
    participantGroups.set(publicId, group)
  }
  const teamGroups = [...participantGroups.values()].sort((first, second) =>
    first.name.localeCompare(second.name, 'pl'),
  )
  const selectedResource = resources?.find(
    (resource) => resource.public_id === selectedResourcePublicId,
  )
  const isResourceLoading = isInventoryLoading || isAssignmentsLoading
  const assignedRegistrationIds = new Set(
    assignments.map((assignment) => assignment.registration_public_id),
  )
  const presentWithoutResourceIds = (participants ?? [])
    .filter(
      (participant) =>
        participant.is_present &&
        !assignedRegistrationIds.has(participant.registration_public_id),
    )
    .map((participant) => participant.registration_public_id)

  const handleAssignPresent = async () => {
    setIsBulkPending(true)
    try {
      await assignResources(presentWithoutResourceIds)
    } finally {
      setIsBulkPending(false)
    }
  }

  const handleResourceCreated = async (resourcePublicId: string) => {
    await loadResources()
    setSelectedResourcePublicId(resourcePublicId)
    setResourceMessage('Pula zasobów została utworzona.')
  }

  return (
    <section
      className="attendance-participants"
      aria-label="Lista uczestników"
    >
      <ResourcePoolCreator
        hackathonPublicId={hackathonPublicId}
        onCreated={handleResourceCreated}
      />
      <div className="attendance-resource-picker">
        <label htmlFor="attendance-resource">Zasób</label>
        <select
          id="attendance-resource"
          value={selectedResourcePublicId}
          disabled={isResourceLoading || resources?.length === 0}
          onChange={(event) => {
            setResourceMessage(null)
            setSelectedResourcePublicId(event.target.value)
          }}
        >
          {resources?.length === 0 && (
            <option value="">Brak zasobów indywidualnych</option>
          )}
          {resources?.map((resource) => (
            <option key={resource.public_id} value={resource.public_id}>
              {resource.name} ({resource.available_item_count} wolnych)
            </option>
          ))}
        </select>
      </div>
      <div className="attendance-participants-actions">
        <Button
          type="button"
          variant="ghost"
          disabled={
            isResourceLoading ||
            isBulkPending ||
            !selectedResource ||
            presentWithoutResourceIds.length === 0
          }
          onClick={() => void handleAssignPresent()}
          title="Przydziela zasoby wyłącznie uczestnikom z potwierdzoną obecnością"
        >
          {isBulkPending ? 'Wysyłanie…' : 'Wyślij obecnym'}
        </Button>
        <Button
          type="button"
          variant="ghost"
          disabled={isLoading}
          onClick={() => void loadCheckIns()}
        >
          {isLoading ? 'Odświeżanie…' : 'Odśwież listę'}
        </Button>
      </div>

      {selectedResource && (
        <p className="attendance-resource-notice">
          Dostępne: {selectedResource.available_item_count} z{' '}
          {selectedResource.item_count}
        </p>
      )}
      {resourceError && <Alert variant="error">{resourceError}</Alert>}
      {resourceMessage && <Alert>{resourceMessage}</Alert>}

      <div aria-live="polite">
        {isLoading && participants === null && <p>Ładowanie uczestników…</p>}
        {error && <Alert variant="error">{error}</Alert>}
        {!isLoading && !error && participants?.length === 0 && (
          <p>Brak zaakceptowanych uczestników.</p>
        )}
        {participants && participants.length > 0 && (
          <div className="attendance-team-list">
            {teamGroups.map((team) => (
              <AttendanceTeamGroup
                key={team.publicId}
                name={team.name}
                participants={team.participants}
                selectedResourceName={
                  isResourceLoading ? null : (selectedResource?.name ?? null)
                }
                assignedRegistrationIds={assignedRegistrationIds}
                pendingRegistrationIds={pendingRegistrationIds}
                hasAvailableItems={
                  (selectedResource?.available_item_count ?? 0) > 0
                }
                onAssign={(registrationPublicId) =>
                  void handleAssign(registrationPublicId)
                }
                onRevoke={(registrationPublicId) =>
                  void handleRevoke(registrationPublicId)
                }
              />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
