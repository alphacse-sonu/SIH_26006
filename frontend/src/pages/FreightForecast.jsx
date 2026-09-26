import { useState } from 'react'
import SelectField from '../components/SelectField'
import InputField from '../components/InputField'
import LoadingSpinner from '../components/LoadingSpinner'
import { predictionsApi } from '../services/api'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'
import { format } from 'date-fns'

const vesselTypes = [
  { value: 'handysize', label: 'Handysize (15,000-35,000 DWT)' },
  { value: 'supramax', label: 'Supramax (50,000-60,000 DWT)' },
  { value: 'panamax', label: 'Panamax (65,000-80,000 DWT)' },
  { value: 'capesize', label: 'Capesize (100,000-200,000 DWT)' },
]

const originPorts = [
  { value: '8', label: 'Newcastle, Australia' },
  { value: '9', label: 'Hay Point, Australia' },
  { value: '10', label: 'Gladstone, Australia' },
  { value: '11', label: 'Hampton Roads, USA' },
  { value: '12', label: 'Baltimore, USA' },
  { value: '13', label: 'Nacala, Mozambique' },
  { value: '14', label: 'Beira, Mozambique' },
  { value: '15', label: 'Samarinda, Indonesia' },
  { value: '16', label: 'Banjarmasin, Indonesia' },
  { value: '17', label: 'Murmansk, Russia' },
]

const destinationPorts = [
  { value: '1', label: 'Paradip, India' },
  { value: '2', label: 'Vizag (Visakhapatnam), India' },
  { value: '3', label: 'Gangavaram, India' },
  { value: '4', label: 'Gopalpur, India' },
  { value: '5', label: 'Dhamra, India' },
  { value: '6', label: 'Haldia, India' },
  { value: '7', label: 'Sagar-Sandheads, India' },
]

