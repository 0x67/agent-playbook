import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Limit, Orch, OrchAgent, OrchStatus, Todo, Usage } from '../types'
import {
  STATUS_MARK,
  elapsed,
  groupAgents,
  parseVerdict,
  shortModel,
  shortType,
  tokens,
  verdictTone,
  workflowTitle,
} from './orch'

const PANE = 'todo'
const TITLE = 'Shared TODO'
const PANE_COLUMNS = 34
// one file every session reads, so a change in one shows in the others
const FILE_NAME = '.claude-todo.md'
const POLL_MS = 2000
const USAGE_EVERY_TICKS = 15
const ORCH_PANE = 'orch'
const ORCH_TITLE = 'Agents'
const ORCH_COLUMNS = 70
// older finished agents drop off past this many
const ORCH_KEEP = 150
// one JSONL file per session and day, so sessions never write the same file
const LOG_DIR = '.claude-orch-log'

const todos = atom({ plugin: 'session-hud', key: 'todos' } as const, [], {
  shape: 'todos-1',
})
const usage = atom({ plugin: 'session-hud', key: 'usage' } as const, null, {
  shape: 'usage-1',
})
const EMPTY_ORCH: Orch = { agents: [], titles: {} }
const orch = atom({ plugin: 'session-hud', key: 'orch' } as const, EMPTY_ORCH, {
  shape: 'orch-1',
})
// ticks while an agent runs, so the pane's elapsed times move
const orchNow = atom({ plugin: 'session-hud', key: 'orchNow' } as const, 0)

const ITEM = /^(\s*[-*]\s+\[)( |x|X)(\]\s+)(.*)$/

const LIMIT_LABELS: Record<string, string> = {
  five_hour: '5h limit',
  seven_day: 'Weekly',
  spend_limit: 'Spend',
}

function parse(text: string): Todo[] {
  const found: Todo[] = []
  text.split('\n').forEach((raw, line) => {
    const match = ITEM.exec(raw)
    if (match) {
      found.push({ line, text: match[4] ?? '', isDone: match[2] !== ' ' })
    }
  })
  return found
}

