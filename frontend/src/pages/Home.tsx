import { useNavigate } from 'react-router-dom'
import { ChatBubbleLeftIcon, FolderIcon, Cog6ToothIcon } from '@heroicons/react/24/outline'

export default function Home() {
  const navigate = useNavigate()

  const features = [
    {
      title: 'Chat',
      description: 'Start a conversation with your AI assistant',
      icon: ChatBubbleLeftIcon,
      action: () => navigate('/chat'),
      color: 'bg-blue-500',
    },
    {
      title: 'Files',
      description: 'Manage your uploaded files',
      icon: FolderIcon,
      action: () => navigate('/files'),
      color: 'bg-green-500',
    },
    {
      title: 'Settings',
      description: 'Configure your agent preferences',
      icon: Cog6ToothIcon,
      action: () => navigate('/settings'),
      color: 'bg-purple-500',
    },
  ]

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to Personal Agent
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Your personal AI assistant powered by multiple LLM providers.
          Start chatting, manage files, and customize your experience.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {features.map((feature) => (
          <button
            key={feature.title}
            onClick={feature.action}
            className="card text-left hover:shadow-md transition-shadow group"
          >
            <div className={`${feature.color} w-12 h-12 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
              <feature.icon className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {feature.title}
            </h3>
            <p className="text-gray-600">{feature.description}</p>
          </button>
        ))}
      </div>

      <div className="mt-12 card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Quick Start
        </h2>
        <ol className="space-y-3 text-gray-600 list-decimal list-inside">
          <li>Click on <strong>Chat</strong> to start a new conversation</li>
          <li>Select your preferred AI model in the settings</li>
          <li>Upload files for the AI to analyze</li>
          <li>Customize your agent's behavior in Settings</li>
        </ol>
      </div>
    </div>
  )
}
