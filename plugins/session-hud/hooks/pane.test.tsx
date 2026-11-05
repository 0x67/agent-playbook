import { expect, test } from 'claude-code/testing'
import type { On } from 'claude-code'

const PANE = {
  plugin: 'session-hud',
  component: 'Pane',
  requestId: 'todo',
  props: {
    title: 'Shared TODO',
    isFocused: false,
    bodyColumns: 40,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const

const HINT = {
  plugin: 'session-hud',
  component: 'PromptHint',
  requestId: 'hint',
  props: { isDraft: false, isWorking: false, hint: '? for shortcuts' },
} as const

const TODOS = [
  { line: 2, text: 'write release notes', isDone: false },
  { line: 3, text: 'update docs', isDone: true },
]

const USAGE = {
  contextPercent: 42,
  limits: [
    { kind: 'five_hour', percent: 23, resetsAt: 1_000 + 2 * 3_600_000 },
    { kind: 'seven_day', percent: 91 },
  ],
  costUsd: 3.125,
  measuredAt: 1_000,
}

function seed(on: On) {
  on('state.get', (_, e) => {
    if (e.key === 'todos') {
      return { value: { value: { shape: 'todos-1', value: TODOS }, version: 1 } }
    }
    if (e.key === 'usage') {
      return { value: { value: { shape: 'usage-1', value: USAGE }, version: 1 } }
    }
    return { value: { value: false, version: 1 } }
  })
}

test('the pane lists open and done items, on every surface', async ($, on) => {
  seed(on)
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /^1 open$/ }))?.text).toMatch(/^1 open$/)
    expect((await ui.find({ type: 'Text', text: /^write release notes$/ }))?.text).toMatch(/^write release notes$/)
    expect((await ui.find({ type: 'Text', text: /^update docs$/ }))?.text).toMatch(/^update docs$/)
    await ui.unmount()
  }
})

test('an empty list says so', async $ => {
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /Nothing/ }))?.text).toBe(
    'Nothing on the list.',
  )
  await ui.unmount()
})

test('the hint line keeps its hints and labels each figure', async ($, on) => {
  seed(on)
  // stands for the engine's own hint line beneath the mod
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>? for shortcuts</Text>
  })
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...HINT, surface })
    expect((await ui.find({ type: 'Text', text: /shortcuts/ }))?.text).toBe(
      '? for shortcuts',
    )
    for (const label of [/^Context $/, /^5h limit $/, /^Weekly $/, /^Cost $/, /^TODO $/]) {
      expect((await ui.find({ type: 'Text', text: label }))?.text).toMatch(label)
    }
    expect((await ui.find({ type: 'Text', text: /^ ↻ 2h 0m$/ }))?.text).toMatch(/^ ↻ 2h 0m$/)
    expect((await ui.find({ type: 'Text', text: /^\$3\.13$/ }))?.text).toMatch(/^\$3\.13$/)
    await ui.unmount()
  }
})

test('/todo shows a hidden pane and hides a shown one', async ($, on) => {
  seed(on)
  let isShown = false
  const calls: string[] = []
  on('ui.panes', () => ({
    value: isShown
      ? [{ id: 'todo', title: 'Shared TODO', isShown: true, isFocused: false, isPlaced: true }]
      : [],
  }))
  on('ui.open', () => {
    calls.push('open')
    isShown = true
    return { value: { isPlaced: true } }
  })
  on('ui.close', () => {
    calls.push('close')
    isShown = false
    return { value: undefined }
  })
  const todo = (args: string) =>
    $.command.run({
      command: 'todo',
      args,
      origin: { kind: 'composer' },
      presentation: { isFullscreen: true, columns: 160 },
    })

  expect((await todo('')).text).toBe(
    'TODO pane shown (1 open).',
  )
  expect((await todo('')).text).toBe('TODO pane hidden.')
  expect((await todo('hide')).text).toBe(
    'TODO pane hidden.',
  )
  expect(calls).toEqual(['open', 'close', 'close'])
})