function duration(ms: number): string {
  const minutes = Math.max(0, Math.round(ms / 60000))
  const days = Math.floor(minutes / 1440)
  const hours = Math.floor((minutes % 1440) / 60)
  const rest = minutes % 60
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h ${rest}m`
  return `${rest}m`
}

function levelColor(percent: number) {
  if (percent >= 85) return 'error'
  if (percent >= 60) return 'warning'
  return 'success'
}

// a window with a little use reads "<1%", so a rounded 0 is not mistaken for no data
function percentText(percent: number): string {
  return percent > 0 && percent < 0.5 ? '<1%' : `${Math.round(percent)}%`
}

function meter(percent: number, cells: number): [string, string] {
  const filled = Math.min(cells, Math.max(0, Math.round((percent / 100) * cells)))
  return ['█'.repeat(filled), '░'.repeat(cells - filled)]
}

function keep(agents: OrchAgent[]): OrchAgent[] {
  let extra = agents.length - ORCH_KEEP
  if (extra <= 0) return agents
  return agents.filter(one => {
    if (extra > 0 && one.status !== 'running') {
      extra -= 1
      return false
    }
    return true
  })
}

function endStatus(reason: string): OrchStatus {
  if (reason === 'answer') return 'done'
  if (reason === 'aborted') return 'aborted'
  return 'failed'
}

// module state; a reload starts it over, which only re-reads the files
let home = ''
let lastMtime = -1
let sessionCwd = ''
let logReady: Promise<{ path: string; lines: string[] }> | null = null

async function homeDir($: EngineInterface) {
  if (home === '') {
    home = (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')) ?? '.'
  }
  return home
}

async function todoFile($: EngineInterface) {
  return `${await homeDir($)}/${FILE_NAME}`
}

async function openLog($: EngineInterface) {
  const day = new Date(await $.clock.now()).toISOString().slice(0, 10)
  const id = (await $.session.id()).slice(0, 8)
  const path = `${await homeDir($)}/${LOG_DIR}/${day}-${id}.jsonl`
  const lines = (await $.fs.exists(path))
    ? (await $.fs.read(path)).split('\n').filter(line => line !== '')
    : []
  return { path, lines }
}

async function appendLog($: EngineInterface, entry: Record<string, unknown>) {
  // one shared promise, so two agents ending together both land
  const log = await (logReady ??= openLog($))
  log.lines.push(JSON.stringify(entry))
  await $.fs.write(log.path, `${log.lines.join('\n')}\n`)
}

async function tickOrch($: EngineInterface) {
  const state = await read($, orch)
  if (!state.agents.some(one => one.status === 'running')) return
  const now = await $.clock.now()
  await update($, orchNow, () => now)
}

async function noteTool($: EngineInterface, agentId: string, tool: string) {
  const state = await read($, orch)
  const isTracked = state.agents.some(
    one => one.id === agentId && one.status === 'running',
  )
  if (!isTracked) return
  await update($, orch, current => ({
    ...current,
    agents: current.agents.map(one =>
      one.id === agentId ? { ...one, lastTool: tool } : one,
    ),
  }))
}

async function readLines($: EngineInterface): Promise<string[]> {
  const path = await todoFile($)
  if (!(await $.fs.exists(path))) return ['# TODO', '']
  return (await $.fs.read(path)).split('\n')
}

async function load($: EngineInterface, isForced = false) {
  const path = await todoFile($)
  const stat = await $.fs.stat(path).catch(() => undefined)
  const mtime = stat?.mtimeMs ?? 0
  if (!isForced && mtime === lastMtime) return
  lastMtime = mtime
  const list = stat ? parse(await $.fs.read(path)) : []
  await update($, todos, () => list)
}

async function save($: EngineInterface, lines: string[]) {
  await $.fs.write(await todoFile($), lines.join('\n'))
  await load($, true)
}

async function measure($: EngineInterface) {
  const now = await $.clock.now()
  const figures = await $.session.usage()
  const limits: Limit[] = figures.rateLimits.map(limit => {
    const resetsAt = limit.resetsAt ? Date.parse(limit.resetsAt) : NaN
    return {
      kind: limit.kind,
      percent: limit.percentUsed,
      ...(Number.isNaN(resetsAt) ? {} : { resetsAt }),
    }
  })
  // right after a reset the engine reports no five_hour window until a request lands in the new
  // one; keep the slot at 0% so the row does not change shape. Accounts with no windows at all
  // report no seven_day either and get no slot.
  if (limits.some(one => one.kind === 'seven_day') && !limits.some(one => one.kind === 'five_hour')) {
    limits.unshift({ kind: 'five_hour', percent: 0 })
  }
  const next: Usage = {
    ...(figures.context.percent === undefined
      ? {}
      : { contextPercent: figures.context.percent }),
    limits,
    ...(figures.cost ? { costUsd: figures.cost.usd } : {}),
    measuredAt: now,
  }
  await update($, usage, () => next)
}

async function toggle($: EngineInterface, item: Todo) {
  const lines = await readLines($)
  const raw = lines[item.line]
  const match = raw === undefined ? null : ITEM.exec(raw)
  // the file moved under us; reload rather than tick the wrong line
  if (!match || match[4] !== item.text) return load($, true)
  lines[item.line] = `${match[1]}${item.isDone ? ' ' : 'x'}${match[3]}${match[4]}`
  await save($, lines)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'todo',
      description:
        'Shared TODO list: /todo shows or hides it; add <text>, done <n>, rm <n>, clear',
      argumentHint: '[show | hide | add <text> | done <n> | rm <n> | clear]',
    })
    await $.command.register({
      name: 'orch',
      description:
        'Subagents and workflow agents of this session: /orch shows or hides the pane; clear, reset, log',
      argumentHint: '[show | hide | clear | reset | log]',
    })
    sessionCwd = e.cwd
    await load($, true)
    await measure($)

    let ticks = 0
    $.clock.every(POLL_MS, () => {
      ticks += 1
      void load($).then(() =>
        ticks % USAGE_EVERY_TICKS === 0 ? measure($) : undefined,
      )
      void tickOrch($)
    })

    return next(e)
  })

  on('session.measure', async ($, e, next) => {
    await measure($)
    return next(e)
  })

  on('command.run', { command: 'todo' }, async ($, e) => {
    const [verb = '', ...rest] = e.args.trim().split(/\s+/)
    const arg = rest.join(' ')
    const list = await read($, todos)
    const pick = () => list[Number(arg) - 1]

    switch (verb) {
      case '':
      case 'show':
      case 'hide': {
        const isShown = (await $.ui.panes()).some(pane => pane.id === PANE)
        const isShowing = verb === '' ? !isShown : verb === 'show'
        if (!isShowing) {
          await $.ui.close({ id: PANE })
          return { text: 'TODO pane hidden.' }
        }
        await $.ui.open({ id: PANE, title: TITLE, columns: PANE_COLUMNS })
        const open = list.filter(one => !one.isDone).length
        return { text: `TODO pane shown (${open} open).` }
      }
      case 'add': {
        if (arg === '') return { text: 'Usage: /todo add <text>' }
        const lines = await readLines($)
        while (lines.length > 0 && lines[lines.length - 1] === '') lines.pop()
        lines.push(`- [ ] ${arg}`, '')
        await save($, lines)
        return { text: `Added: ${arg}` }
      }
      case 'done': {
        const item = pick()
        if (!item) return { text: `No item ${arg}.` }
        await toggle($, item)
        return { text: `${item.isDone ? 'Reopened' : 'Done'}: ${item.text}` }
      }
      case 'rm': {
        const item = pick()
        if (!item) return { text: `No item ${arg}.` }
        const lines = await readLines($)
        lines.splice(item.line, 1)
        await save($, lines)
        return { text: `Removed: ${item.text}` }
      }
      case 'clear': {
        const done = new Set(list.filter(one => one.isDone).map(one => one.line))
        const lines = (await readLines($)).filter((_, i) => !done.has(i))
        await save($, lines)
        return { text: `Cleared ${done.size} done item(s).` }
      }
      default:
        return {
          text: 'Usage: /todo [show | hide | add <text> | done <n> | rm <n> | clear]',
        }
    }
  })

  on('command.run', { command: 'orch' }, async ($, e) => {
    const verb = e.args.trim()
    switch (verb) {
      case '':
      case 'show':
      case 'hide': {
        const isShown = (await $.ui.panes()).some(pane => pane.id === ORCH_PANE)
        const isShowing = verb === '' ? !isShown : verb === 'show'
        if (!isShowing) {
          await $.ui.close({ id: ORCH_PANE })
          return { text: 'Agents pane hidden.' }
        }
        await $.ui.open({ id: ORCH_PANE, title: ORCH_TITLE, columns: ORCH_COLUMNS })
        const state = await read($, orch)
        const running = state.agents.filter(one => one.status === 'running').length
        return { text: `Agents pane shown (${running} running).` }
      }
      case 'clear':
      case 'reset': {
        await update($, orch, state => {
          const agents =
            verb === 'reset' ? [] : state.agents.filter(one => one.status === 'running')
          const groups = new Set(agents.map(one => one.group))
          const titles = Object.fromEntries(
            Object.entries(state.titles).filter(([key]) => groups.has(key)),
          )
          return { agents, titles }
        })
        return { text: verb === 'reset' ? 'Agents list reset.' : 'Finished agents cleared.' }
      }
      case 'log':
        return { text: `Run log: ${await homeDir($)}/${LOG_DIR}/ (one JSONL file per session and day)` }
      default:
        return { text: 'Usage: /orch [show | hide | clear | reset | log]' }
    }
  })

  // a Workflow call's id is shared by every agent of its run: name the group
  on('tool.call', async ($, e, next) => {
    if (e.tool === 'Workflow') {
      const title = workflowTitle(e) ?? 'Workflow'
      await update($, orch, state => ({
        ...state,
        titles: { ...state.titles, [e.tool_use_id]: title },
      }))
    } else if (e.agentId !== undefined) {
      void noteTool($, e.agentId, String(e.tool)).catch(() => undefined)
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  on('agent.spawn', async ($, e, next) => {
    const started = await next(e)
    if (started.deny !== undefined || started.agentId === undefined) return started
    if (e.isTeammate) return started
    const id = started.agentId
    const now = await $.clock.now()
    const group = e.workflow
      ? e.tool_use_id || e.workflow.runId
      : (e.parentAgentId ?? 'main')
    const fresh: OrchAgent = {
      id,
      description: e.description,
      type: e.subagentType,
      model: started.model,
      group,
      ...(e.workflow ? { runId: e.workflow.runId } : {}),
      status: 'running',
      startedAt: now,
      tokens: 0,
    }
    await update($, orch, state => {
      const parent = state.agents.find(one => one.id === group)
      const title =
        state.titles[group] ??
        (group === 'main'
          ? 'Main thread'
          : e.workflow
            ? `Workflow ${e.workflow.runId}`
            : (parent?.description ?? 'Subagent'))
      // a resumed agent keeps its row, start time and tokens
      const previous = state.agents.find(one => one.id === id)
      const agent: OrchAgent = previous
        ? { ...previous, status: 'running' }
        : fresh
      return {
        titles: { ...state.titles, [group]: title },
        agents: keep([...state.agents.filter(one => one.id !== id), agent]),
      }
    })
    return started
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    const id = e.agentId
    if (id === undefined) return result
    const state = await read($, orch)
    const agent = state.agents.find(one => one.id === id)
    if (!agent) return result

    const now = await $.clock.now()
    const used = e.usage
    const spent = used
      ? used.input_tokens +
        used.output_tokens +
        used.cache_read_input_tokens +
        used.cache_creation_input_tokens
      : 0
    const verdict = parseVerdict(e.answer)
    const finished: OrchAgent = {
      ...agent,
      status: endStatus(e.reason),
      endedAt: now,
      tokens: agent.tokens + spent,
      ...(used ? { model: used.model } : {}),
      ...(verdict ? { verdict: verdict.label } : {}),
    }
    await update($, orch, current => ({
      ...current,
      agents: current.agents.map(one => (one.id === id ? finished : one)),
    }))
    await appendLog($, {
      ts: new Date(now).toISOString(),
      cwd: sessionCwd,
      group: state.titles[agent.group] ?? agent.group,
      runId: agent.runId,
      agentId: id,
      description: agent.description,
      type: agent.type,
      model: finished.model,
      status: finished.status,
      verdict: finished.verdict,
      durationMs: e.durationMs,
      input_tokens: used?.input_tokens ?? 0,
      output_tokens: used?.output_tokens ?? 0,
      cache_read_input_tokens: used?.cache_read_input_tokens ?? 0,
      cache_creation_input_tokens: used?.cache_creation_input_tokens ?? 0,
    }).catch(() => undefined)
    return result
  })

  // usage sits on the hint line under the prompt, a row below the engine's
  // own hints; the TODO pane stays hidden until /todo shows it
  on('ui.render', { component: 'PromptHint' }, async ($, e, next) => {
    const figures = await read($, usage)
    const engine = await next(e)
    if (figures === null) return engine

    const { Box, Text } = $.ui.resolve(e)
    const list = await read($, todos)
    const open = list.filter(one => !one.isDone).length
    const agents = await read($, orch)
    const running = agents.agents.filter(one => one.status === 'running').length
    const columns = e.viewport?.columns ?? 80
    const cells = columns >= 140 ? 8 : columns >= 110 ? 5 : 0

    // labels in the plain foreground; the theme's grey keys wash out in
    // a terminal
    const gauge = (label: string, percent: number, resetsAt?: number) => {
      const [filled, empty] = meter(percent, cells)
      const color = levelColor(percent)
      return (
        <Text>
          <Text>{label} </Text>
          {cells > 0 && <Text color={color}>{filled + empty} </Text>}
          <Text color={color} bold>
            {percentText(percent)}
          </Text>
          {resetsAt !== undefined && (
            <Text> ↻ {duration(resetsAt - figures.measuredAt)}</Text>
          )}
        </Text>
      )
    }

    const parts = [
      figures.contextPercent !== undefined &&
        gauge('Context', figures.contextPercent),
      ...figures.limits.map(limit =>
        gauge(LIMIT_LABELS[limit.kind] ?? limit.kind, limit.percent, limit.resetsAt),
      ),
      figures.costUsd !== undefined && (
        <Text>
          <Text>Cost </Text>
          <Text color="claude" bold>
            ${figures.costUsd.toFixed(2)}
          </Text>
        </Text>
      ),
      running > 0 && (
        <Text>
          <Text>Agents </Text>
          <Text color="warning" bold>
            {running} running
          </Text>
        </Text>
      ),
      open > 0 && (
        <Text>
          <Text>TODO </Text>
          <Text color="suggestion" bold>
            {open}
          </Text>
        </Text>
      ),
    ].filter(part => part !== false)

    return (
      <Box flexDirection="column">
        {engine}
        <Box flexDirection="row" flexWrap="wrap" columnGap={3}>
          {parts}
        </Box>
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const list = await read($, todos)
    const width = Math.max(10, e.props.bodyColumns - 5)
    const clip = (text: string) =>
      text.length > width ? `${text.slice(0, width - 1)}…` : text
    // file order gives each item its number, so /todo done <n> matches
    const numbered = list.map((item, i) => ({ item, n: i + 1 }))
    const open = numbered.filter(one => !one.item.isDone)
    const done = numbered.filter(one => one.item.isDone)

    const row = ({ item, n }: { item: Todo; n: number }) => (
      <Button key={`item-${item.line}`} plain onPress={() => toggle($, item)}>
        <Text>{String(n).padStart(2)} </Text>
        {item.isDone ? (
          <Text color="success">✓ </Text>
        ) : (
          <Text color="warning">○ </Text>
        )}
        {item.isDone ? (
          <Text strikethrough>{clip(item.text)}</Text>
        ) : (
          <Text bold>{clip(item.text)}</Text>
        )}
      </Button>
    )

    return (
      <Box flexDirection="column">
        <Text>
          <Text color="warning" bold>
            {open.length} open
          </Text>
          <Text> · </Text>
          <Text color="success" bold>
            {done.length} done
          </Text>
        </Text>
        {list.length === 0 && <Text>Nothing on the list.</Text>}
        {open.map(row)}
        {done.map(row)}
        <Text>
          <Text color="suggestion">/todo add</Text> · done n · rm n · clear
        </Text>
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: ORCH_PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const state = await read($, orch)
    const ticked = await read($, orchNow)
    const groups = groupAgents(state.agents, state.titles)
    if (groups.length === 0) {
      return <Text>No subagents yet this session. /orch hides this pane.</Text>
    }
    const latest = Math.max(
      ticked,
      ...state.agents.map(one => one.endedAt ?? one.startedAt),
    )
    const isWide = e.props.bodyColumns >= 84

    const row = (agent: OrchAgent) => {
      const mark = STATUS_MARK[agent.status]
      const isRunning = agent.status === 'running'
      return (
        <Box key={agent.id} flexDirection="row" columnGap={1}>
          <Text color={mark.tone}>{mark.mark}</Text>
          <Box flexGrow={1} flexShrink={1}>
            <Text wrap="truncate" bold={isRunning}>
              {agent.description}
            </Text>
          </Box>
          {isWide && (
            <Box width={11}>
              <Text wrap="truncate">{shortType(agent.type)}</Text>
            </Box>
          )}
          <Box width={9}>
            <Text wrap="truncate">{shortModel(agent.model)}</Text>
          </Box>
          <Box width={7} justifyContent="flex-end">
            <Text>{elapsed((agent.endedAt ?? latest) - agent.startedAt)}</Text>
          </Box>
          <Box width={8} justifyContent="flex-end">
            {isRunning ? (
              <Text color="suggestion" wrap="truncate">
                {agent.lastTool ?? 'starting'}
              </Text>
            ) : (
              <Text>{tokens(agent.tokens)}</Text>
            )}
          </Box>
          <Box width={8}>
            {agent.verdict !== undefined && (
              <Text color={verdictTone(agent.verdict)} bold>
                {agent.verdict}
              </Text>
            )}
          </Box>
        </Box>
      )
    }

    return (
      <Box flexDirection="column">
        {groups.map(group => (
          <Box key={group.key} flexDirection="column" marginBottom={1}>
            <Box flexDirection="row" columnGap={1}>
              <Box flexGrow={1} flexShrink={1}>
                <Text color="claude" bold wrap="truncate">
                  {group.title}
                </Text>
              </Box>
              <Text>
                {group.done}/{group.agents.length} ·{' '}
                {elapsed((group.endedAt ?? latest) - group.startedAt)} ·{' '}
                {tokens(group.tokens)}
              </Text>
            </Box>
            {group.agents.map(row)}
          </Box>
        ))}
      </Box>
    )
  })
}
