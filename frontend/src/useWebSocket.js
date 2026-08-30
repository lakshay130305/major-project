import { useEffect, useRef, useState } from 'react'
import { WS_PATH } from './config'

// Subscribes to a backend live-push channel, token-authenticated.
// `path` defaults to the admin alert feed (/ws/alerts); pass an explicit
// path (e.g. `/ws/tourist/{id}`) to use the per-tourist channel instead.
export default function useWebSocket(onEvent, path = WS_PATH) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const cbRef = useRef(onEvent)
  cbRef.current = onEvent

  useEffect(() => {
    if (!path) return undefined
    const token = localStorage.getItem('token')
    if (!token) return undefined
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    // Token passed as a query param so the server can authorize the socket.
    const url = `${proto}://${location.host}${path}?token=${encodeURIComponent(token)}`
    const ws = new WebSocket(url)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        cbRef.current && cbRef.current(data)
      } catch { /* ignore */ }
    }
    return () => ws.close()
  }, [path])

  return { connected }
}
