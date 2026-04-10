import { useState, useEffect } from 'react'
import { api } from '../services/api'
import {
  PlusIcon,
  PlayIcon,
  TrashIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'

interface Task {
  id: string
  name: string
  enabled: boolean
  schedule: {
    kind: 'at' | 'every' | 'cron'
    at_ms?: number
    every_ms?: number
    expr?: string
    tz?: string
  }
  payload: { kind: string; message?: string }
  state: {
    next_run_at_ms?: number
    last_run_at_ms?: number
    last_status?: 'success' | 'failed'
    run_count: number
  }
}

const SCHEDULE_KINDS = [
  { value: 'at', label: 'One-time (at)' },
  { value: 'every', label: 'Interval (every)' },
  { value: 'cron', label: 'Cron expression' },
]

function formatNextRun(task: Task): string {
  if (!task.state.next_run_at_ms) return 'N/A'
  const d = new Date(task.state.next_run_at_ms)
  return d.toLocaleString()
}

function formatInterval(ms: number): string {
  if (ms < 60000) return `${ms / 1000}s`
  if (ms < 3600000) return `${ms / 60000}min`
  return `${ms / 3600000}h`
}

export default function Scheduler() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({
    name: '',
    kind: 'every' as 'at' | 'every' | 'cron',
    interval_ms: '300000',
    at_ms: '',
    cron_expr: '0 9 * * *',
    payload_message: '',
  })
  const [creating, setCreating] = useState(false)
  const [runningId, setRunningId] = useState<string | null>(null)

  useEffect(() => {
    loadTasks()
  }, [])

  const loadTasks = async () => {
    setIsLoading(true)
    try {
      const res = await api.get('/scheduler/tasks')
      setTasks(res.data)
    } catch {
      console.error('Failed to load tasks')
    } finally {
      setIsLoading(false)
    }
  }

  const createTask = async () => {
    if (!form.name.trim()) return
    setCreating(true)
    try {
      let schedule: object
      if (form.kind === 'at') {
        schedule = { kind: 'at', at_ms: parseInt(form.at_ms) }
      } else if (form.kind === 'every') {
        schedule = { kind: 'every', every_ms: parseInt(form.interval_ms) }
      } else {
        schedule = { kind: 'cron', expr: form.cron_expr }
      }
      await api.post('/scheduler/tasks', {
        name: form.name,
        schedule,
        payload: { kind: 'message', message: form.payload_message },
        enabled: true,
      })
      setShowCreate(false)
      setForm({ name: '', kind: 'every', interval_ms: '300000', at_ms: '', cron_expr: '0 9 * * *', payload_message: '' })
      loadTasks()
    } catch {
      console.error('Failed to create task')
    } finally {
      setCreating(false)
    }
  }

  const deleteTask = async (id: string) => {
    try {
      await api.delete(`/scheduler/tasks/${id}`)
      setTasks(prev => prev.filter(t => t.id !== id))
    } catch {
      console.error('Failed to delete task')
    }
  }

  const runTask = async (id: string) => {
    setRunningId(id)
    try {
      await api.post(`/scheduler/tasks/${id}/run`)
    } catch {
      console.error('Failed to run task')
    } finally {
      setRunningId(null)
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Scheduler</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <PlusIcon className="w-5 h-5" />
          New Task
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          No scheduled tasks yet. Click "New Task" to create one.
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map(task => (
            <div key={task.id} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-semibold text-gray-900">{task.name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${task.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {task.enabled ? 'Active' : 'Disabled'}
                    </span>
                    <span className="text-xs text-gray-400">
                      {task.schedule.kind === 'every'
                        ? `every ${formatInterval(task.schedule.every_ms || 0)}`
                        : task.schedule.kind === 'cron'
                        ? `cron: ${task.schedule.expr}`
                        : `at: ${task.state.next_run_at_ms ? new Date(task.state.next_run_at_ms).toLocaleString() : 'past'}`}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <ClockIcon className="w-4 h-4" />
                      Next: {formatNextRun(task)}
                    </span>
                    <span>Runs: {task.state.run_count}</span>
                    {task.state.last_run_at_ms && (
                      <span>
                        Last: {task.state.last_status === 'success' ? (
                          <CheckCircleIcon className="w-4 h-4 inline text-green-500 ml-1" />
                        ) : (
                          <XCircleIcon className="w-4 h-4 inline text-red-500 ml-1" />
                        )}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => runTask(task.id)}
                    disabled={runningId === task.id}
                    className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg disabled:opacity-50"
                    title="Run now"
                  >
                    <PlayIcon className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => deleteTask(task.id)}
                    className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    title="Delete"
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
            <h2 className="text-lg font-semibold mb-4">New Scheduled Task</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Task Name</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                  placeholder="Daily weather reminder"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Schedule Type</label>
                <select
                  value={form.kind}
                  onChange={e => setForm(f => ({ ...f, kind: e.target.value as any }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  {SCHEDULE_KINDS.map(k => (
                    <option key={k.value} value={k.value}>{k.label}</option>
                  ))}
                </select>
              </div>
              {form.kind === 'every' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Interval (ms)</label>
                  <input
                    type="number"
                    value={form.interval_ms}
                    onChange={e => setForm(f => ({ ...f, interval_ms: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder="300000"
                  />
                  <p className="text-xs text-gray-400 mt-1">e.g. 300000 = 5 minutes</p>
                </div>
              )}
              {form.kind === 'cron' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cron Expression</label>
                  <input
                    type="text"
                    value={form.cron_expr}
                    onChange={e => setForm(f => ({ ...f, cron_expr: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder="0 9 * * *"
                  />
                </div>
              )}
              {form.kind === 'at' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Timestamp (ms)</label>
                  <input
                    type="number"
                    value={form.at_ms}
                    onChange={e => setForm(f => ({ ...f, at_ms: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder="1775800000000"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payload Message</label>
                <textarea
                  value={form.payload_message}
                  onChange={e => setForm(f => ({ ...f, payload_message: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  rows={2}
                  placeholder="Message to send when triggered"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={createTask}
                disabled={creating || !form.name.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {creating ? 'Creating...' : 'Create Task'}
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
