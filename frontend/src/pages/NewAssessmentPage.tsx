import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { createAssessment } from '../api/assessments'
import type { ReviewMode } from '../types'

export default function NewAssessmentPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    product_name: '',
    product_url: '',
    repo_url: '',
    review_mode: 'standard' as ReviewMode,
    project_scope: '',
  })
  const [error, setError] = useState<string | null>(null)

  const mut = useMutation({
    mutationFn: createAssessment,
    onSuccess: (assessment) => navigate(`/assessments/${assessment.id}`),
    onError: () => setError('Failed to start assessment. Please try again.'),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    mut.mutate({
      product_name: form.product_name,
      product_url: form.product_url || undefined,
      repo_url: form.repo_url || undefined,
      review_mode: form.review_mode,
      project_scope: form.project_scope || undefined,
    })
  }

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">New Assessment</h2>
        <p className="text-sm text-gray-500 mt-1">Enter the product details to begin a security assessment.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Product Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            required
            value={form.product_name}
            onChange={e => setForm(f => ({ ...f, product_name: e.target.value }))}
            placeholder="e.g. Slack, GitHub Copilot"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Website URL</label>
          <input
            type="url"
            value={form.product_url}
            onChange={e => setForm(f => ({ ...f, product_url: e.target.value }))}
            placeholder="https://example.com"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Repository URL</label>
          <input
            type="url"
            value={form.repo_url}
            onChange={e => setForm(f => ({ ...f, repo_url: e.target.value }))}
            placeholder="https://github.com/org/repo"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Project Scope <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <textarea
            rows={3}
            value={form.project_scope}
            onChange={e => setForm(f => ({ ...f, project_scope: e.target.value }))}
            placeholder="Describe the project's nature, audience, and purpose. e.g. 'Small community fork removing upload features to reduce data exfiltration risk. Intended for personal/small team use, not enterprise deployment.'"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <p className="text-xs text-gray-400 mt-1">AI modules will adjust grading expectations based on this context.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Review Mode</label>
          <div className="grid grid-cols-2 gap-3">
            {(['standard', 'deep_review'] as ReviewMode[]).map(mode => (
              <label
                key={mode}
                className={`flex flex-col p-3 border rounded-lg cursor-pointer transition-colors ${
                  form.review_mode === mode ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name="review_mode"
                  value={mode}
                  checked={form.review_mode === mode}
                  onChange={() => setForm(f => ({ ...f, review_mode: mode }))}
                  className="sr-only"
                />
                <span className="font-medium text-sm text-gray-900">
                  {mode === 'standard' ? 'Standard' : 'Deep Review'}
                </span>
                <span className="text-xs text-gray-500 mt-0.5">
                  {mode === 'standard' ? '~8 AI calls per module' : '~88 AI calls — council of 5 advisors'}
                </span>
              </label>
            ))}
          </div>
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={mut.isPending}
          className="w-full bg-blue-700 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
        >
          {mut.isPending ? 'Starting…' : 'Start Assessment'}
        </button>
      </form>
    </div>
  )
}
