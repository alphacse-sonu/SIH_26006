import { useState, useEffect } from 'react'
import LoadingSpinner from '../components/LoadingSpinner'
import SelectField from '../components/SelectField'
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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts'

const vesselTypes = [
  { value: 'handysize', label: 'Handysize' },
  { value: 'supramax', label: 'Supramax' },
  { value: 'panamax', label: 'Panamax' },
  { value: 'capesize', label: 'Capesize' },
]

export default function Analytics() {
  const [loading, setLoading] = useState(true)
  const [selectedVessel, setSelectedVessel] = useState('supramax')
  const [marketData, setMarketData] = useState(null)

  useEffect(() => {
    fetchAnalytics()
  }, [selectedVessel])

  const fetchAnalytics = async () => {
    setLoading(true)
    // Simulate API call with mock data
    setTimeout(() => {
      setMarketData(generateMockAnalytics(selectedVessel))
      setLoading(false)
    }, 500)
  }

  const generateMockAnalytics = (vesselType) => {
    const baseRates = {
      handysize: 12.5,
      supramax: 15.8,
      panamax: 18.2,
      capesize: 22.5,
    }
    const base = baseRates[vesselType]

    // Monthly data for the year
    const monthlyData = [
      { month: 'Jan', rate: base * 1.08, volume: 2500000 },
      { month: 'Feb', rate: base * 1.05, volume: 2300000 },
      { month: 'Mar', rate: base * 1.02, volume: 2400000 },
      { month: 'Apr', rate: base * 0.98, volume: 2200000 },
      { month: 'May', rate: base * 0.95, volume: 2100000 },
      { month: 'Jun', rate: base * 0.92, volume: 1900000 },
      { month: 'Jul', rate: base * 0.90, volume: 1800000 },
      { month: 'Aug', rate: base * 0.92, volume: 1850000 },
      { month: 'Sep', rate: base * 0.96, volume: 2000000 },
      { month: 'Oct', rate: base * 1.02, volume: 2300000 },
      { month: 'Nov', rate: base * 1.10, volume: 2600000 },
      { month: 'Dec', rate: base * 1.12, volume: 2700000 },
    ]

    // Route comparison data
    const routeData = [
      { route: 'Australia-Paradip', avgRate: base * 1.0, volume: 45, distance: 5800 },
      { route: 'Australia-Vizag', avgRate: base * 0.98, volume: 38, distance: 5700 },
      { route: 'USA-Paradip', avgRate: base * 1.15, volume: 22, distance: 9500 },
      { route: 'Indonesia-Vizag', avgRate: base * 0.85, volume: 30, distance: 2700 },
      { route: 'Mozambique-Dhamra', avgRate: base * 0.92, volume: 18, distance: 3200 },
    ]

    // Seasonal pattern radar
    const seasonalPattern = [
      { season: 'Q1 (Jan-Mar)', value: 85 },
      { season: 'Q2 (Apr-Jun)', value: 65 },
      { season: 'Q3 (Jul-Sep)', value: 55 },
      { season: 'Q4 (Oct-Dec)', value: 95 },
    ]

    // Market metrics
    const metrics = {
      currentRate: base,
      avgRate: (monthlyData.reduce((sum, m) => sum + m.rate, 0) / 12).toFixed(2),
      minRate: Math.min(...monthlyData.map(m => m.rate)).toFixed(2),
      maxRate: Math.max(...monthlyData.map(m => m.rate)).toFixed(2),
      volatility: ((Math.max(...monthlyData.map(m => m.rate)) - Math.min(...monthlyData.map(m => m.rate))) / base * 100).toFixed(1),
      totalVolume: (monthlyData.reduce((sum, m) => sum + m.volume, 0) / 1000000).toFixed(1),
      peakMonths: ['November', 'December', 'January'],
      lowMonths: ['July', 'August'],
    }

    return {
      monthlyData,
      routeData,
      seasonalPattern,
      metrics,
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Market Analytics</h2>
          <p className="mt-1 text-sm text-gray-500">
            Comprehensive market analysis and seasonal patterns
          </p>
        </div>
        <div className="w-48">
          <SelectField
            options={vesselTypes}
            value={selectedVessel}
            onChange={setSelectedVessel}
            placeholder="Select vessel type"
          />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <div className="card text-center">
          <p className="text-sm text-gray-500">Current Rate</p>
          <p className="text-xl font-bold text-primary-600">${marketData.metrics.currentRate}/ton</p>
        </div>
        <div className="card text-center">
          <p className="text-sm text-gray-500">Avg Rate (YTD)</p>
          <p className="text-xl font-bold text-gray-900">${marketData.metrics.avgRate}/ton</p>
        </div>
        <div className="card text-center">
          <p className="text-sm text-gray-500">Min Rate</p>
          <p className="text-xl font-bold text-green-600">${marketData.metrics.minRate}/ton</p>
        </div>
        <div className="card text-center">
          <p className="text-sm text-gray-500">Max Rate</p>
          <p className="text-xl font-bold text-red-600">${marketData.metrics.maxRate}/ton</p>
        </div>
        <div className="card text-center">
          <p className="text-sm text-gray-500">Volatility</p>
          <p className="text-xl font-bold text-yellow-600">{marketData.metrics.volatility}%</p>
        </div>
        <div className="card text-center">
          <p className="text-sm text-gray-500">Total Volume</p>
          <p className="text-xl font-bold text-gray-900">{marketData.metrics.totalVolume}M MT</p>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Monthly Rate Trend */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Rate Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={marketData.monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis domain={['auto', 'auto']} />
              <Tooltip
                formatter={(value) => [`$${value.toFixed(2)}/ton`, 'Rate']}
                contentStyle={{ borderRadius: '8px' }}
              />
              <Line
                type="monotone"
                dataKey="rate"
                stroke="#2563eb"
                strokeWidth={3}
                dot={{ fill: '#2563eb' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Seasonal Pattern */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Seasonal Demand Pattern</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={marketData.seasonalPattern}>
              <PolarGrid />
              <PolarAngleAxis dataKey="season" />
              <PolarRadiusAxis angle={30} domain={[0, 100]} />
              <Radar
                name="Demand Index"
                dataKey="value"
                stroke="#2563eb"
                fill="#3b82f6"
                fillOpacity={0.5}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Route Comparison */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Route Rate Comparison</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={marketData.routeData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="route" type="category" width={120} />
              <Tooltip
                formatter={(value) => [`$${value.toFixed(2)}/ton`, 'Avg Rate']}
                contentStyle={{ borderRadius: '8px' }}
              />
              <Bar dataKey="avgRate" fill="#2563eb" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Volume by Month */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Cargo Volume</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={marketData.monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip
                formatter={(value) => [`${(value / 1000000).toFixed(2)}M MT`, 'Volume']}
                contentStyle={{ borderRadius: '8px' }}
              />
              <Bar dataKey="volume" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Insights */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Market Insights</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="p-4 bg-green-50 rounded-lg">
            <h4 className="font-medium text-green-800">Best Time to Charter</h4>
            <p className="mt-1 text-sm text-green-700">
              Lowest rates typically occur in <strong>{marketData.metrics.lowMonths.join(' and ')}</strong>. 
              Consider planning shipments during these months for cost savings.
            </p>
          </div>
          <div className="p-4 bg-yellow-50 rounded-lg">
            <h4 className="font-medium text-yellow-800">Peak Season Alert</h4>
            <p className="mt-1 text-sm text-yellow-700">
              Highest demand and rates occur in <strong>{marketData.metrics.peakMonths.join(', ')}</strong>. 
              Book early or consider term contracts to secure capacity.
            </p>
          </div>
          <div className="p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-blue-800">Route Recommendation</h4>
            <p className="mt-1 text-sm text-blue-700">
              Indonesia routes offer the lowest rates due to shorter distances. 
              Consider for cost-sensitive shipments when quality requirements allow.
            </p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg">
            <h4 className="font-medium text-purple-800">Volatility Analysis</h4>
            <p className="mt-1 text-sm text-purple-700">
              Current volatility of <strong>{marketData.metrics.volatility}%</strong> suggests 
              {parseFloat(marketData.metrics.volatility) > 15 
                ? ' high market uncertainty. Consider hedging strategies.'
                : ' relatively stable conditions. Good time for spot chartering.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