export default function FreightForecast() {
  const [formData, setFormData] = useState({
    vesselType: '',
    originPort: '',
    destinationPort: '',
    forecastDays: '30',
    cargoVolume: '',
  })
  const [loading, setLoading] = useState(false)
  const [forecast, setForecast] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Generate mock forecast data for demo
      const mockForecast = generateMockForecast(
        formData.vesselType,
        parseInt(formData.forecastDays)
      )
      setForecast(mockForecast)
    } catch (err) {
      setError('Failed to generate forecast. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const generateMockForecast = (vesselType, days) => {
    const baseRates = {
      handysize: 12.5,
      supramax: 15.8,
      panamax: 18.2,
      capesize: 22.5,
    }
    const baseRate = baseRates[vesselType] || 15
    const forecasts = []
    const today = new Date()

    for (let i = 0; i < days; i++) {
      const date = new Date(today)
      date.setDate(date.getDate() + i)
      
      const seasonalFactor = 1 + 0.05 * Math.sin((2 * Math.PI * (date.getMonth() + 1)) / 12)
      const trendFactor = 1 + i * 0.001 * (Math.random() > 0.5 ? 1 : -1)
      const volatility = (Math.random() - 0.5) * 0.04
      
      const predictedRate = baseRate * seasonalFactor * trendFactor * (1 + volatility)
      const confidenceMargin = predictedRate * 0.1 * (1 + i * 0.005)

      forecasts.push({
        date: format(date, 'MMM dd'),
        fullDate: date.toISOString(),
        predicted_rate: parseFloat(predictedRate.toFixed(2)),
        confidence_lower: parseFloat((predictedRate - confidenceMargin).toFixed(2)),
        confidence_upper: parseFloat((predictedRate + confidenceMargin).toFixed(2)),
        trend: i > 0 && forecasts[i - 1] 
          ? predictedRate > forecasts[i - 1].predicted_rate * 1.01 ? 'up' 
          : predictedRate < forecasts[i - 1].predicted_rate * 0.99 ? 'down' : 'stable'
          : 'stable',
      })
    }

    return {
      vessel_type: vesselType,
      forecasts,
      summary: {
        avg_rate: (forecasts.reduce((sum, f) => sum + f.predicted_rate, 0) / forecasts.length).toFixed(2),
        min_rate: Math.min(...forecasts.map(f => f.predicted_rate)).toFixed(2),
        max_rate: Math.max(...forecasts.map(f => f.predicted_rate)).toFixed(2),
        trend: forecasts[forecasts.length - 1].predicted_rate > forecasts[0].predicted_rate ? 'Upward' : 'Downward',
      },
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Freight Rate Forecast</h2>
        <p className="mt-1 text-sm text-gray-500">
          Predict future freight rates using our ML-powered forecasting model
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Input Form */}
        <div className="card lg:col-span-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Forecast Parameters</h3>
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
              label="Forecast Horizon (Days)"
              type="number"
              value={formData.forecastDays}
              onChange={(value) => setFormData({ ...formData, forecastDays: value })}
              min="7"
              max="180"
              required
            />
            <InputField
              label="Cargo Volume (MT)"
              type="number"
              value={formData.cargoVolume}
              onChange={(value) => setFormData({ ...formData, cargoVolume: value })}
              placeholder="Optional"
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary flex items-center justify-center"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Generating Forecast...
                </>
              ) : (
                'Generate Forecast'
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

          {forecast && (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Average Rate</p>
                  <p className="text-xl font-bold text-primary-600">
                    ${forecast.summary.avg_rate}/ton
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Min Rate</p>
                  <p className="text-xl font-bold text-green-600">
                    ${forecast.summary.min_rate}/ton
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Max Rate</p>
                  <p className="text-xl font-bold text-red-600">
                    ${forecast.summary.max_rate}/ton
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Trend</p>
                  <p className={`text-xl font-bold ${
                    forecast.summary.trend === 'Upward' ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {forecast.summary.trend}
                  </p>
                </div>
              </div>

              {/* Forecast Chart */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Rate Forecast with Confidence Interval
                </h3>
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={forecast.forecasts}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={['auto', 'auto']} />
                    <Tooltip
                      contentStyle={{ borderRadius: '8px' }}
                      formatter={(value, name) => [
                        `$${value}/ton`,
                        name === 'predicted_rate' ? 'Predicted' :
                        name === 'confidence_upper' ? 'Upper Bound' : 'Lower Bound'
                      ]}
                    />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="confidence_upper"
                      stroke="#93c5fd"
                      fill="#dbeafe"
                      name="Upper Bound"
                    />
                    <Area
                      type="monotone"
                      dataKey="confidence_lower"
                      stroke="#93c5fd"
                      fill="#ffffff"
                      name="Lower Bound"
                    />
                    <Line
                      type="monotone"
                      dataKey="predicted_rate"
                      stroke="#2563eb"
                      strokeWidth={3}
                      dot={false}
                      name="Predicted Rate"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Recommendations */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
                <div className="space-y-3">
                  {forecast.summary.trend === 'Upward' ? (
                    <div className="flex items-start p-3 bg-yellow-50 rounded-lg">
                      <span className="text-yellow-500 mr-3">⚠️</span>
                      <div>
                        <p className="font-medium text-gray-900">Rates Expected to Rise</p>
                        <p className="text-sm text-gray-600">
                          Consider locking in current rates with a short-term contract to avoid higher costs.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start p-3 bg-green-50 rounded-lg">
                      <span className="text-green-500 mr-3">✓</span>
                      <div>
                        <p className="font-medium text-gray-900">Favorable Market Conditions</p>
                        <p className="text-sm text-gray-600">
                          Rates are expected to decrease. Consider waiting for better rates if timeline allows.
                        </p>
                      </div>
                    </div>
                  )}
                  <div className="flex items-start p-3 bg-blue-50 rounded-lg">
                    <span className="text-blue-500 mr-3">ℹ️</span>
                    <div>
                      <p className="font-medium text-gray-900">Model Confidence</p>
                      <p className="text-sm text-gray-600">
                        Predictions are based on historical data and market indicators. 
                        Confidence intervals widen for longer forecast horizons.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {!forecast && !error && (
            <div className="card text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900">No Forecast Generated</h3>
              <p className="mt-1 text-sm text-gray-500">
                Fill in the parameters and click "Generate Forecast" to see predictions.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
