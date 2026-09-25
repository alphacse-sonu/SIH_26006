import { useState } from 'react'
import SelectField from '../components/SelectField'
import InputField from '../components/InputField'
import LoadingSpinner from '../components/LoadingSpinner'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { format, addDays } from 'date-fns'

const vesselTypes = [
  { value: 'handysize', label: 'Handysize' },
  { value: 'supramax', label: 'Supramax' },
  { value: 'panamax', label: 'Panamax' },
  { value: 'capesize', label: 'Capesize' },
]

const originPorts = [
  { value: '8', label: 'Newcastle, Australia' },
  { value: '9', label: 'Hay Point, Australia' },
  { value: '11', label: 'Hampton Roads, USA' },
  { value: '13', label: 'Nacala, Mozambique' },
  { value: '15', label: 'Samarinda, Indonesia' },
]

const destinationPorts = [
  { value: '1', label: 'Paradip, India' },
  { value: '2', label: 'Vizag, India' },
  { value: '3', label: 'Gangavaram, India' },
  { value: '5', label: 'Dhamra, India' },
]

export default function MarketEntry() {
  const [formData, setFormData] = useState({
    vesselType: '',
    originPort: '',
    destinationPort: '',
    contractDuration: '30',
    targetDate: '',
  })
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Generate mock analysis
      const mockAnalysis = generateMockAnalysis(formData)
      setAnalysis(mockAnalysis)
    } catch (err) {
      setError('Failed to analyze market entry. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const generateMockAnalysis = (data) => {
    const baseRates = {
      handysize: 12.5,
      supramax: 15.8,
      panamax: 18.2,
      capesize: 22.5,
    }
    const baseRate = baseRates[data.vesselType] || 15
    const today = new Date()
    
    // Generate 90-day forecast
    const forecasts = []
    for (let i = 0; i < 90; i++) {
      const date = addDays(today, i)
      const seasonalFactor = 1 + 0.08 * Math.sin((2 * Math.PI * (date.getMonth() + 1)) / 12)
      const trendFactor = 1 + i * 0.0008
      const volatility = (Math.random() - 0.5) * 0.06
      const rate = baseRate * seasonalFactor * trendFactor * (1 + volatility)
      
      forecasts.push({
        date: format(date, 'MMM dd'),
        rate: parseFloat(rate.toFixed(2)),
        avgRate: baseRate * seasonalFactor,
      })
    }

    // Find optimal windows (periods below average)
    const avgRate = forecasts.reduce((sum, f) => sum + f.rate, 0) / forecasts.length
    const optimalWindows = []
    let windowStart = null

    forecasts.forEach((f, i) => {
      if (f.rate < avgRate * 0.97) {
        if (!windowStart) windowStart = i
      } else if (windowStart !== null) {
        optimalWindows.push({
          start: forecasts[windowStart].date,
          end: forecasts[i - 1].date,
          avgRate: (forecasts.slice(windowStart, i).reduce((s, x) => s + x.rate, 0) / (i - windowStart)).toFixed(2),
          savings: ((avgRate - forecasts.slice(windowStart, i).reduce((s, x) => s + x.rate, 0) / (i - windowStart)) / avgRate * 100).toFixed(1),
        })
        windowStart = null
      }
    })

    const currentRate = forecasts[0].rate
    const rate30d = forecasts[29].rate
    const trend = rate30d > currentRate * 1.03 ? 'bullish' : rate30d < currentRate * 0.97 ? 'bearish' : 'stable'

    return {
      currentRate: currentRate.toFixed(2),
      predictedRate30d: rate30d.toFixed(2),
      avgRate: avgRate.toFixed(2),
      marketTrend: trend,
      confidenceScore: (75 + Math.random() * 20).toFixed(1),
      optimalWindows: optimalWindows.slice(0, 3),
      forecasts,
      recommendation: trend === 'bullish' 
        ? 'Market rates are expected to rise. Consider entering the market soon to lock in current rates.'
        : trend === 'bearish'
        ? 'Market rates are expected to decline. Consider waiting for better rates if your timeline allows.'
        : 'Market is relatively stable. Enter based on your operational requirements.',
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Market Entry Analysis</h2>
        <p className="mt-1 text-sm text-gray-500">
          Identify optimal timing for charter contracts based on market forecasts
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Input Form */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Parameters</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <SelectField
              label="Vessel Type"
              options={vesselTypes}
              value={formData.vesselType}
              onChange={(value) => setFormData({ ...formData, vesselType: value })}
              required
            />
            <SelectField
              label="Origin Port"
              options={originPorts}
              value={formData.originPort}
              onChange={(value) => setFormData({ ...formData, originPort: value })}
              required
            />
            <SelectField
              label="Destination Port"
              options={destinationPorts}
              value={formData.destinationPort}
              onChange={(value) => setFormData({ ...formData, destinationPort: value })}
              required
            />
            <InputField
              label="Contract Duration (Days)"
              type="number"
              value={formData.contractDuration}
              onChange={(value) => setFormData({ ...formData, contractDuration: value })}
              min="7"
              max="365"
              required
            />
            <InputField
              label="Target Start Date"
              type="date"
              value={formData.targetDate}
              onChange={(value) => setFormData({ ...formData, targetDate: value })}
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary flex items-center justify-center"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Analyzing...
                </>
              ) : (
                'Analyze Market Entry'
              )}
            </button>
          </form>
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {error && (
            <div className="card bg-red-50 border-red-200">
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {analysis && (
            <>
              {/* Key Metrics */}
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Current Rate</p>
                  <p className="text-xl font-bold text-gray-900">${analysis.currentRate}/ton</p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-500">30-Day Forecast</p>
                  <p className={`text-xl font-bold ${
                    parseFloat(analysis.predictedRate30d) > parseFloat(analysis.currentRate) 
                      ? 'text-red-600' : 'text-green-600'
                  }`}>
                    ${analysis.predictedRate30d}/ton
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Market Trend</p>
                  <p className={`text-xl font-bold capitalize ${
                    analysis.marketTrend === 'bullish' ? 'text-red-600' :
                    analysis.marketTrend === 'bearish' ? 'text-green-600' : 'text-gray-600'
                  }`}>
                    {analysis.marketTrend}
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Confidence</p>
                  <p className="text-xl font-bold text-primary-600">{analysis.confidenceScore}%</p>
                </div>
              </div>

              {/* Rate Forecast Chart */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">90-Day Rate Forecast</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <AreaChart data={analysis.forecasts}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" interval={14} />
                    <YAxis domain={['auto', 'auto']} />
                    <Tooltip contentStyle={{ borderRadius: '8px' }} />
                    <ReferenceLine 
                      y={parseFloat(analysis.avgRate)} 
                      stroke="#f59e0b" 
                      strokeDasharray="5 5"
                      label={{ value: 'Avg', position: 'right' }}
                    />
                    <Area
                      type="monotone"
                      dataKey="rate"
                      stroke="#2563eb"
                      fill="#dbeafe"
                      name="Predicted Rate"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Optimal Entry Windows */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Optimal Entry Windows</h3>
                {analysis.optimalWindows.length > 0 ? (
                  <div className="space-y-3">
                    {analysis.optimalWindows.map((window, idx) => (
                      <div key={idx} className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">
                            {window.start} - {window.end}
                          </p>
                          <p className="text-sm text-gray-600">
                            Expected Rate: ${window.avgRate}/ton
                          </p>
                        </div>
                        <div className="text-right">
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            Save {window.savings}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No significant entry windows identified in the forecast period.</p>
                )}
              </div>

              {/* Recommendation */}
              <div className={`card ${
                analysis.marketTrend === 'bullish' ? 'bg-yellow-50 border-yellow-200' :
                analysis.marketTrend === 'bearish' ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200'
              }`}>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Recommendation</h3>
                <p className="text-gray-700">{analysis.recommendation}</p>
              </div>
            </>
          )}

          {!analysis && !error && (
            <div className="card text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900">Ready to Analyze</h3>
              <p className="mt-1 text-sm text-gray-500">
                Enter your parameters to find the optimal market entry timing.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
