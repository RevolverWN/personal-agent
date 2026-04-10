import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { format } from 'date-fns'
import {
  PlusIcon,
  TrashIcon,
  UsersIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'

interface AgentRole {
  id: string
  name: string
  description: string
  icon: string
  color: string
  tools: string[]
}

interface AgentInstance {
  id: string
  name: string
  description: string
  icon: string
  color: string
  model: string
  temperature: number
  usage_count: number
  is_active: boolean
  created_at: string
  role_id?: string
}

const MODEL_OPTIONS = [
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
  { value: 'deepseek-chat', label: 'DeepSeek Chat' },
  { value: 'moonshot-v1-8k', label: 'Moonshot Kimi' },
]

export default function Agents() {
  const [builtinRoles, setBuiltinRoles] = useState<AgentRole[]>([])
  const [agents, setAgents] = useState<AgentInstance[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showCollaborateModal, setShowCollaborateModal] = useState(false)
  const [,] = useState<AgentRole | null>(null)
  const [newAgent, setNewAgent] = useState({
    name: '',
    description: '',
    system_prompt: '',
    model: 'gpt-4o-mini',
    temperature: 0.7,
  })
  const [collaboration, setCollaboration] = useState({
    message: '',
    agentIds: [] as string[],
    mode: 'parallel' as 'sequential' | 'parallel' | 'debate',
  })
  const [collaborationResult, setCollaborationResult] = useState<any>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [rolesRes, agentsRes] = await Promise.all([
        api.get('/agents/roles'),
        api.get('/agents'),
      ])
      setBuiltinRoles(rolesRes.data)
      setAgents(agentsRes.data)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateFromRole = async (role: AgentRole) => {
    try {
      const response = await api.post(`/agents/from-role/${role.id}`, null, {
        params: { custom_name: `${role.name} (Custom)` }
      })
      setAgents([...agents, response.data])
    } catch (error) {
      console.error('Failed to create agent:', error)
    }
  }

  const handleCreateCustom = async () => {
    try {
      const response = await api.post('/agents', {
        name: newAgent.name,
        description: newAgent.description,
        system_prompt: newAgent.system_prompt,
        model: newAgent.model,
        temperature: newAgent.temperature,
      })
      setAgents([...agents, response.data])
      setShowCreateModal(false)
      setNewAgent({
        name: '',
        description: '',
        system_prompt: '',
        model: 'gpt-4o-mini',
        temperature: 0.7,
      })
    } catch (error) {
      console.error('Failed to create agent:', error)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return

    try {
      await api.delete(`/agents/${id}`)
      setAgents(agents.filter(a => a.id !== id))
    } catch (error) {
      console.error('Failed to delete agent:', error)
    }
  }

  const handleCollaborate = async () => {
    if (collaboration.agentIds.length < 2) {
      alert('Please select at least 2 agents')
      return
    }

    try {
      const response = await api.post('/agents/collaborate', {
        message: collaboration.message,
        agent_ids: collaboration.agentIds,
        mode: collaboration.mode,
      })
      setCollaborationResult(response.data)
    } catch (error) {
      console.error('Collaboration failed:', error)
    }
  }

  if (isLoading) {
    return <div className="text-center py-12">Loading...</div>
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Agents</h1>
          <p className="text-gray-600 mt-1">Create and manage specialized AI agents</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCollaborateModal(true)}
            className="btn-secondary flex items-center"
          >
            <UsersIcon className="w-5 h-5 mr-2" />
            Multi-Agent
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center"
          >
            <PlusIcon className="w-5 h-5 mr-2" />
            Create Agent
          </button>
        </div>
      </div>

      {/* Built-in Roles */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <SparklesIcon className="w-5 h-5 mr-2" />
          Built-in Roles
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {builtinRoles.map((role) => (
            <div
              key={role.id}
              className="card hover:shadow-lg transition-shadow cursor-pointer group"
              onClick={() => handleCreateFromRole(role)}
            >
              <div className="flex items-start justify-between">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                  style={{ backgroundColor: role.color + '20' }}
                >
                  {role.icon}
                </div>
                <span
                  className="text-xs px-2 py-1 rounded-full"
                  style={{ backgroundColor: role.color + '20', color: role.color }}
                >
                  {role.tools.length} tools
                </span>
              </div>
              <h3 className="font-semibold mt-3">{role.name}</h3>
              <p className="text-sm text-gray-600 mt-1">{role.description}</p>
              <button className="text-sm text-primary-600 mt-3 group-hover:underline">
                Use this role →
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* My Agents */}
      <div>
        <h2 className="text-xl font-semibold mb-4">My Agents</h2>
        {agents.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-500">No custom agents yet</p>
            <p className="text-sm text-gray-400 mt-1">
              Create an agent from a built-in role or build your own
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {agents.map((agent) => (
              <div key={agent.id} className="card flex items-center justify-between">
                <div className="flex items-center">
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl mr-4"
                    style={{ backgroundColor: agent.color + '20' }}
                  >
                    {agent.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold">{agent.name}</h3>
                    <p className="text-sm text-gray-600">{agent.description}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                      <span>{agent.model}</span>
                      <span>•</span>
                      <span>Used {agent.usage_count} times</span>
                      <span>•</span>
                      <span>Created {format(new Date(agent.created_at), 'MMM d')}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {!agent.role_id && (
                    <button
                      onClick={() => handleDelete(agent.id)}
                      className="text-gray-400 hover:text-red-600 p-2"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Create Custom Agent</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={newAgent.name}
                  onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Code Reviewer"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input
                  type="text"
                  value={newAgent.description}
                  onChange={(e) => setNewAgent({ ...newAgent, description: e.target.value })}
                  className="input-field"
                  placeholder="What does this agent do?"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt</label>
                <textarea
                  value={newAgent.system_prompt}
                  onChange={(e) => setNewAgent({ ...newAgent, system_prompt: e.target.value })}
                  rows={4}
                  className="input-field"
                  placeholder="Instructions for the agent..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                <select
                  value={newAgent.model}
                  onChange={(e) => setNewAgent({ ...newAgent, model: e.target.value })}
                  className="input-field"
                >
                  {MODEL_OPTIONS.map((m) => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature: {newAgent.temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={newAgent.temperature}
                  onChange={(e) => setNewAgent({ ...newAgent, temperature: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setShowCreateModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleCreateCustom}
                disabled={!newAgent.name || !newAgent.system_prompt}
                className="btn-primary"
              >
                Create Agent
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Collaborate Modal */}
      {showCollaborateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Multi-Agent Collaboration</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Task</label>
                <textarea
                  value={collaboration.message}
                  onChange={(e) => setCollaboration({ ...collaboration, message: e.target.value })}
                  rows={3}
                  className="input-field"
                  placeholder="Describe the task or question..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mode</label>
                <select
                  value={collaboration.mode}
                  onChange={(e) => setCollaboration({ ...collaboration, mode: e.target.value as any })}
                  className="input-field"
                >
                  <option value="parallel">Parallel - All agents respond independently</option>
                  <option value="sequential">Sequential - Build on previous responses</option>
                  <option value="debate">Debate - Agents discuss and challenge each other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Select Agents</label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {agents.map((agent) => (
                    <label key={agent.id} className="flex items-center p-2 hover:bg-gray-50 rounded">
                      <input
                        type="checkbox"
                        checked={collaboration.agentIds.includes(agent.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setCollaboration({
                              ...collaboration,
                              agentIds: [...collaboration.agentIds, agent.id]
                            })
                          } else {
                            setCollaboration({
                              ...collaboration,
                              agentIds: collaboration.agentIds.filter(id => id !== agent.id)
                            })
                          }
                        }}
                        className="mr-3"
                      />
                      <span className="text-2xl mr-2">{agent.icon}</span>
                      <span>{agent.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {collaborationResult && (
              <div className="mt-6 border-t pt-4">
                <h3 className="font-semibold mb-3">Results</h3>
                {collaborationResult.responses.map((resp: any, idx: number) => (
                  <div key={idx} className="mb-4 p-3 bg-gray-50 rounded">
                    <p className="font-medium text-sm text-gray-700">{resp.agent_name}</p>
                    <p className="text-sm mt-1">{resp.response}</p>
                  </div>
                ))}
                {collaborationResult.synthesis && (
                  <div className="mt-4 p-3 bg-primary-50 rounded">
                    <p className="font-medium text-sm text-primary-700">Synthesis</p>
                    <p className="text-sm mt-1">{collaborationResult.synthesis}</p>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setShowCollaborateModal(false)} className="btn-secondary">
                Close
              </button>
              <button
                onClick={handleCollaborate}
                disabled={!collaboration.message || collaboration.agentIds.length < 2}
                className="btn-primary"
              >
                Start Collaboration
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
