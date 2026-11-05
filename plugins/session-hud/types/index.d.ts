export type Todo = { line: number; text: string; isDone: boolean }

export type Limit = { kind: string; percent: number; resetsAt?: number }

export type Usage = {
  contextPercent?: number
  limits: Limit[]
  costUsd?: number
  measuredAt: number
}

declare module 'claude-code' {
  interface PluginState {
    'session-hud': {
      todos: Shaped<Todo[]>
      usage: Shaped<Usage | null>
    }
  }
}
