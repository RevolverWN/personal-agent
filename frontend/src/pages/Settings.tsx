import { useState, useEffect } from 'react'
import { api } from '../services/api'

interface AgentConfig {
  model: string
  temperature: number
  max_tokens: number
  system_prompt: string | null
  enable_tools: string[]
  enable_memory: boolean
}

interface ModelInfo {
  id: string
  name: string
  provider: string
  description: string
}

export default function Settings() {
  const [config, setConfig] = useState<AgentConfig | null>(null)
  const [models, setModels] = useState<ModelInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const [configRes, modelsRes] = await Promise.all([
        api.get('/agent/config'),
        api.get('/models'),
      ])
      setConfig(configRes.data.config)
      setModels(modelsRes.data.models)
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    if (!config) return
    
    setIsSaving(true)
    setMessage('')
    
    try {
      await api.put('/agent/config', config)
      setMessage('Settings saved successfully')
    } catch (error) {
      setMessage('Failed to save settings')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading settings...</div>
      </div>
    )
  }

  if (!config) {
    return (
      <div className="text-center text-red-600">
        Failed to load settings
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

      {message && (
        <div className={`p-4 rounded-lg mb-6 ${message.includes('success') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {message}
        </div>
      )}

      <div className="space-y-6">
        {/* Model Selection */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">AI Model</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Model
              </label>
              <select
                value={config.model}
                onChange={(e) => setConfig({ ...config, model: e.target.value })}
                className="input-field"
              >
                {models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} - {model.description}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Generation Settings */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Generation Settings</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature: {config.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={config.temperature}
                onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                className="w-full"
              />
              <p className="text-sm text-gray-500 mt-1">
                Lower values make responses more focused and deterministic
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Tokens: {config.max_tokens}
              </label>
              <input
                type="range"
                min="256"
                max="128000"
                step="256"
                value={config.max_tokens}
                onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* System Prompt */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">System Prompt</h2>
          <textarea
            value={config.system_prompt || ''}
            onChange={(e) => setConfig({ ...config, system_prompt: e.target.value || null })}
            placeholder="Enter a system prompt to customize the AI's behavior..."
            rows={4}
            className="input-field"
          />
          <p className="text-sm text-gray-500 mt-2">
            This prompt sets the AI's personality and behavior for all conversations
          </p>
        </div>

        {/* Features */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Features</h2>
          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={config.enable_memory}
                onChange={(e) => setConfig({ ...config, enable_memory: e.target.checked })}
                className="w-4 h-4 text-primary-600 rounded"
              />
              <span className="text-gray-700">Enable long-term memory</span>
            </label>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn-primary px-8 py-3"
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
