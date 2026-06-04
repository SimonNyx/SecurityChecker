import { useState, useEffect } from 'react'

function formatElapsed(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${s}s`
}

function parseUTC(ts: string): number {
  return new Date(ts.endsWith('Z') ? ts : ts + 'Z').getTime()
}

interface Props {
  since: string
  className?: string
}

export default function ElapsedTimer({ since, className }: Props) {
  const [elapsed, setElapsed] = useState(() =>
    Math.floor((Date.now() - parseUTC(since)) / 1000)
  )

  useEffect(() => {
    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - parseUTC(since)) / 1000))
    }, 1000)
    return () => clearInterval(id)
  }, [since])

  return <span className={className}>{formatElapsed(elapsed)}</span>
}
