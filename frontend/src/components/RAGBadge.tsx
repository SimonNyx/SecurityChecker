import type { RAGStatus } from '../types'

const STYLES: Record<RAGStatus, string> = {
  green: 'bg-green-100 text-green-800',
  amber: 'bg-amber-100 text-amber-800',
  red: 'bg-red-100 text-red-800',
}

const LABELS: Record<RAGStatus, string> = {
  green: 'GREEN',
  amber: 'AMBER',
  red: 'RED',
}

export default function RAGBadge({ rag }: { rag: RAGStatus }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${STYLES[rag]}`}>
      {LABELS[rag]}
    </span>
  )
}
