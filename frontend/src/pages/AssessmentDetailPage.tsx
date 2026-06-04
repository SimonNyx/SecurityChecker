import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { getAssessment, confirmProduct, downloadPdf, deleteAssessment, rerunAssessment } from '../api/assessments'
import type { ReviewMode } from '../types'
import RAGBadge from '../components/RAGBadge'
import FindingCard from '../components/FindingCard'
import ElapsedTimer from '../components/ElapsedTimer'

const SECTION_PATTERNS: [RegExp, string][] = [
  [/overall\s+posture/i, 'Overall Posture'],
  [/key\s+strengths?/i, 'Key Strengths'],
  [/key\s+concerns?/i, 'Key Concerns'],
  [/recommended?\s+next\s+steps?/i, 'Recommended Next Steps'],
]

function matchSection(line: string): string | null {
  const clean = line.replace(/^[#*\s]+|[#*\s]+$/g, '').trim()
  for (const [pattern, label] of SECTION_PATTERNS) {
    if (pattern.test(clean)) return label
  }
  return null
}

function ExecSummary({ text }: { text: string }) {
  const sections: { heading: string; lines: string[] }[] = []
  let current: { heading: string; lines: string[] } | null = null

  for (const raw of text.split('\n')) {
    const line = raw.trim()
    if (!line) continue
    const matched = matchSection(line)
    if (matched) {
      if (current) sections.push(current)
      current = { heading: matched, lines: [] }
    } else if (current) {
      current.lines.push(line)
    }
  }
  if (current) sections.push(current)

  if (sections.length === 0) {
    return <p className="text-sm text-gray-700 leading-relaxed">{text}</p>
  }

  return (
    <div className="space-y-4">
      {sections.map(s => (
        <div key={s.heading}>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">{s.heading}</h4>
          {s.lines[0]?.startsWith('-') ? (
            <ul className="space-y-1">
              {s.lines.map((l, i) => (
                <li key={i} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-gray-400 mt-0.5">•</span>
                  <span>{l.replace(/^[-•]\s*/, '')}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-700 leading-relaxed">{s.lines.join(' ')}</p>
          )}
        </div>
      ))}
    </div>
  )
}

const MODULE_LABELS: Record<string, string> = {
  vendor_trust: 'Vendor Trust',
  cve: 'CVE History',
  maintenance: 'Maintenance',
  dependency: 'Dependency Risk',
  encryption: 'Encryption',
  logging: 'Logging & Monitoring',
  data_exfiltration: 'Data Exfiltration Risk',
  third_party: 'Third-Party Integrations',
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending', confirming: 'Awaiting Confirmation', running: 'Running…', complete: 'Complete', failed: 'Failed',
}

const RECOMMENDATION_LABELS: Record<string, string> = {
  approve: 'Approve', conditional: 'Conditional Approval', reject: 'Reject',
}

const RECOMMENDATION_COLOURS: Record<string, string> = {
  approve: 'text-green-700 bg-green-50 border-green-200',
  conditional: 'text-amber-700 bg-amber-50 border-amber-200',
  reject: 'text-red-700 bg-red-50 border-red-200',
}

export default function AssessmentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: assessment, isLoading, isError } = useQuery({
    queryKey: ['assessment', id],
    queryFn: () => getAssessment(id!),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'running' || status === 'confirming' ? 3000 : false
    },
  })

  const [confirmForm, setConfirmForm] = useState({
    confirmed_name: '',
    confirmed_vendor: '',
    confirmed_url: '',
  })

  const confirmMut = useMutation({
    mutationFn: (body: typeof confirmForm) => confirmProduct(id!, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assessment', id] }),
  })

  const deleteMut = useMutation({
    mutationFn: () => deleteAssessment(id!),
    onSuccess: () => navigate('/'),
  })

  const [rerunMode, setRerunMode] = useState<ReviewMode>('standard')
  const [rerunScope, setRerunScope] = useState('')
  useEffect(() => {
    if (assessment) {
      setRerunMode(assessment.review_mode)
      setRerunScope(assessment.project_scope ?? '')
    }
  }, [assessment?.id])
  const rerunMut = useMutation({
    mutationFn: () => rerunAssessment(id!, rerunMode, rerunScope || undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assessment', id] }),
  })

  function handleDelete() {
    if (!window.confirm(`Delete this assessment? This cannot be undone.`)) return
    deleteMut.mutate()
  }

  if (isLoading) return <div className="text-gray-400 text-sm">Loading…</div>
  if (isError || !assessment) return <div className="text-red-600 text-sm">Assessment not found.</div>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button onClick={() => navigate('/')} className="text-sm text-blue-600 hover:underline mb-2 block">
            ← Back to Dashboard
          </button>
          <h2 className="text-2xl font-bold text-gray-900">{assessment.product_name}</h2>
          <p className="text-sm text-gray-500 mt-1">
            {STATUS_LABELS[assessment.status]} &middot; {assessment.review_mode === 'deep_review' ? 'Deep Review' : 'Standard'} &middot; {new Date(assessment.created_at).toLocaleDateString('en-GB')}
            {assessment.submitted_by_name && <> &middot; Submitted by <span className="font-medium text-gray-700">{assessment.submitted_by_name}</span></>}
          </p>
          {assessment.project_scope && (
            <p className="text-xs text-blue-700 bg-blue-50 border border-blue-100 rounded-lg px-3 py-1.5 mt-2 max-w-lg">
              <span className="font-semibold">Scope: </span>{assessment.project_scope}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {(assessment.status === 'complete' || assessment.status === 'failed') && (
            <button
              onClick={() => {
                if (!window.confirm(`Re-run assessment for "${assessment.product_name}"? This will clear all existing findings and scores.`)) return
                rerunMut.mutate()
              }}
              disabled={rerunMut.isPending}
              className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
            >
              {rerunMut.isPending ? 'Starting…' : 'Re-run'}
            </button>
          )}
          {assessment.status === 'complete' && (
            <button
              onClick={() => downloadPdf(assessment.id, assessment.product_name)}
              className="bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50"
            >
              Download PDF
            </button>
          )}
          <button
            onClick={handleDelete}
            disabled={deleteMut.isPending}
            className="bg-white border border-red-200 text-red-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-50 disabled:opacity-50"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Re-run panel */}
      {(assessment.status === 'complete' || assessment.status === 'failed') && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-3">
          <h3 className="text-sm font-semibold text-gray-700">Re-run Assessment</h3>
          <div className="grid grid-cols-2 gap-3 items-start">
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600">Review Mode</label>
              <select
                value={rerunMode}
                onChange={e => setRerunMode(e.target.value as ReviewMode)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-300"
              >
                <option value="standard">Standard</option>
                <option value="deep_review">Deep Review</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600">
                Project Scope <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <textarea
                rows={2}
                value={rerunScope}
                onChange={e => setRerunScope(e.target.value)}
                placeholder="Describe project nature to calibrate grading…"
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
              />
            </div>
          </div>
        </div>
      )}

      {/* Running state */}
      {(assessment.status === 'running' || assessment.status === 'pending') && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="animate-pulse text-blue-600 font-medium">Analysis in progress…</div>
            <ElapsedTimer since={assessment.run_started_at ?? assessment.created_at} className="text-sm text-blue-400" />
          </div>
          {assessment.status === 'running' && assessment.progress_total > 0 ? (
            <>
              <div className="flex justify-between text-sm text-blue-500 mb-2">
                <span>
                  {assessment.current_module
                    ? `Running: ${MODULE_LABELS[assessment.current_module] ?? assessment.current_module}`
                    : `${assessment.progress_current} of ${assessment.progress_total} modules complete`}
                </span>
                <span>{assessment.progress_current} / {assessment.progress_total}</span>
              </div>
              <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-500"
                  style={{ width: `${(assessment.progress_current / assessment.progress_total) * 100}%` }}
                />
              </div>
            </>
          ) : (
            <p className="text-sm text-blue-500">This page refreshes automatically.</p>
          )}
        </div>
      )}

      {/* Confirmation form */}
      {assessment.status === 'confirming' && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 space-y-4">
          <h3 className="font-semibold text-amber-900">Confirm Product Identity</h3>
          <p className="text-sm text-amber-800">The AI could not confidently identify this product. Please confirm the details before analysis begins.</p>
          <div className="grid grid-cols-3 gap-3">
            {(['confirmed_name', 'confirmed_vendor', 'confirmed_url'] as const).map(field => (
              <div key={field}>
                <label className="block text-xs font-medium text-amber-800 mb-1 capitalize">{field.replace('confirmed_', '').replace('_', ' ')}</label>
                <input
                  type="text"
                  value={confirmForm[field]}
                  onChange={e => setConfirmForm(f => ({ ...f, [field]: e.target.value }))}
                  className="w-full border border-amber-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>
            ))}
          </div>
          <button
            onClick={() => confirmMut.mutate(confirmForm)}
            disabled={confirmMut.isPending}
            className="bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-amber-700 disabled:opacity-50"
          >
            {confirmMut.isPending ? 'Confirming…' : 'Confirm & Start Analysis'}
          </button>
        </div>
      )}

      {/* Results */}
      {assessment.status === 'complete' && assessment.overall_rag && assessment.recommendation && (
        <>
          <div className={`border rounded-xl p-5 flex items-center gap-6 ${RECOMMENDATION_COLOURS[assessment.recommendation]}`}>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide opacity-70">Recommendation</div>
              <div className="text-2xl font-bold mt-0.5">{RECOMMENDATION_LABELS[assessment.recommendation]}</div>
            </div>
            <div className="border-l border-current opacity-30 h-10" />
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide opacity-70">Overall Score</div>
              <div className="text-2xl font-bold mt-0.5">
                {assessment.overall_score?.toFixed(1)}/10{' '}
                <RAGBadge rag={assessment.overall_rag} />
              </div>
            </div>
          </div>

          {assessment.executive_summary && (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Executive Summary</h3>
              <ExecSummary text={assessment.executive_summary} />
            </div>
          )}

          <div className="space-y-2">
            <h3 className="font-semibold text-gray-900">Module Findings</h3>
            {(assessment.findings ?? []).map(f => (
              <FindingCard key={f.id} finding={f} />
            ))}
          </div>
        </>
      )}

      {assessment.status === 'failed' && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700 text-sm">
          Assessment failed. Please try again or contact your administrator.
        </div>
      )}

      {/* Run history */}
      {assessment.runs.length > 0 && (
        <section>
          <h3 className="font-semibold text-gray-900 mb-3">Previous Runs</h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Date</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Re-run By</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Mode</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Score</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">RAG</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Recommendation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {assessment.runs.map(r => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-500">{new Date(r.run_at.endsWith('Z') ? r.run_at : r.run_at + 'Z').toLocaleDateString('en-GB')}</td>
                    <td className="px-4 py-3 text-gray-700">{r.run_by_name ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-500">{r.review_mode === 'deep_review' ? 'Deep' : 'Standard'}</td>
                    <td className="px-4 py-3 font-medium text-gray-700">{r.overall_score != null ? `${r.overall_score.toFixed(1)}/10` : '—'}</td>
                    <td className="px-4 py-3">{r.overall_rag ? <RAGBadge rag={r.overall_rag} /> : '—'}</td>
                    <td className="px-4 py-3 text-gray-500 capitalize">{r.recommendation ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
