import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid'

export default function StatCard({ title, value, change, changeType, icon: Icon, color = 'blue' }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
          {change !== undefined && (
            <div className="mt-2 flex items-center text-sm">
              {changeType === 'increase' ? (
                <ArrowUpIcon className="h-4 w-4 text-green-500" />
              ) : changeType === 'decrease' ? (
                <ArrowDownIcon className="h-4 w-4 text-red-500" />
              ) : null}
              <span
                className={`ml-1 ${
                  changeType === 'increase'
                    ? 'text-green-600'
                    : changeType === 'decrease'
                    ? 'text-red-600'
                    : 'text-gray-500'
                }`}
              >
                {change}%
              </span>
              <span className="ml-1 text-gray-500">vs last month</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className={`rounded-lg p-3 ${colorClasses[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
        )}
      </div>
    </div>
  )
}
