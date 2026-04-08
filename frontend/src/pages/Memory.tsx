import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { format } from 'date-fns'
import {
  PlusIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  ChartBarIcon,
  TagIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'

interface Memory {
  id: string
  content: string
  category: string
  importance: number
  created_at: string
  access_count: number
}

interface MemoryStats {
  total_memories: number
  by_category: Record<string, number>
  recent_additions: number
}

const CATEGORIES = [
  { value: 'preference', label: 'Preference', color: 'bg-blue-100 text-blue-800' },
  { value: 'fact', label: 'Fact', color: 'bg-green-100 text-green-800' },
  { value: 'goal', label: 'Goal', color: 'bg-purple-100 text-purple-800' },
  { value: 'task', label: 'Task', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'general', label: 'General', color: 'bg-gray-100 text-gray-800' },
]

export default function Memory() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [stats, setStats] = useState<MemoryStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [newMemory, setNewMemory] = useState({
    content: '',
    category: 'general',
    importance: 3,
  })

  useEffect(() => {
    loadMemories()
    loadStats()
  }, [selectedCategory])

  const loadMemories = async () => {
    try {
      const params = new URLSearchParams()
      if (selectedCategory) params.append('category', selectedCategory)
      
      const response = await api.get(`/memory?${params}`)
      setMemories(response.data)
    } catch (error) {
      console.error('Failed to load memories:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await api.get('/memory/stats')
      setStats(response.data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadMemories()
      return
    }
    
    try {
      const response = await api.get(`/memory/search?query=${encodeURIComponent(searchQuery)}`)
      setMemories(response.data.memories)
    } catch (error) {
      console.error('Search failed:', error)
    }
  }

  const handleCreate = async () => {
    try {
      await api.post('/memory', newMemory)
      setShowAddModal(false)
      setNewMemory({ content: '', category: 'general', importance: 3 })
      loadMemories()
      loadStats()
    } catch (error) {
      console.error('Failed to create memory:', error)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this memory?')) return
    
    try {
      await api.delete(`/memory/${id}`)
      loadMemories()
      loadStats()
    } catch (error) {
      console.error('Failed to delete memory:', error)
    }
  }

  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to delete ALL memories? This cannot be undone.')) return
    
    try {
      await api.delete('/memory')
      loadMemories()
      loadStats()
    } catch (error) {
      console.error('Failed to clear memories:', error)
    }
  }

  const getCategoryStyle = (category: string) => {
    return CATEGORIES.find(c => c.value === category)?.color || 'bg-gray-100 text-gray-800'
  }

  const getCategoryLabel = (category: string) => {
    return CATEGORIES.find(c => c.value === category)?.label || category
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Memory</h1>
          <p className="text-gray-600 mt-1">Manage what your AI assistant remembers about you</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Add Memory
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="card">
            <div className="flex items-center">
              <ChartBarIcon className="w-8 h-8 text-primary-600" />
              <div className="ml-3">
                <p className="text-sm text-gray-600">Total Memories</p>
                <p className="text-2xl font-bold">{stats.total_memories}</p>
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center">
              <ClockIcon className="w-8 h-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm text-gray-600">This Week</p>
                <p className="text-2xl font-bold">{stats.recent_additions}</p>
              </div>
            </div>
          </div>
          
          {Object.entries(stats.by_category).slice(0, 2).map(([cat, count]) => (
            <div key={cat} className="card">
              <div className="flex items-center">
                <TagIcon className="w-8 h-8 text-purple-600" />
                <div className="ml-3">
                  <p className="text-sm text-gray-600">{getCategoryLabel(cat)}</p>
                  <p className="text-2xl font-bold">{count}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Search and Filter */}
      <div className="card mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[300px]">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search memories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
          
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map(cat => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
          
          <button onClick={handleSearch} className="btn-primary">
            Search
          </button>
        </div>
      </div>

      {/* Memories List */}
      {isLoading ? (
        <div className="text-center py-12">Loading memories...</div>
      ) : memories.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 mb-4">No memories found</p>
          <p className="text-sm text-gray-400">
            Memories are automatically extracted from conversations, or you can add them manually.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {memories.map((memory) => (
            <div key={memory.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryStyle(memory.category)}`}>
                      {getCategoryLabel(memory.category)}
                    </span>
                    <div className="flex items-center">
                      {[...Array(5)].map((_, i) => (
                        <div
                          key={i}
                          className={`w-2 h-2 rounded-full mr-1 ${
                            i < memory.importance ? 'bg-yellow-400' : 'bg-gray-200'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                  
                  <p className="text-gray-900 mb-2">{memory.content}</p>
                  
                  <div className="flex items-center text-sm text-gray-500 gap-4">
                    <span>Added {format(new Date(memory.created_at), 'MMM d, yyyy')}</span>
                    <span>Accessed {memory.access_count} times</span>
                  </div>
                </div>
                
                <button
                  onClick={() => handleDelete(memory.id)}
                  className="text-gray-400 hover:text-red-600 p-2"
                >
                  <TrashIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Clear All Button */}
      {memories.length > 0 && (
        <div className="mt-8 text-center">
          <button
            onClick={handleClearAll}
            className="text-red-600 hover:text-red-800 text-sm"
          >
            Clear All Memories
          </button>
        </div>
      )}

      {/* Add Memory Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg">
            <h2 className="text-xl font-bold mb-4">Add Memory</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Content
                </label>
                <textarea
                  value={newMemory.content}
                  onChange={(e) => setNewMemory({ ...newMemory, content: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  placeholder="Something to remember..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  value={newMemory.category}
                  onChange={(e) => setNewMemory({ ...newMemory, category: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  {CATEGORIES.map(cat => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Importance: {newMemory.importance}
                </label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={newMemory.importance}
                  onChange={(e) => setNewMemory({ ...newMemory, importance: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!newMemory.content.trim()}
                className="btn-primary"
              >
                Add Memory
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
