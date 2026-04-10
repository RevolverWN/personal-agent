import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { BoltIcon, XMarkIcon, PlayIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline'

interface SkillAction {
  name: string
  description: string
  parameters: {
    type: string
    properties: Record<string, {
      type: string
      description: string
      enum?: string[]
      default?: unknown
    }>
    required: string[]
  }
}

interface Skill {
  name: string
  description: string
  version: string
  icon: string
  category: string
  tags: string[]
  initialized: boolean
  actions_count: number
  actions?: SkillAction[]
}

export default function Skills() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)
  const [skillActions, setSkillActions] = useState<SkillAction[]>([])
  const [selectedAction, setSelectedAction] = useState<SkillAction | null>(null)
  const [params, setParams] = useState<Record<string, unknown>>({})
  const [executeResult, setExecuteResult] = useState<Record<string, unknown> | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null)

  useEffect(() => {
    loadSkills()
  }, [])

  const loadSkills = async () => {
    try {
      const response = await api.get('/skills')
      setSkills(response.data)
    } catch (error) {
      console.error('Failed to load skills:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadSkillActions = async (skillName: string) => {
    try {
      const response = await api.get(`/skills/${skillName}/actions`)
      return response.data.actions as SkillAction[]
    } catch (error) {
      console.error('Failed to load actions:', error)
      return []
    }
  }

  const handleSkillClick = async (skill: Skill) => {
    setSelectedSkill(skill)
    setExecuteResult(null)
    setSelectedAction(null)
    setParams({})
    
    // Load detailed info including actions
    try {
      const response = await api.get(`/skills/${skill.name}`)
      const actions = response.data.actions as SkillAction[]
      setSkillActions(actions)
      
      // Auto-select first action if available
      if (actions.length > 0) {
        setSelectedAction(actions[0])
        initDefaultParams(actions[0])
      }
    } catch (error) {
      console.error('Failed to load skill info:', error)
      setSkillActions([])
    }
  }

  const initDefaultParams = (action: SkillAction) => {
    const defaults: Record<string, unknown> = {}
    for (const [key, prop] of Object.entries(action.parameters.properties)) {
      if (prop.default !== undefined) {
        defaults[key] = prop.default
      }
    }
    setParams(defaults)
  }

  const handleActionChange = (action: SkillAction) => {
    setSelectedAction(action)
    initDefaultParams(action)
  }

  const handleParamChange = (key: string, value: unknown) => {
    setParams(prev => ({ ...prev, [key]: value }))
  }

  const executeAction = async () => {
    if (!selectedSkill || !selectedAction) return
    
    setIsExecuting(true)
    setExecuteResult(null)
    
    try {
      const response = await api.post(
        `/skills/${selectedSkill.name}/execute?action=${selectedAction.name}`,
        params
      )
      setExecuteResult(response.data)
    } catch (error: unknown) {
      const errorData = error as { response?: { data?: { detail?: string } } }
      setExecuteResult({
        success: false,
        error: errorData.response?.data?.detail || 'Execution failed'
      })
    } finally {
      setIsExecuting(false)
    }
  }

  const renderParamInput = (key: string, prop: SkillAction['parameters']['properties'][string]) => {
    const type = prop.type
    const value = params[key] ?? ''
    
    if (prop.enum) {
      return (
        <select
          value={String(value)}
          onChange={(e) => handleParamChange(key, e.target.value)}
          className="input-field"
        >
          {prop.enum.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      )
    }
    
    if (type === 'integer') {
      return (
        <input
          type="number"
          value={String(value)}
          onChange={(e) => handleParamChange(key, parseInt(e.target.value) || 0)}
          className="input-field"
          placeholder={prop.description}
        />
      )
    }
    
    if (type === 'string' && prop.description.toLowerCase().includes('text')) {
      return (
        <textarea
          value={String(value)}
          onChange={(e) => handleParamChange(key, e.target.value)}
          className="input-field min-h-[100px]"
          placeholder={prop.description}
        />
      )
    }
    
    return (
      <input
        type="text"
        value={String(value)}
        onChange={(e) => handleParamChange(key, e.target.value)}
        className="input-field"
        placeholder={prop.description}
      />
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading skills...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Skills</h1>
          <p className="text-gray-600 mt-1">Extensible capabilities for your AI assistant</p>
        </div>
        <div className="text-sm text-gray-500">
          {skills.length} skills available
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {skills.map((skill) => (
          <div key={skill.name} className="relative">
            <div
              className={`card hover:shadow-lg transition-all cursor-pointer ${
                selectedSkill?.name === skill.name ? 'ring-2 ring-primary-500' : ''
              }`}
              onClick={() => handleSkillClick(skill)}
            >
              <div className="flex items-start justify-between">
                <div className="text-4xl mb-3">{skill.icon}</div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setExpandedSkill(expandedSkill === skill.name ? null : skill.name)
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  {expandedSkill === skill.name ? (
                    <ChevronUpIcon className="w-5 h-5" />
                  ) : (
                    <ChevronDownIcon className="w-5 h-5" />
                  )}
                </button>
              </div>
              <h3 className="font-semibold capitalize">{skill.name}</h3>
              <p className="text-sm text-gray-600 mt-1 line-clamp-2">{skill.description}</p>
              <div className="flex items-center gap-2 mt-3 text-xs text-gray-500">
                <span className="px-2 py-1 bg-gray-100 rounded">{skill.category}</span>
                <span>{skill.actions_count} actions</span>
                {skill.initialized && (
                  <span className="text-green-600">● Ready</span>
                )}
              </div>
              
              {expandedSkill === skill.name && (
                <div className="mt-4 pt-4 border-t text-sm">
                  <p className="text-gray-600 mb-2">Tags: {skill.tags.join(', ')}</p>
                  <p className="text-gray-500">Version: {skill.version}</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {skills.length === 0 && (
        <div className="card text-center py-12">
          <BoltIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No skills available</p>
        </div>
      )}

      {/* Skill Execution Modal */}
      {selectedSkill && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-6 border-b">
              <div className="flex items-center">
                <span className="text-3xl mr-3">{selectedSkill.icon}</span>
                <div>
                  <h2 className="text-xl font-bold capitalize">{selectedSkill.name}</h2>
                  <p className="text-sm text-gray-600">{selectedSkill.description}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedSkill(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6">
              {skillActions.length > 0 && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Action
                  </label>
                  <select
                    value={selectedAction?.name || ''}
                    onChange={(e) => {
                      const action = skillActions.find(a => a.name === e.target.value)
                      if (action) handleActionChange(action)
                    }}
                    className="input-field"
                  >
                    {skillActions.map((action) => (
                      <option key={action.name} value={action.name}>
                        {action.name} - {action.description}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {selectedAction && (
                <div className="space-y-4">
                  <h3 className="font-medium text-gray-900">Parameters</h3>
                  
                  {Object.entries(selectedAction.parameters.properties).map(([key, prop]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {key}
                        {selectedAction.parameters.required.includes(key) && (
                          <span className="text-red-500 ml-1">*</span>
                        )}
                      </label>
                      <p className="text-xs text-gray-500 mb-1">{prop.description}</p>
                      {renderParamInput(key, prop)}
                    </div>
                  ))}
                </div>
              )}

              {executeResult && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Result</h3>
                  <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(executeResult, null, 2)}
                  </pre>
                  {executeResult.message && (
                    <div className="mt-3 p-3 bg-blue-50 rounded text-sm text-blue-800 whitespace-pre-wrap">
                      {String(executeResult.message)}
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex justify-end gap-3 p-6 border-t bg-gray-50">
              <button
                onClick={() => setSelectedSkill(null)}
                className="btn-secondary"
              >
                Close
              </button>
              {selectedAction && (
                <button
                  onClick={executeAction}
                  disabled={isExecuting}
                  className="btn-primary flex items-center gap-2"
                >
                  {isExecuting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Executing...
                    </>
                  ) : (
                    <>
                      <PlayIcon className="w-4 h-4" />
                      Execute
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
