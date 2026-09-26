import { useState, useEffect } from 'react'
import {
  CurrencyDollarIcon,
  TruckIcon,
  MapPinIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import StatCard from '../components/StatCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { analyticsApi } from '../services/api'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState(null)
  const [marketData, setMarketData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      // For demo, use mock data since backend might not be running
      const mockDashboard = {
        latest_rates: {
          handysize: 12.5,
          supramax: 15.8,
          panamax: 18.2,
          capesize: 22.5,
        },
        rate_changes_30d: {
          handysize: 3.2,
          supramax: -1.5,
          panamax: 2.8,
          capesize: 5.1,
        },
        congested_ports_count: 3,
        active_routes_count: 16,
      }

      const mockMarket = {
        vessel_type_data: {
          handysize: { current_rate: 12.5, avg_rate: 12.1, volatility: 8.5 },
          supramax: { current_rate: 15.8, avg_rate: 16.2, volatility: 10.2 },
          panamax: { current_rate: 18.2, avg_rate: 17.5, volatility: 12.1 },
          capesize: { current_rate: 22.5, avg_rate: 21.0, volatility: 15.3 },
        },
        market_sentiment: 'bullish',
      }

      setDashboardData(mockDashboard)
      setMarketData(mockMarket)
    } catch (err) {
      setError('Failed to load dashboard data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <button onClick={fetchDashboardData} className="btn-primary mt-4">
          Retry
        </button>
      </div>
    )
  }

  const rateChartData = dashboardData
    ? Object.entries(dashboardData.latest_rates).map(([type, rate]) => ({
        name: type.charAt(0).toUpperCase() + type.slice(1),
        rate: rate,
        change: dashboardData.rate_changes_30d[type] || 0,
      }))
    : []

  const trendData = [
    { month: 'Jul', handysize: 11.2, supramax: 14.5, panamax: 16.8, capesize: 20.1 },
    { month: 'Aug', handysize: 11.8, supramax: 15.0, panamax: 17.2, capesize: 20.8 },
    { month: 'Sep', handysize: 12.1, supramax: 15.3, panamax: 17.5, capesize: 21.2 },
    { month: 'Oct', handysize: 12.3, supramax: 15.6, panamax: 17.9, capesize: 21.8 },
    { month: 'Nov', handysize: 12.4, supramax: 15.7, panamax: 18.0, capesize: 22.2 },
    { month: 'Dec', handysize: 12.5, supramax: 15.8, panamax: 18.2, capesize: 22.5 },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard Overview</h2>
        <p className="mt-1 text-sm text-gray-500">
          Real-time freight market insights and forecasting metrics
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Avg. Freight Rate"
          value={`$${dashboardData?.latest_rates?.supramax?.toFixed(2) || '0'}/ton`}
          change={dashboardData?.rate_changes_30d?.supramax?.toFixed(1)}
          changeType={dashboardData?.rate_changes_30d?.supramax > 0 ? 'increase' : 'decrease'}
          icon={CurrencyDollarIcon}
          color="blue"
        />
        <StatCard
          title="Active Routes"
          value={dashboardData?.active_routes_count || 0}
          icon={TruckIcon}
          color="green"
        />
        <StatCard
          title="Congested Ports"
          value={dashboardData?.congested_ports_count || 0}
          icon={MapPinIcon}
          color="yellow"
        />
        <StatCard
          title="Market Sentiment"
          value={marketData?.market_sentiment?.toUpperCase() || 'N/A'}
          icon={ExclamationTriangleIcon}
          color={marketData?.market_sentiment === 'bullish' ? 'green' : 'red'}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Freight Rates by Vessel Type */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Current Freight Rates by Vessel Type
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={rateChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip
                formatter={(value) => [`$${value}/ton`, 'Rate']}
                contentStyle={{ borderRadius: '8px' }}
              />
              <Bar dataKey="rate" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Rate Trends */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            6-Month Rate Trends
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip contentStyle={{ borderRadius: '8px' }} />
              <Legend />
              <Line type="monotone" dataKey="handysize" stroke="#3b82f6" strokeWidth={2} />
              <Line type="monotone" dataKey="supramax" stroke="#10b981" strokeWidth={2} />
              <Line type="monotone" dataKey="panamax" stroke="#f59e0b" strokeWidth={2} />
              <Line type="monotone" dataKey="capesize" stroke="#ef4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <a
            href="/forecast"
            className="flex items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
          >
            <div className="flex-shrink-0 p-2 bg-blue-500 rounded-lg">
              <CurrencyDollarIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-900">Forecast Rates</p>
              <p className="text-xs text-gray-500">Predict future freight rates</p>
            </div>
          </a>
          <a
            href="/market-entry"
            className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
          >
            <div className="flex-shrink-0 p-2 bg-green-500 rounded-lg">
              <TruckIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-900">Market Entry</p>
              <p className="text-xs text-gray-500">Find optimal timing</p>
            </div>
          </a>
          <a
            href="/vessel-optimization"
            className="flex items-center p-4 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors"
          >
            <div className="flex-shrink-0 p-2 bg-yellow-500 rounded-lg">
              <MapPinIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-900">Optimize Vessel</p>
              <p className="text-xs text-gray-500">Select best vessel type</p>
            </div>
          </a>
          <a
            href="/risk"
            className="flex items-center p-4 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
          >
            <div className="flex-shrink-0 p-2 bg-red-500 rounded-lg">
              <ExclamationTriangleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-900">Assess Risk</p>
              <p className="text-xs text-gray-500">Evaluate voyage risks</p>
            </div>
          </a>
        </div>
      </div>
    </div>
  )
}
