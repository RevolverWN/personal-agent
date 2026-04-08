import { useState } from 'react'
import { WrenchIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline'

interface ToolCall {
  tool: string
  arguments: Record<string, any>
  result: {
    success: boolean
    data: any
    error?: string
  }
}

interface ToolCallDisplayProps {
  toolCalls: ToolCall[]
}

export default function ToolCallDisplay({ toolCalls }: ToolCallDisplayProps) {
  const [expandedTool, setExpandedTool] = useState<string | null>(null)

  if (!toolCalls || toolCalls.length === 0) return null

  return (
    <div className="mt-4 space-y-2">
      <p className="text-xs text-gray-500 flex items-center">
        <WrenchIcon className="w-3 h-3 mr-1" />
        Used {toolCalls.length} tool{toolCalls.length > 1 ? 's' : ''}
      </p>
      
      {toolCalls.map((toolCall, index) => (
        <div
          key={index}
          className={`border rounded-lg overflow-hidden ${
            toolCall.result.success
              ? 'border-green-200 bg-green-50'
              : 'border-red-200 bg-red-50'
          }`}
        >
          <button
            onClick={() => setExpandedTool(
              expandedTool === `${index}` ? null : `${index}`
            )}
            className="w-full px-3 py-2 flex items-center justify-between text-left"
          >
            <div className="flex items-center space-x-2">
              <WrenchIcon className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-900">
                {toolCall.tool}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  toolCall.result.success
                    ? 'bg-green-200 text-green-800'
                    : 'bg-red-200 text-red-800'
                }`}
              >
                {toolCall.result.success ? 'Success' : 'Failed'}
              </span>
            </div>
            {expandedTool === `${index}` ? (
              <ChevronUpIcon className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDownIcon className="w-4 h-4 text-gray-500" />
            )}
          </button>
          
          {expandedTool === `${index}` && (
            <div className="px-3 pb-3 border-t border-gray-200">
              {/* Arguments */}
              <div className="mt-2">
                <p className="text-xs font-medium text-gray-600 mb-1">Arguments:</p>
                <pre className="text-xs bg-white p-2 rounded border border-gray-200 overflow-x-auto">
                  {JSON.stringify(toolCall.arguments, null, 2)}
                </pre>
              </div>
              
              {/* Result */}
              <div className="mt-2">
                <p className="text-xs font-medium text-gray-600 mb-1">Result:</p>
                {toolCall.result.error ? (
                  <p className="text-xs text-red-600 bg-white p-2 rounded border border-red-200">
                    {toolCall.result.error}
                  </p>
                ) : (
                  <pre className="text-xs bg-white p-2 rounded border border-gray-200 overflow-x-auto max-h-40">
                    {JSON.stringify(toolCall.result.data, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
