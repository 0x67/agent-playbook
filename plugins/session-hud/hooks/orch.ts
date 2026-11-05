import type { OrchAgent, OrchStatus } from '../types'

export type Verdict = { label: string; tone: 'success' | 'warning' | 'error' }

const VERDICTS: Record<string, Verdict> = {
  APPROVED: { label: 'APPROVED', tone: 'success' },
  VERIFIED: { label: 'VERIFIED', tone: 'success' },
  PASS: { label: 'PASS', tone: 'success' },
  PASSED: { label: 'PASS', tone: 'success' },
  // spec-driven task statuses, which implement agents report
  DONE: { label: 'DONE', tone: 'success' },
  BLOCKED: { label: 'BLOCKED', tone: 'error' },
  'VERIFIED WITH CAVEATS': { label: 'CAVEATS', tone: 'warning' },
  NEEDS_REVISION: { label: 'REVISE', tone: 'warning' },
  FAILED: { label: 'FAILED', tone: 'error' },
  FAIL: { label: 'FAILED', tone: 'error' },
  REFUTED: { label: 'REFUTED', tone: 'error' },
}

// a verdict line stands alone, optionally after a "Verdict:" style label and
// markdown emphasis, so "tests FAILED before the fix" in prose is not one
const VERDICT_LINE =
  /^[\s#>*_`-]*(?:(?:verdict|status|result|outcome)[\s*_`]*[:=-][\s*_`]*)?(VERIFIED WITH CAVEATS|NEEDS_REVISION|APPROVED|VERIFIED|REFUTED|FAILED|FAIL|PASSED|PASS|DONE|BLOCKED)[*_`]*\s*(?:$|[.:(-])/i
const VERDICT_JSON = /"(?:verdict|status|result|outcome)"\s*:\s*"([A-Za-z_ ]+)"/i

export function parseVerdict(answer: string): Verdict | undefined {
  const json = VERDICT_JSON.exec(answer)
  if (json?.[1]) {
    const hit = VERDICTS[json[1].trim().toUpperCase().replace(/ +/g, ' ')]
    if (hit) return hit
  }
  for (const line of answer.split('\n')) {
    const match = VERDICT_LINE.exec(line)
    if (match?.[1]) return VERDICTS[match[1].toUpperCase()]
  }
  return undefined
}

// claude-opus-5-5 -> opus 5.5; aliases and other ids pass through
export function shortModel(model: string): string {
  const match = /^claude-([a-z]+)-(\d+)(?:-(\d{1,2}))?(?:-\d{8})?(?:\[.*\])?$/.exec(model)
  if (!match) return model
  return match[3] ? `${match[1]} ${match[2]}.${match[3]}` : `${match[1]} ${match[2]}`
}

// ai-setup:implement-subagent -> implement
export function shortType(type: string): string {
  const bare = type.includes(':') ? type.slice(type.indexOf(':') + 1) : type
  return bare.replace(/-subagent$/, '').replace(/^general-purpose$/, 'general')
}

export function workflowTitle(input: {
  script?: string
  name?: string
  scriptPath?: string
  title?: string
}): string | undefined {
  const fromMeta = input.script
    ? /meta\s*=\s*\{[^}]*?\bname\s*:\s*['"`]([^'"`]+)['"`]/.exec(input.script)?.[1]
    : undefined
  const fromPath = input.scriptPath?.split(/[\\/]/).pop()?.replace(/\.[a-z]+$/, '')
  return input.title ?? fromMeta ?? input.name ?? fromPath
}

export function elapsed(ms: number): string {
  const seconds = Math.max(0, Math.round(ms / 1000))
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const rest = seconds % 60
  if (hours > 0) return `${hours}h${String(minutes).padStart(2, '0')}m`
  if (minutes > 0) return `${minutes}m${String(rest).padStart(2, '0')}s`
  return `${rest}s`
}

export function tokens(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`
  if (count >= 1_000) return `${(count / 1_000).toFixed(count >= 100_000 ? 0 : 1)}k`
  return String(count)
}

export const STATUS_MARK: Record<OrchStatus, { mark: string; tone: string }> = {
  running: { mark: '◐', tone: 'warning' },
  done: { mark: '✓', tone: 'success' },
  failed: { mark: '✗', tone: 'error' },
  aborted: { mark: '■', tone: 'error' },
}

export type OrchGroup = {
  key: string
  title: string
  agents: OrchAgent[]
  startedAt: number
  endedAt?: number
  done: number
  tokens: number
}

// newest group first, agents in spawn order inside each
export function groupAgents(
  agents: readonly OrchAgent[],
  titles: Readonly<Record<string, string>>,
): OrchGroup[] {
  const groups = new Map<string, OrchGroup>()
  for (const agent of agents) {
    const group = groups.get(agent.group) ?? {
      key: agent.group,
      title: titles[agent.group] ?? agent.group,
      agents: [],
      startedAt: agent.startedAt,
      done: 0,
      tokens: 0,
    }
    group.agents.push(agent)
    group.startedAt = Math.min(group.startedAt, agent.startedAt)
    group.tokens += agent.tokens
    if (agent.status !== 'running') group.done += 1
    groups.set(agent.group, group)
  }
  for (const group of groups.values()) {
    const isFinished = group.agents.every(one => one.status !== 'running')
    if (isFinished) {
      group.endedAt = Math.max(...group.agents.map(one => one.endedAt ?? one.startedAt))
    }
  }
  return [...groups.values()].sort((a, b) => b.startedAt - a.startedAt)
}

export function verdictTone(label: string): Verdict['tone'] {
  return Object.values(VERDICTS).find(one => one.label === label)?.tone ?? 'warning'
}
