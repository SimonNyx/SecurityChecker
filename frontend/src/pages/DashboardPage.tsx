import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { listAssessments, deleteAssessment } from '../api/assessments'
import RAGBadge from '../components/RAGBadge'
import ScoreBar from '../components/ScoreBar'
import ElapsedTimer from '../components/ElapsedTimer'

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  confirming: 'Confirming',
  running: 'Running…',
  complete: 'Complete',
  failed: 'Failed',
}

const STATUS_COLOURS: Record<string, string> = {
  pending: 'text-gray-500',
  confirming: 'text-blue-600',
  running: 'text-blue-600 animate-pulse',
  complete: 'text-green-700',
  failed: 'text-red-600',
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

const RECOMMENDATION_LABELS: Record<string, string> = {
  approve: 'Approve',
  conditional: 'Conditional',
  reject: 'Reject',
}

export default function DashboardPage() {
  const qc = useQueryClient()
  const deleteMut = useMutation({
    mutationFn: deleteAssessment,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assessments'] }),
  })

  function handleDelete(id: string, name: string) {
    if (!window.confirm(`Delete assessment for "${name}"? This cannot be undone.`)) return
    deleteMut.mutate(id)
  }

  const [search, setSearch] = useState('')

  const { data: assessments, isLoading, isError } = useQuery({
    queryKey: ['assessments'],
    queryFn: () => listAssessments({ limit: 50 }),
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 5000
      const hasRunning = data.some(a => a.status === 'running' || a.status === 'confirming')
      return hasRunning ? 3000 : false
    },
  })

  if (isLoading) {
    return <div className="text-gray-400 text-sm">Loading assessments…</div>
  }

  if (isError) {
    return <div className="text-red-600 text-sm">Failed to load assessments.</div>
  }
  const complete = assessments?.filter(a => a.status === 'complete') ?? []
  const filtered = search.trim()
    ? complete.filter(a => a.product_name.toLowerCase().includes(search.toLowerCase()))
    : complete
  const inProgress = assessments?.filter(a => a.status !== 'complete') ?? []

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-sm text-gray-500 mt-1">{assessments?.length ?? 0} total assessments</p>
        </div>
        <Link
          to="/assessments/new"
          className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800"
        >
          New Assessment
        </Link>
      </div>

      {/* Summary cards */}
      {complete.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          {(['green', 'amber', 'red'] as const).map(rag => {
            const count = complete.filter(a => a.overall_rag === rag).length
            const colourMap = { green: 'text-green-700 bg-green-50 border-green-200', amber: 'text-amber-700 bg-amber-50 border-amber-200', red: 'text-red-700 bg-red-50 border-red-200' }
            return (
              <div key={rag} className={`border rounded-xl p-4 ${colourMap[rag]}`}>
                <div className="text-3xl font-bold">{count}</div>
                <div className="text-sm font-medium uppercase mt-1">{rag}</div>
              </div>
            )
          })}
        </div>
      )}

      {/* In-progress */}
      {inProgress.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">In Progress</h3>
          <div className="space-y-2">
            {inProgress.map(a => (
              <div key={a.id} className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <Link to={`/assessments/${a.id}`} className="font-medium text-blue-700 hover:underline text-sm">
                      {a.product_name}
                    </Link>
                  </div>
                  <span className={`text-xs font-medium ${STATUS_COLOURS[a.status]}`}>
                    {STATUS_LABELS[a.status]}
                  </span>
                  {(a.status === 'running' || a.status === 'confirming' || a.status === 'pending') && (
                    <ElapsedTimer since={a.created_at} className="text-xs text-gray-400" />
                  )}
                  <button
                    onClick={() => handleDelete(a.id, a.product_name)}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    Delete
                  </button>
                </div>
                {a.status === 'running' && a.progress_total > 0 && (
                  <div className="mt-2">
                    <div className="flex justify-between text-xs text-gray-400 mb-1">
                      <span>{a.current_module ? `Running: ${MODULE_LABELS[a.current_module] ?? a.current_module}` : `${a.progress_current} / ${a.progress_total} modules`}</span>
                      <span>{a.progress_current} / {a.progress_total}</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all duration-500"
                        style={{ width: `${(a.progress_current / a.progress_total) * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Complete assessments table */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Completed</h3>
          {complete.length > 0 && (
            <input
              type="search"
              placeholder="Search by product name…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          )}
        </div>
        {complete.length === 0 ? (
          <div className="text-gray-400 text-sm py-8 text-center border border-dashed border-gray-200 rounded-lg">
            No completed assessments yet.{' '}
            <Link to="/assessments/new" className="text-blue-600 hover:underline">Run your first one.</Link>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-gray-400 text-sm py-8 text-center border border-dashed border-gray-200 rounded-lg">
            No results for "{search}".
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Product</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Score</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">RAG</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Recommendation</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Mode</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Submitted By</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Date</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map(a => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link to={`/assessments/${a.id}`} className="font-medium text-blue-700 hover:underline">
                        {a.product_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 w-40">
                      {a.overall_score != null ? <ScoreBar score={a.overall_score} /> : '—'}
                    </td>
                    <td className="px-4 py-3">
                      {a.overall_rag ? <RAGBadge rag={a.overall_rag} /> : '—'}
                    </td>
                    <td className="px-4 py-3 capitalize text-gray-700">
                      {a.recommendation ? RECOMMENDATION_LABELS[a.recommendation] : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-500 capitalize">
                      {a.review_mode === 'deep_review' ? 'Deep' : 'Standard'}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {a.submitted_by_name ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {new Date(a.created_at).toLocaleDateString('en-GB')}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDelete(a.id, a.product_name)}
                        className="text-xs text-red-500 hover:text-red-700"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
