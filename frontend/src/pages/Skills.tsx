import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { BoltIcon, PlayIcon } from '@heroicons/react/24/outline'

interface Skill {
  name: string
  description: string
  icon: string
  category: string
  actions_count: number
}

export default function Skills() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)
  const [actionResult, setActionResult] = useState<any>(null)

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

  const executeAction = async (skillName: string, action: string, params: any) => {
    try {
      const response = await api.post(`/skills/${skillName}/execute`, null, {
        params: { action, params: JSON.stringify(params) }
      })
      setActionResult(response.data)
    } catch (error) {
      console.error('Action failed:', error)
    }
  }

  if (isLoading) {
    return <div className="text-center py-12">Loading skills...</div>
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Skills</h1>
          <p className="text-gray-600 mt-1">Extensible capabilities for your AI assistant</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {skills.map((skill) => (
          <div
            key={skill.name}
            className="card hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => setSelectedSkill(skill)}
          >
            <div className="text-4xl mb-3">{skill.icon}</div>
            <h3 className="font-semibold capitalize">{skill.name}</h3>
            <p className="text-sm text-gray-600 mt-1">{skill.description}</p>
            <div className="flex items-center mt-3 text-xs text-gray-500">
              <span className="px-2 py-1 bg-gray-100 rounded">{skill.category}</span>
              <span className="ml-2">{skill.actions_count} actions</span>
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

      {/* Skill Detail Modal */}
      {selectedSkill && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg">
            <div className="flex items-center mb-4">
              <span className="text-3xl mr-3">{selectedSkill.icon}</span>
              <div>
                <h2 className="text-xl font-bold capitalize">{selectedSkill.name}</h2>
                <p className="text-sm text-gray-600">{selectedSkill.description}</p>
              </div>
            </div>
            
            <div className="border-t pt-4">
              <p className="text-sm text-gray-500 mb-3">
                This skill will be automatically used by the AI when relevant.
              </p>
              
              {actionResult && (
                <div className="mt-4 p-3 bg-gray-50 rounded">
                  <p className="text-sm font-medium">Last Result:</p>
                  <pre className="text-xs mt-1 overflow-x-auto">
                    {JSON.stringify(actionResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setSelectedSkill(null)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
