import { useState } from 'react'
import type { AssessmentFinding } from '../types'
import RAGBadge from './RAGBadge'
import ScoreBar from './ScoreBar'

const CATEGORY_LABELS: Record<string, string> = {
  vendor_trust: 'Vendor Trust',
  cve: 'CVE History',
  maintenance: 'Maintenance',
  dependency: 'Dependency Risk',
  encryption: 'Encryption',
  logging: 'Logging & Monitoring',
  data_exfiltration: 'Data Exfiltration Risk',
  third_party: 'Third-Party Integrations',
}

export default function FindingCard({ finding }: { finding: AssessmentFinding }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 text-left"
      >
        <RAGBadge rag={finding.rag} />
        <span className="flex-1 font-medium text-gray-900 text-sm">
          {CATEGORY_LABELS[finding.category] ?? finding.category}
        </span>
        <div className="w-32">
          <ScoreBar score={finding.score} />
        </div>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          <p className="mt-3 text-sm text-gray-700">{finding.summary}</p>
          {finding.analyst_notes && (
            <div className="mt-3 p-3 bg-yellow-50 rounded-lg text-sm text-yellow-900">
              <span className="font-semibold">Analyst note: </span>{finding.analyst_notes}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
