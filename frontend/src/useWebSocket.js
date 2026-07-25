import { useEffect, useRef, useState } from 'react'
import { WS_PATH } from './config'

// Subscribes to the backend live alert feed (admin-only, token-authenticated).
export default function useWebSocket(onEvent) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const cbRef = useRef(onEvent)
  cbRef.current = onEvent

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    // Token passed as a query param so the server can authorize the socket.
    const url = `${proto}://${location.host}${WS_PATH}?token=${encodeURIComponent(token)}`
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
  }, [])

  return { connected }
}
