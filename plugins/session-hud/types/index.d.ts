export type Todo = { line: number; text: string; isDone: boolean }

export type Limit = { kind: string; percent: number; resetsAt?: number }

export type Usage = {
  contextPercent?: number
  limits: Limit[]
  costUsd?: number
  measuredAt: number
}

export type OrchStatus = 'running' | 'done' | 'failed' | 'aborted'

export type OrchAgent = {
  id: string
  description: string
  type: string
  model: string
  // a workflow run's Workflow tool_use_id, the parent agent's id, or "main"
  group: string
  runId?: string
  status: OrchStatus
  startedAt: number
  endedAt?: number
  tokens: number
  verdict?: string
  lastTool?: string
}

export type Orch = {
  agents: OrchAgent[]
  // group key -> title shown above its agents
  titles: Record<string, string>
}

declare module 'claude-code' {
  interface PluginState {
    'session-hud': {
      todos: Shaped<Todo[]>
      usage: Shaped<Usage | null>
      orch: Shaped<Orch>
      orchNow: number
    }
  }
}
