import { expect, test } from 'claude-code/testing'

import {
  groupAgents,
  parseVerdict,
  shortModel,
  shortType,
  workflowTitle,
} from './orch'

test('verdicts come from verdict lines and JSON, not from prose', () => {
  expect(parseVerdict('Review done.\n\nAPPROVED\n')?.label).toBe('APPROVED')
  expect(parseVerdict('**Verdict:** VERIFIED WITH CAVEATS')?.label).toBe('CAVEATS')
  expect(parseVerdict('**Verdict**: FAILED')?.label).toBe('FAILED')
  expect(parseVerdict('## REFUTED\nThe test was weakened.')?.label).toBe('REFUTED')
  expect(parseVerdict('Status: NEEDS_REVISION (2 findings)')?.label).toBe('REVISE')
  expect(parseVerdict('{"verdict": "verified", "findings": []}')?.label).toBe(
    'VERIFIED',
  )
  expect(parseVerdict('The tests FAILED before the fix, now they pass.')).toBe(
    undefined,
  )
  expect(parseVerdict('Implemented the change in two files.')).toBe(undefined)
  expect(parseVerdict('{\n  "status": "DONE",\n  "files_changed": []\n}')?.label).toBe('DONE')
  expect(parseVerdict('Status: BLOCKED (missing fixture)')?.label).toBe('BLOCKED')
  expect(parseVerdict('Done with the first pass, moving on.')).toBe(undefined)
})

test('model, type and workflow names are shortened', () => {
  expect(shortModel('claude-opus-5-5')).toBe('opus 5.5')
  expect(shortModel('claude-haiku-4-5-20251001')).toBe('haiku 4.5')
  expect(shortModel('sonnet')).toBe('sonnet')
  expect(shortType('ai-setup:implement-subagent')).toBe('implement')
  expect(shortType('general-purpose')).toBe('general')
  expect(
    workflowTitle({
      script: "export const meta = { name: 'review-changes', description: 'x' }",
    }),
  ).toBe('review-changes')
  expect(workflowTitle({ scriptPath: '/tmp/runs/nightly-audit.js' })).toBe(
    'nightly-audit',
  )
})

test('agents group by run, newest run first', () => {
  const base = { type: 'Explore', model: 'haiku', tokens: 10 } as const
  const groups = groupAgents(
    [
      { ...base, id: 'a', description: 'one', group: 'g1', status: 'done', startedAt: 1, endedAt: 5 },
      { ...base, id: 'b', description: 'two', group: 'g2', status: 'running', startedAt: 3 },
      { ...base, id: 'c', description: 'three', group: 'g1', status: 'failed', startedAt: 2, endedAt: 4 },
    ],
    { g1: 'First run' },
  )
  expect(groups.map(group => group.key)).toEqual(['g2', 'g1'])
  expect(groups[1]?.title).toBe('First run')
  expect(groups[1]?.done).toBe(2)
  expect(groups[1]?.endedAt).toBe(5)
  expect(groups[0]?.endedAt).toBe(undefined)
})

const ORCH_PANE = {
  plugin: 'session-hud',
  component: 'Pane',
  requestId: 'orch',
  props: {
    title: 'Agents',
    isFocused: false,
    bodyColumns: 70,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 30 },
    view: {},
  },
} as const

test('a workflow agent shows under its run, with tokens and verdict', async ($, on) => {
  const written: string[] = []
  // spawn reads the clock once and completion once: a minute apart
  const times = [1_700_000_000_000, 1_700_000_061_000]
  on('clock.now', () => ({ value: times.shift() ?? 1_700_000_061_000 }))
  on('agent.spawn', () => ({ model: 'claude-opus-5-5', agentId: 'agent-1' }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('tool.call', () => ({ result: {} }))
  on('session.id', () => ({ value: 'session-0001' }))
  on('env.get', () => ({ value: '/home/test' }))
  on('fs.exists', () => ({ value: false }))
  on('fs.write', (_, e) => {
    expect(e.path).toBe('/home/test/.claude-orch-log/2023-11-14-session-.jsonl')
    written.push(e.text)
    return { value: undefined }
  })

  await $.tool.call({
    tool: 'Workflow',
    tool_use_id: 'toolu_wf',
    script: "export const meta = { name: 'release-check' }",
  })
  await $.agent.spawn({
    tool_use_id: 'toolu_wf',
    prompt: 'verify the release notes',
    description: 'notes-verify',
    subagentType: 'ai-setup:code-review-subagent',
    provider: { plugin: 'ai-setup', tier: 'user' },
    parentModel: 'claude-opus-5-5',
    background: true,
    fork: false,
    workflow: { runId: 'wf_test', agentIndex: 1 },
  })
  await $.turn.complete({
    answer: 'Checked every claim.\n\nVERIFIED',
    durationMs: 61_000,
    isAborted: false,
    turnId: 'turn-1',
    agentId: 'agent-1',
    reason: 'answer',
    usage: {
      model: 'claude-opus-5-5',
      input_tokens: 1_000,
      output_tokens: 2_000,
      cache_read_input_tokens: 40_000,
      cache_creation_input_tokens: 500,
    },
  })

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...ORCH_PANE, surface })
    expect((await ui.find({ type: 'Text', text: /release-check/ }))?.text).toBe(
      'release-check',
    )
    expect((await ui.find({ type: 'Text', text: /notes-verify/ }))?.text).toBe(
      'notes-verify',
    )
    expect((await ui.find({ type: 'Text', text: /^43\.5k$/ }))?.text).toBe('43.5k')
    expect((await ui.find({ type: 'Text', text: /^VERIFIED$/ }))?.text).toBe(
      'VERIFIED',
    )
    await ui.unmount()
  }

  const line = JSON.parse(written.at(-1)?.trim().split('\n').at(-1) ?? '{}')
  expect(line.group).toBe('release-check')
  expect(line.verdict).toBe('VERIFIED')
  expect(line.output_tokens).toBe(2_000)
  expect(line.model).toBe('claude-opus-5-5')
})
