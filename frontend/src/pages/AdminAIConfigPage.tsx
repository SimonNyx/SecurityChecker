import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAIConfig, updateAIConfig } from '../api/aiConfig'
import type { AIProvider, AIConfigUpdate } from '../types'

const PROVIDERS: AIProvider[] = ['openwebui', 'ollama', 'gemini']

export default function AdminAIConfigPage() {
  const qc = useQueryClient()
  const { data: config, isLoading } = useQuery({ queryKey: ['ai-config'], queryFn: getAIConfig })

  const [form, setForm] = useState<AIConfigUpdate>({
    provider: 'openwebui',
    base_url: '',
    model_name: '',
    api_key: '',
  })
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (config) {
      setForm({ provider: config.provider, base_url: config.base_url, model_name: config.model_name, api_key: '' })
    }
  }, [config])

  const saveMut = useMutation({
    mutationFn: updateAIConfig,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['ai-config'] }); setSaved(true); setTimeout(() => setSaved(false), 3000) },
  })

  if (isLoading) return <div className="text-gray-400 text-sm">Loading…</div>

  return (
    <div className="space-y-6 max-w-xl">
      <h2 className="text-2xl font-bold text-gray-900">AI Configuration</h2>

      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
          <select
            value={form.provider}
            onChange={e => setForm(f => ({ ...f, provider: e.target.value as AIProvider }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {PROVIDERS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
          <input
            type="url"
            value={form.base_url}
            onChange={e => setForm(f => ({ ...f, base_url: e.target.value }))}
            placeholder="http://openwebui:3000"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Model Name</label>
          <input
            type="text"
            value={form.model_name}
            onChange={e => setForm(f => ({ ...f, model_name: e.target.value }))}
            placeholder="llama3.1:70b"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            API Key <span className="text-gray-400 font-normal">(leave blank to keep existing)</span>
          </label>
          <input
            type="password"
            value={form.api_key}
            onChange={e => setForm(f => ({ ...f, api_key: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => saveMut.mutate(form)}
            disabled={saveMut.isPending}
            className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
          >
            {saveMut.isPending ? 'Saving…' : 'Save Configuration'}
          </button>
          {saved && <span className="text-green-700 text-sm font-medium">Saved!</span>}
          {saveMut.isError && <span className="text-red-600 text-sm">Save failed.</span>}
        </div>
      </div>

      {config && (
        <div className="text-xs text-gray-400 space-y-1">
          <p>Active: {config.is_active ? 'Yes' : 'No'}</p>
          <p>Last updated: {new Date(config.created_at).toLocaleDateString()}</p>
        </div>
      )}
    </div>
  )
}
