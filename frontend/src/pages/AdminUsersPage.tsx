import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listUsers, createUser, updateUser } from '../api/users'
import type { Role, UserCreate } from '../types'

const ROLES: Role[] = ['admin', 'analyst', 'viewer']

export default function AdminUsersPage() {
  const qc = useQueryClient()
  const { data: users, isLoading } = useQuery({ queryKey: ['users'], queryFn: listUsers })

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<UserCreate>({ email: '', full_name: '', password: '', role: 'analyst' })
  const [formError, setFormError] = useState<string | null>(null)

  const createMut = useMutation({
    mutationFn: createUser,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); setShowForm(false); setForm({ email: '', full_name: '', password: '', role: 'analyst' }) },
    onError: () => setFormError('Failed to create user.'),
  })

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) => updateUser(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })

  if (isLoading) return <div className="text-gray-400 text-sm">Loading…</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Users</h2>
        <button
          onClick={() => setShowForm(s => !s)}
          className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800"
        >
          {showForm ? 'Cancel' : 'Add User'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <h3 className="font-semibold text-gray-900">New User</h3>
          {formError && <p className="text-red-600 text-sm">{formError}</p>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input type="text" value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input type="password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value as Role }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
          <button
            onClick={() => { setFormError(null); createMut.mutate(form) }}
            disabled={createMut.isPending}
            className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
          >
            {createMut.isPending ? 'Creating…' : 'Create User'}
          </button>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Name</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Email</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Role</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {(users ?? []).map(u => (
              <tr key={u.id} className={!u.is_active ? 'opacity-50' : ''}>
                <td className="px-4 py-3 font-medium text-gray-900">{u.full_name}</td>
                <td className="px-4 py-3 text-gray-600">{u.email}</td>
                <td className="px-4 py-3 capitalize text-gray-600">{u.role}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium ${u.is_active ? 'text-green-700' : 'text-red-600'}`}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => toggleActive.mutate({ id: u.id, is_active: !u.is_active })}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    {u.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
