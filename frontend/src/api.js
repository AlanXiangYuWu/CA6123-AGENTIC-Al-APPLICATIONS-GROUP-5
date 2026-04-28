// REST + WS client. Vite proxies /api -> localhost:8000.

const BASE = ''  // proxied

export async function checkHealth() {
  const r = await fetch(`${BASE}/api/health`)
  return r.json()
}

export async function runOnce(userIdea) {
  const r = await fetch(`${BASE}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_idea: userIdea }),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.detail?.blocked_by || err.detail || `HTTP ${r.status}`)
  }
  return r.json()
}

export function streamRun(userIdea, handlers, threadId = '') {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const url = `${proto}://${location.host}/api/ws/run`
  const ws = new WebSocket(url)

  ws.onopen = () => ws.send(JSON.stringify({ user_idea: userIdea, thread_id: threadId || undefined }))
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data)
    handlers.onEvent?.(msg)
  }
  ws.onerror = (e) => handlers.onError?.(e)
  ws.onclose = () => handlers.onClose?.()
  return ws
}
