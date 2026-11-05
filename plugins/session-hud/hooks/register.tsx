import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Limit, Todo, Usage } from '../types'

const PANE = 'todo'
const TITLE = 'Shared TODO'
const PANE_COLUMNS = 34
// one file every session reads, so a change in one shows in the others
const FILE_NAME = '.claude-todo.md'
const POLL_MS = 2000
const USAGE_EVERY_TICKS = 15

const todos = atom({ plugin: 'session-hud', key: 'todos' } as const, [], {
  shape: 'todos-1',
})
const usage = atom({ plugin: 'session-hud', key: 'usage' } as const, null, {
  shape: 'usage-1',
})

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

function meter(percent: number, cells: number): [string, string] {
  const filled = Math.min(cells, Math.max(0, Math.round((percent / 100) * cells)))
  return ['█'.repeat(filled), '░'.repeat(cells - filled)]
}

// module state; a reload starts it over, which only re-reads the file
let file = ''
let lastMtime = -1

async function todoFile($: EngineInterface) {
  if (file === '') {
    const home =
      (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')) ?? '.'
    file = `${home}/${FILE_NAME}`
  }
  return file
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
    await load($, true)
    await measure($)

    let ticks = 0
    $.clock.every(POLL_MS, () => {
      ticks += 1
      void load($).then(() =>
        ticks % USAGE_EVERY_TICKS === 0 ? measure($) : undefined,
      )
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

  // usage sits on the hint line under the prompt, a row below the engine's
  // own hints; the TODO pane stays hidden until /todo shows it
  on('ui.render', { component: 'PromptHint' }, async ($, e, next) => {
    const figures = await read($, usage)
    const engine = await next(e)
    if (figures === null) return engine

    const { Box, Text } = $.ui.resolve(e)
    const list = await read($, todos)
    const open = list.filter(one => !one.isDone).length
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
            {Math.round(percent)}%
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
}
