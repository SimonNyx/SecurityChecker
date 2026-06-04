import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listAIConfigs, upsertAIConfig, activateAIConfig, testAIConnection } from '../api/aiConfig'
import type { AIProvider, AIConfig } from '../types'

const PROVIDER_LABELS: Record<AIProvider, string> = {
  openwebui: 'Open WebUI',
  ollama: 'Ollama',
  gemini: 'Gemini',
}

const PROVIDER_PLACEHOLDERS: Record<AIProvider, { url: string; model: string }> = {
  openwebui: { url: 'http://openwebui:3000', model: 'llama3.1:70b' },
  ollama: { url: 'http://ollama:11434', model: 'llama3.1:70b' },
  gemini: { url: 'https://generativelanguage.googleapis.com', model: 'gemini-1.5-pro' },
}

function ProviderCard({ config, onSaved }: { config: AIConfig; onSaved: () => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ base_url: config.base_url, model_name: config.model_name, api_key: '' })
  const [saved, setSaved] = useState(false)
  const ph = PROVIDER_PLACEHOLDERS[config.provider]

  const saveMut = useMutation({
    mutationFn: () => upsertAIConfig(config.provider, {
      base_url: form.base_url || undefined,
      model_name: form.model_name || undefined,
      api_key: form.api_key || undefined,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ai-configs'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
      onSaved()
    },
  })

  const activateMut = useMutation({
    mutationFn: () => activateAIConfig(config.provider),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-configs'] }),
  })

  return (
    <div className={`bg-white border rounded-xl p-5 space-y-4 ${config.is_active ? 'border-blue-400 ring-1 ring-blue-300' : 'border-gray-200'}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900">{PROVIDER_LABELS[config.provider]}</h3>
          {config.is_active && (
            <span className="text-xs font-medium bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">Active</span>
          )}
          {config.has_api_key && (
            <span className="text-xs font-medium bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Key stored</span>
          )}
        </div>
        {!config.is_active && (
          <button
            onClick={() => activateMut.mutate()}
            disabled={activateMut.isPending || !config.base_url}
            className="text-xs bg-gray-100 border border-gray-300 text-gray-700 px-3 py-1.5 rounded-lg hover:bg-gray-200 disabled:opacity-40"
            title={!config.base_url ? 'Save settings first' : undefined}
          >
            {activateMut.isPending ? 'Activating…' : 'Set Active'}
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-600 mb-1">Base URL</label>
          <input
            type="url"
            value={form.base_url}
            onChange={e => setForm(f => ({ ...f, base_url: e.target.value }))}
            placeholder={ph.url}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Model Name</label>
          <input
            type="text"
            value={form.model_name}
            onChange={e => setForm(f => ({ ...f, model_name: e.target.value }))}
            placeholder={ph.model}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            API Key {config.has_api_key && <span className="text-gray-400 font-normal">(leave blank to keep)</span>}
          </label>
          <input
            type="password"
            value={form.api_key}
            onChange={e => setForm(f => ({ ...f, api_key: e.target.value }))}
            placeholder={config.has_api_key ? '••••••••' : 'Optional'}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => saveMut.mutate()}
          disabled={saveMut.isPending}
          className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
        >
          {saveMut.isPending ? 'Saving…' : 'Save'}
        </button>
        {saved && <span className="text-green-700 text-sm font-medium">Saved!</span>}
        {saveMut.isError && <span className="text-red-600 text-sm">Save failed.</span>}
        {activateMut.isError && <span className="text-red-600 text-sm">Could not activate — save settings first.</span>}
      </div>
    </div>
  )
}

export default function AdminAIConfigPage() {
  const qc = useQueryClient()
  const { data: configs, isLoading } = useQuery({ queryKey: ['ai-configs'], queryFn: listAIConfigs })
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [testing, setTesting] = useState(false)

  if (isLoading) return <div className="text-gray-400 text-sm">Loading…</div>

  const active = configs?.find(c => c.is_active)

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">AI Configuration</h2>
        {active && (
          <button
            onClick={async () => {
              setTesting(true)
              setTestResult(null)
              try {
                const r = await testAIConnection()
                setTestResult({ ok: true, message: `${PROVIDER_LABELS[r.provider as AIProvider]} responded: "${r.response}"` })
              } catch (e: unknown) {
                const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Connection failed'
                setTestResult({ ok: false, message: msg })
              } finally {
                setTesting(false)
              }
            }}
            disabled={testing}
            className="bg-gray-100 border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 disabled:opacity-50"
          >
            {testing ? 'Testing…' : 'Test Active Provider'}
          </button>
        )}
      </div>

      {testResult && (
        <div className={`rounded-lg px-4 py-3 text-sm ${testResult.ok ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
          {testResult.ok ? '✓ ' : '✗ '}{testResult.message}
        </div>
      )}

      <div className="space-y-4">
        {configs?.map(config => (
          <ProviderCard key={config.provider} config={config} onSaved={() => qc.invalidateQueries({ queryKey: ['ai-configs'] })} />
        ))}
      </div>
    </div>
  )
}
