import { useState } from 'react'
import SelectField from '../components/SelectField'
import InputField from '../components/InputField'
import LoadingSpinner from '../components/LoadingSpinner'
import {
  ShieldExclamationIcon,
  CloudIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'

const vesselTypes = [
  { value: 'handysize', label: 'Handysize' },
  { value: 'supramax', label: 'Supramax' },
  { value: 'panamax', label: 'Panamax' },
  { value: 'capesize', label: 'Capesize' },
]

const originPorts = [
  { value: '8', label: 'Newcastle, Australia' },
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

export default function RiskAssessment() {
  const [formData, setFormData] = useState({
    vesselType: '',
    originPort: '',
    destinationPort: '',
    voyageDate: '',
  })
  const [loading, setLoading] = useState(false)
  const [assessment, setAssessment] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const mockAssessment = generateMockAssessment(formData)
      setAssessment(mockAssessment)
    } catch (err) {
      setError('Failed to assess risks. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const generateMockAssessment = (data) => {
    const voyageDate = new Date(data.voyageDate || Date.now())
    const month = voyageDate.getMonth() + 1

    // Weather risk based on monsoon season
    let weatherRisk, weatherDesc, weatherMitigation
    if (month >= 6 && month <= 9) {
      weatherRisk = 'high'
      weatherDesc = 'Monsoon season in Indian Ocean region. Expect rough seas and potential delays.'
      weatherMitigation = 'Consider weather routing services and build buffer time into schedule.'
    } else if (month >= 11 || month <= 2) {
      weatherRisk = 'medium'
      weatherDesc = 'Winter weather may cause moderate disruptions in certain regions.'
      weatherMitigation = 'Monitor weather forecasts and maintain communication with vessel.'
    } else {
      weatherRisk = 'low'
      weatherDesc = 'Generally favorable weather conditions expected.'
      weatherMitigation = 'Standard weather monitoring recommended.'
    }

    // Congestion risk
    const congestionLevel = Math.random()
    let congestionRisk, congestionDesc, congestionMitigation
    if (congestionLevel > 0.7) {
      congestionRisk = 'high'
      congestionDesc = 'High port congestion reported. Expect significant waiting times at anchorage.'
      congestionMitigation = 'Consider alternative discharge ports or adjust arrival timing.'
    } else if (congestionLevel > 0.4) {
      congestionRisk = 'medium'
      congestionDesc = 'Moderate congestion levels. Some waiting time expected.'
      congestionMitigation = 'Coordinate with port agents for optimal arrival window.'
    } else {
      congestionRisk = 'low'
      congestionDesc = 'Port congestion is within normal levels.'
      congestionMitigation = 'Maintain standard port coordination procedures.'
    }

    // Market volatility risk
    const volatility = Math.random()
    let marketRisk, marketDesc, marketMitigation
    if (volatility > 0.7) {
      marketRisk = 'high'
      marketDesc = 'High freight rate volatility observed. Rates may fluctuate significantly.'
      marketMitigation = 'Consider locking in rates with term contracts or hedging strategies.'
    } else if (volatility > 0.4) {
      marketRisk = 'medium'
      marketDesc = 'Moderate market volatility. Some rate fluctuations expected.'
      marketMitigation = 'Monitor market closely and be prepared to act on favorable rates.'
    } else {
      marketRisk = 'low'
      marketDesc = 'Market conditions are relatively stable.'
      marketMitigation = 'Standard market monitoring recommended.'
    }

    // Calculate overall risk
    const riskWeights = { low: 1, medium: 2, high: 3 }
    const riskValues = [riskWeights[weatherRisk], riskWeights[congestionRisk], riskWeights[marketRisk]]
    const overallScore = (riskValues.reduce((a, b) => a + b, 0) / (riskValues.length * 3)) * 100

    let overallRisk
    if (overallScore > 66) overallRisk = 'high'
    else if (overallScore > 33) overallRisk = 'medium'
    else overallRisk = 'low'

    const recommendations = [
      'Maintain regular communication with vessel and port agents',
      'Monitor weather forecasts and market conditions daily',
      'Ensure all documentation is prepared in advance',
    ]

    if (overallRisk === 'high') {
      recommendations.unshift('Consider postponing voyage if timeline allows')
      recommendations.push('Prepare contingency plans for potential delays')
    }

    return {
      overallRiskLevel: overallRisk,
      riskScore: Math.round(overallScore),
      weatherRisk,
      congestionRisk,
      marketRisk,
      riskFactors: [
        {
          factor: 'Weather Conditions',
          level: weatherRisk,
          description: weatherDesc,
          mitigation: weatherMitigation,
          icon: CloudIcon,
        },
        {
          factor: 'Port Congestion',
          level: congestionRisk,
          description: congestionDesc,
          mitigation: congestionMitigation,
          icon: MapPinIcon,
        },
        {
          factor: 'Market Volatility',
          level: marketRisk,
          description: marketDesc,
          mitigation: marketMitigation,
          icon: CurrencyDollarIcon,
        },
      ],
      recommendations,
      voyageDate: voyageDate.toLocaleDateString(),
    }
  }

  const getRiskColor = (level) => {
    switch (level) {
      case 'high': return 'text-red-600 bg-red-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'low': return 'text-green-600 bg-green-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getRiskBgColor = (level) => {
    switch (level) {
      case 'high': return 'bg-red-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Risk Assessment</h2>
        <p className="mt-1 text-sm text-gray-500">
          Evaluate potential risks for your voyage and get mitigation recommendations
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Input Form */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Voyage Details</h3>
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
              label="Voyage Date"
              type="date"
              value={formData.voyageDate}
              onChange={(value) => setFormData({ ...formData, voyageDate: value })}
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary flex items-center justify-center"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Assessing...
                </>
              ) : (
                'Assess Risks'
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

          {assessment && (
            <>
              {/* Overall Risk Score */}
              <div className={`card ${
                assessment.overallRiskLevel === 'high' ? 'bg-red-50 border-red-200' :
                assessment.overallRiskLevel === 'medium' ? 'bg-yellow-50 border-yellow-200' :
                'bg-green-50 border-green-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ShieldExclamationIcon className={`h-12 w-12 ${
                      assessment.overallRiskLevel === 'high' ? 'text-red-500' :
                      assessment.overallRiskLevel === 'medium' ? 'text-yellow-500' :
                      'text-green-500'
                    }`} />
                    <div className="ml-4">
                      <h3 className="text-lg font-semibold text-gray-900">
                        Overall Risk: <span className="capitalize">{assessment.overallRiskLevel}</span>
                      </h3>
                      <p className="text-sm text-gray-600">
                        Voyage Date: {assessment.voyageDate}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-4xl font-bold ${
                      assessment.overallRiskLevel === 'high' ? 'text-red-600' :
                      assessment.overallRiskLevel === 'medium' ? 'text-yellow-600' :
                      'text-green-600'
                    }`}>
                      {assessment.riskScore}
                    </div>
                    <p className="text-sm text-gray-500">Risk Score</p>
                  </div>
                </div>
              </div>

              {/* Risk Factors */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Factors</h3>
                <div className="space-y-4">
                  {assessment.riskFactors.map((factor, idx) => (
                    <div key={idx} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start">
                          <div className={`p-2 rounded-lg ${getRiskColor(factor.level)}`}>
                            <factor.icon className="h-6 w-6" />
                          </div>
                          <div className="ml-4">
                            <div className="flex items-center">
                              <h4 className="font-medium text-gray-900">{factor.factor}</h4>
                              <span className={`ml-2 text-xs px-2 py-1 rounded-full capitalize ${getRiskColor(factor.level)}`}>
                                {factor.level}
                              </span>
                            </div>
                            <p className="mt-1 text-sm text-gray-600">{factor.description}</p>
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 ml-14 p-3 bg-gray-50 rounded-lg">
                        <p className="text-sm">
                          <span className="font-medium text-gray-700">Mitigation: </span>
                          <span className="text-gray-600">{factor.mitigation}</span>
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommendations */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
                <ul className="space-y-3">
                  {assessment.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start">
                      <CheckCircleIcon className="h-5 w-5 text-primary-500 mr-3 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}

          {!assessment && !error && (
            <div className="card text-center py-12">
              <ShieldExclamationIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">Risk Assessment</h3>
              <p className="mt-1 text-sm text-gray-500">
                Enter voyage details to evaluate potential risks and get recommendations.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
