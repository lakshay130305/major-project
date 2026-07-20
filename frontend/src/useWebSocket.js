import { useEffect, useRef, useState } from 'react'

// Subscribes to the backend live alert feed. Returns the latest events (newest first).
export default function useWebSocket(onEvent) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const cbRef = useRef(onEvent)
  cbRef.current = onEvent

  useEffect(() => {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${location.host}/ws/alerts`)
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
