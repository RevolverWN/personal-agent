import { useState, useEffect, useMemo } from 'react'
import { api } from '../services/api'
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  CpuChipIcon,
  CalendarDaysIcon,
} from '@heroicons/react/24/outline'

interface UsageByModel {
  model: string
  provider: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  call_count: number
  cost: number
}

interface UsageByDate {
  date: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  call_count: number
  cost: number
}

interface UsageSummary {
  total_prompt_tokens: number
  total_completion_tokens: number
  total_tokens: number
  total_calls: number
  total_cost: number
  by_model: UsageByModel[]
  by_date: UsageByDate[]
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return n.toLocaleString()
}

function formatCost(n: number): string {
  if (n >= 1) return '$' + n.toFixed(2)
  if (n >= 0.01) return '$' + n.toFixed(3)
  return '$' + n.toFixed(6)
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ElementType
  label: string
  value: string
  sub?: string
  color: string
}) {
  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: color + '15', color }}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
          {sub && <p className="text-xs text-gray-400">{sub}</p>}
        </div>
      </div>
    </div>
  )
}

export default function TokenUsage() {
  const [summary, setSummary] = useState<UsageSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadSummary()
  }, [])

  const loadSummary = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const res = await api.get('/token-usage/summary')
      setSummary(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load token usage')
    } finally {
      setIsLoading(false)
    }
  }

  // Compute max values for bar charts
  const maxModelTokens = useMemo(() => {
    if (!summary) return 1
    return Math.max(...summary.by_model.map((m) => m.total_tokens), 1)
  }, [summary])

  const maxDailyTokens = useMemo(() => {
    if (!summary) return 1
    return Math.max(...summary.by_date.map((d) => d.total_tokens), 1)
  }, [summary])

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">Loading token usage...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="card text-center py-12">
          <p className="text-red-500 mb-4">{error}</p>
          <button onClick={loadSummary} className="btn-primary">
            Retry
          </button>
        </div>
      </div>
    )
  }

  const hasData = summary && summary.total_calls > 0

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Token Usage</h1>
        <p className="text-gray-600 mt-1">Track your LLM token consumption and costs</p>
      </div>

      {!hasData ? (
        <div className="card text-center py-16">
          <ChartBarIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h2 className="text-xl font-semibold text-gray-700">No usage data yet</h2>
          <p className="text-gray-500 mt-2">
            Start chatting with your agent to see token usage statistics here.
          </p>
        </div>
      ) : (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              icon={ChartBarIcon}
              label="Total Tokens"
              value={formatNumber(summary.total_tokens)}
              sub={`${formatNumber(summary.total_prompt_tokens)} prompt / ${formatNumber(summary.total_completion_tokens)} completion`}
              color="#3B82F6"
            />
            <StatCard
              icon={CalendarDaysIcon}
              label="Total Calls"
              value={summary.total_calls.toLocaleString()}
              color="#8B5CF6"
            />
            <StatCard
              icon={CurrencyDollarIcon}
              label="Total Cost"
              value={formatCost(summary.total_cost)}
              color="#10B981"
            />
            <StatCard
              icon={CpuChipIcon}
              label="Models Used"
              value={summary.by_model.length.toString()}
              color="#F59E0B"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Daily Trend */}
            <div className="card">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <CalendarDaysIcon className="w-5 h-5 text-gray-400" />
                Daily Token Usage
              </h2>
              {summary.by_date.length === 0 ? (
                <p className="text-gray-400 text-center py-8">No daily data</p>
              ) : (
                <div className="space-y-2">
                  {summary.by_date.map((d) => (
                    <div key={d.date} className="flex items-center gap-3">
                      <span className="text-xs text-gray-500 w-20 shrink-0 font-mono">
                        {d.date.slice(5)}
                      </span>
                      <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden relative">
                        <div
                          className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.max((d.total_tokens / maxDailyTokens) * 100, 2)}%`,
                          }}
                        />
                        <span className="absolute inset-0 flex items-center justify-end pr-2 text-xs font-medium text-gray-700">
                          {formatNumber(d.total_tokens)}
                        </span>
                      </div>
                      <span className="text-xs text-gray-400 w-16 text-right shrink-0">
                        {d.call_count} calls
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Model Distribution */}
            <div className="card">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <CpuChipIcon className="w-5 h-5 text-gray-400" />
                Usage by Model
              </h2>
              {summary.by_model.length === 0 ? (
                <p className="text-gray-400 text-center py-8">No model data</p>
              ) : (
                <div className="space-y-3">
                  {summary.by_model.map((m) => (
                    <div key={m.model}>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-800">{m.model}</span>
                          <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
                            {m.provider}
                          </span>
                        </div>
                        <span className="text-sm font-semibold text-gray-700">
                          {formatNumber(m.total_tokens)}
                        </span>
                      </div>
                      <div className="bg-gray-100 rounded-full h-3 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-violet-400 to-violet-600 rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.max((m.total_tokens / maxModelTokens) * 100, 2)}%`,
                          }}
                        />
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-400">
                          {m.call_count} calls · {formatNumber(m.prompt_tokens)} in / {formatNumber(m.completion_tokens)} out
                        </span>
                        <span className="text-xs font-medium text-green-600">
                          {formatCost(m.cost)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Cost Breakdown */}
          <div className="card mt-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <CurrencyDollarIcon className="w-5 h-5 text-gray-400" />
              Cost Breakdown
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b border-gray-200">
                    <th className="pb-2 font-medium">Model</th>
                    <th className="pb-2 font-medium text-right">Calls</th>
                    <th className="pb-2 font-medium text-right">Input Tokens</th>
                    <th className="pb-2 font-medium text-right">Output Tokens</th>
                    <th className="pb-2 font-medium text-right">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.by_model.map((m) => (
                    <tr key={m.model} className="border-b border-gray-100">
                      <td className="py-2.5 font-medium text-gray-800">{m.model}</td>
                      <td className="py-2.5 text-right text-gray-600">{m.call_count}</td>
                      <td className="py-2.5 text-right text-gray-600">{formatNumber(m.prompt_tokens)}</td>
                      <td className="py-2.5 text-right text-gray-600">{formatNumber(m.completion_tokens)}</td>
                      <td className="py-2.5 text-right font-medium text-green-600">{formatCost(m.cost)}</td>
                    </tr>
                  ))}
                  <tr className="font-semibold">
                    <td className="pt-3 text-gray-900">Total</td>
                    <td className="pt-3 text-right text-gray-900">{summary.total_calls}</td>
                    <td className="pt-3 text-right text-gray-900">{formatNumber(summary.total_prompt_tokens)}</td>
                    <td className="pt-3 text-right text-gray-900">{formatNumber(summary.total_completion_tokens)}</td>
                    <td className="pt-3 text-right text-green-600">{formatCost(summary.total_cost)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
