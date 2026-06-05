import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../hooks/useAuth'
import { listAPIKeys, createAPIKey, revokeAPIKey } from '../api/apiKeys'
import client from '../api/client'
import type { APIKey } from '../types'

const EXPIRY_OPTIONS = [
  { label: '1 day', value: 1 },
  { label: '1 week', value: 7 },
  { label: '1 month', value: 30 },
  { label: '3 months', value: 90 },
  { label: '6 months', value: 180 },
  { label: '12 months', value: 365 },
]

function formatDate(ts: string) {
  return new Date(ts.endsWith('Z') ? ts : ts + 'Z').toLocaleDateString('en-GB')
}

function isExpired(ts: string) {
  return new Date(ts.endsWith('Z') ? ts : ts + 'Z') < new Date()
}

export default function ProfilePage() {
  const { currentUser } = useAuth()
  const qc = useQueryClient()

  // Change password
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm: '' })
  const [pwError, setPwError] = useState<string | null>(null)
  const [pwSuccess, setPwSuccess] = useState(false)
  const [pwLoading, setPwLoading] = useState(false)

  async function handleChangePassword() {
    setPwError(null)
    if (pwForm.new_password !== pwForm.confirm) { setPwError('New passwords do not match'); return }
    setPwLoading(true)
    try {
      await client.post('/auth/change-password', {
        current_password: pwForm.current_password,
        new_password: pwForm.new_password,
      })
      setPwSuccess(true)
      setPwForm({ current_password: '', new_password: '', confirm: '' })
      setTimeout(() => setPwSuccess(false), 3000)
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setPwError(detail ?? 'Failed to change password')
    } finally {
      setPwLoading(false)
    }
  }

  // API keys
  const { data: apiKeys } = useQuery({
    queryKey: ['api-keys'],
    queryFn: listAPIKeys,
    enabled: !!currentUser?.can_generate_api_keys,
  })
  const [newKey, setNewKey] = useState<APIKey | null>(null)
  const [keyForm, setKeyForm] = useState({ name: '', expires_in_days: 30 })

  const createMut = useMutation({
    mutationFn: () => createAPIKey(keyForm.name, keyForm.expires_in_days),
    onSuccess: (key) => {
      setNewKey(key)
      setKeyForm({ name: '', expires_in_days: 30 })
      qc.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })

  const revokeMut = useMutation({
    mutationFn: revokeAPIKey,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['api-keys'] }),
  })

  return (
    <div className="space-y-8 max-w-xl">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Profile</h2>
        <p className="text-sm text-gray-500 mt-1">{currentUser?.email} &middot; <span className="capitalize">{currentUser?.role}</span></p>
      </div>

      {/* Change password */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <h3 className="font-semibold text-gray-900">Change Password</h3>
        <div className="space-y-3">
          {(['current_password', 'new_password', 'confirm'] as const).map(field => (
            <div key={field}>
              <label className="block text-xs font-medium text-gray-600 mb-1 capitalize">
                {field === 'confirm' ? 'Confirm new password' : field.replace('_', ' ')}
              </label>
              <input
                type="password"
                value={pwForm[field]}
                onChange={e => setPwForm(f => ({ ...f, [field]: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
            </div>
          ))}
        </div>
        {pwError && <p className="text-red-600 text-sm">{pwError}</p>}
        {pwSuccess && <p className="text-green-700 text-sm">Password changed.</p>}
        <button
          onClick={handleChangePassword}
          disabled={pwLoading}
          className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
        >
          {pwLoading ? 'Saving…' : 'Update Password'}
        </button>
      </div>

      {/* API Keys */}
      {currentUser?.can_generate_api_keys && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900">API Keys</h3>
            <p className="text-xs text-gray-500 mt-1">Keys authenticate API requests without a session. Shown once on creation.</p>
          </div>

          {newKey?.key && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 space-y-2">
              <p className="text-xs font-semibold text-amber-800">Copy this key now — it will not be shown again.</p>
              <code className="block text-xs bg-amber-100 rounded px-3 py-2 font-mono break-all text-amber-900 select-all">
                {newKey.key}
              </code>
              <button onClick={() => setNewKey(null)} className="text-xs text-amber-700 hover:underline">Dismiss</button>
            </div>
          )}

          {/* Generate form */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Key name</label>
              <input
                type="text"
                value={keyForm.name}
                onChange={e => setKeyForm(f => ({ ...f, name: e.target.value }))}
                placeholder="e.g. CI pipeline"
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Expires</label>
              <select
                value={keyForm.expires_in_days}
                onChange={e => setKeyForm(f => ({ ...f, expires_in_days: Number(e.target.value) }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
              >
                {EXPIRY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          </div>
          <button
            onClick={() => createMut.mutate()}
            disabled={createMut.isPending || !keyForm.name}
            className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
          >
            {createMut.isPending ? 'Generating…' : 'Generate Key'}
          </button>

          {/* Key list */}
          {apiKeys && apiKeys.length > 0 && (
            <div className="border border-gray-100 rounded-lg overflow-hidden">
              <table className="w-full text-xs">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left px-3 py-2 font-semibold text-gray-600">Name</th>
                    <th className="text-left px-3 py-2 font-semibold text-gray-600">Prefix</th>
                    <th className="text-left px-3 py-2 font-semibold text-gray-600">Expires</th>
                    <th className="text-left px-3 py-2 font-semibold text-gray-600">Last used</th>
                    <th className="px-3 py-2" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {apiKeys.map(k => (
                    <tr key={k.id} className={!k.is_active || isExpired(k.expires_at) ? 'opacity-40' : ''}>
                      <td className="px-3 py-2 font-medium text-gray-800">{k.name}</td>
                      <td className="px-3 py-2 font-mono text-gray-500">sk_{k.key_prefix}…</td>
                      <td className="px-3 py-2 text-gray-500">{formatDate(k.expires_at)}</td>
                      <td className="px-3 py-2 text-gray-400">{k.last_used_at ? formatDate(k.last_used_at) : '—'}</td>
                      <td className="px-3 py-2 text-right">
                        {k.is_active && !isExpired(k.expires_at) && (
                          <button
                            onClick={() => revokeMut.mutate(k.id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            Revoke
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
