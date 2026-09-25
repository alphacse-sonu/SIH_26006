import { useState } from 'react'
import SelectField from '../components/SelectField'
import InputField from '../components/InputField'
import LoadingSpinner from '../components/LoadingSpinner'
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/solid'

const originPorts = [
  { value: '8', label: 'Newcastle, Australia' },
  { value: '9', label: 'Hay Point, Australia' },
  { value: '10', label: 'Gladstone, Australia' },
  { value: '11', label: 'Hampton Roads, USA' },
  { value: '13', label: 'Nacala, Mozambique' },
  { value: '15', label: 'Samarinda, Indonesia' },
  { value: '16', label: 'Banjarmasin, Indonesia' },
]

const destinationPorts = [
  { value: '1', label: 'Paradip, India', maxDwt: 150000, maxDraft: 14.5 },
  { value: '2', label: 'Vizag, India', maxDwt: 180000, maxDraft: 17.1 },
  { value: '3', label: 'Gangavaram, India', maxDwt: 200000, maxDraft: 21.0 },
  { value: '4', label: 'Gopalpur, India', maxDwt: 80000, maxDraft: 14.0 },
  { value: '5', label: 'Dhamra, India', maxDwt: 180000, maxDraft: 18.0 },
  { value: '6', label: 'Haldia, India', maxDwt: 60000, maxDraft: 8.5 },
]

const cargoTypes = [
  { value: 'coal', label: 'Coal' },
  { value: 'iron_ore', label: 'Iron Ore' },
  { value: 'grain', label: 'Grain' },
]

export default function VesselOptimization() {
  const [formData, setFormData] = useState({
    cargoVolume: '',
    originPort: '',
    destinationPort: '',
    cargoType: 'coal',
  })
  const [loading, setLoading] = useState(false)
  const [optimization, setOptimization] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const mockOptimization = generateMockOptimization(formData)
      setOptimization(mockOptimization)
    } catch (err) {
      setError('Failed to optimize vessel selection. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const generateMockOptimization = (data) => {
    const cargoVolume = parseFloat(data.cargoVolume)
    const destPort = destinationPorts.find(p => p.value === data.destinationPort)
    
    const vesselTypes = [
      {
        name: 'Handysize',
        minDwt: 15000,
        maxDwt: 35000,
        typicalDwt: 28000,
        typicalDraft: 10,
        dailyRate: 12000,
      },
      {
        name: 'Supramax',
        minDwt: 50000,
        maxDwt: 60000,
        typicalDwt: 55000,
        typicalDraft: 12.8,
        dailyRate: 16000,
      },
      {
        name: 'Panamax',
        minDwt: 65000,
        maxDwt: 80000,
        typicalDwt: 75000,
        typicalDraft: 13.5,
        dailyRate: 20000,
      },
      {
        name: 'Capesize',
        minDwt: 100000,
        maxDwt: 200000,
        typicalDwt: 180000,
        typicalDraft: 18.5,
        dailyRate: 30000,
      },
    ]

    const recommendations = vesselTypes.map(vt => {
      let score = 100
      const issues = []
      const advantages = []

      // Check cargo capacity
      if (vt.maxDwt < cargoVolume) {
        score -= 50
        issues.push(`Insufficient capacity: max ${vt.maxDwt.toLocaleString()} MT vs ${cargoVolume.toLocaleString()} MT required`)
      } else if (vt.minDwt > cargoVolume * 1.5) {
        score -= 20
        issues.push(`Vessel oversized for cargo: min ${vt.minDwt.toLocaleString()} MT`)
      } else {
        advantages.push(`Suitable capacity for ${cargoVolume.toLocaleString()} MT cargo`)
      }

      // Check port constraints
      if (destPort) {
        if (vt.typicalDwt > destPort.maxDwt) {
          score -= 40
          issues.push(`Exceeds port DWT limit: ${destPort.maxDwt.toLocaleString()} MT`)
        }
        if (vt.typicalDraft > destPort.maxDraft) {
          score -= 40
          issues.push(`Exceeds port draft limit: ${destPort.maxDraft}m`)
        } else {
          advantages.push(`Draft compatible with port (${vt.typicalDraft}m vs ${destPort.maxDraft}m max)`)
        }
      }

      // Calculate utilization
      const utilization = Math.min(cargoVolume / vt.typicalDwt, 1.0)
      if (utilization > 0.85) {
        score += 15
        advantages.push(`High utilization: ${(utilization * 100).toFixed(0)}%`)
      } else if (utilization < 0.5) {
        score -= 10
        issues.push(`Low utilization: ${(utilization * 100).toFixed(0)}%`)
      }

      // Estimate costs
      const voyageDays = 25 // Simplified
      const estimatedCost = vt.dailyRate * voyageDays
      const costPerTon = estimatedCost / cargoVolume

      return {
        vesselType: vt.name,
        score: Math.max(0, Math.min(100, score)),
        issues,
        advantages,
        utilization: (utilization * 100).toFixed(0),
        estimatedCost,
        costPerTon: costPerTon.toFixed(2),
        dailyRate: vt.dailyRate,
        typicalDwt: vt.typicalDwt,
        typicalDraft: vt.typicalDraft,
      }
    })

    recommendations.sort((a, b) => b.score - a.score)

    return {
      cargoVolume,
      recommendations,
      bestChoice: recommendations[0].vesselType,
      portConstraints: destPort ? {
        maxDwt: destPort.maxDwt,
        maxDraft: destPort.maxDraft,
      } : null,
    }
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100'
    if (score >= 60) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Vessel Type Optimization</h2>
        <p className="mt-1 text-sm text-gray-500">
          Find the optimal vessel type based on cargo volume and port constraints
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Input Form */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cargo Details</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <InputField
              label="Cargo Volume (MT)"
              type="number"
              value={formData.cargoVolume}
              onChange={(value) => setFormData({ ...formData, cargoVolume: value })}
              placeholder="e.g., 50000"
              min="1000"
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
            <SelectField
              label="Cargo Type"
              options={cargoTypes}
              value={formData.cargoType}
              onChange={(value) => setFormData({ ...formData, cargoType: value })}
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary flex items-center justify-center"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Optimizing...
                </>
              ) : (
                'Optimize Vessel Selection'
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

          {optimization && (
            <>
              {/* Best Choice Banner */}
              <div className="card bg-green-50 border-green-200">
                <div className="flex items-center">
                  <CheckCircleIcon className="h-8 w-8 text-green-500 mr-3" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Recommended: {optimization.bestChoice}
                    </h3>
                    <p className="text-sm text-gray-600">
                      Best match for {optimization.cargoVolume.toLocaleString()} MT cargo with port constraints
                    </p>
                  </div>
                </div>
              </div>

              {/* Port Constraints Info */}
              {optimization.portConstraints && (
                <div className="card bg-blue-50 border-blue-200">
                  <h4 className="font-medium text-gray-900 mb-2">Destination Port Constraints</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Max DWT:</span>
                      <span className="ml-2 font-medium">{optimization.portConstraints.maxDwt.toLocaleString()} MT</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Max Draft:</span>
                      <span className="ml-2 font-medium">{optimization.portConstraints.maxDraft}m</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Vessel Recommendations */}
              <div className="space-y-4">
                {optimization.recommendations.map((rec, idx) => (
                  <div key={rec.vesselType} className={`card ${
                    idx === 0 ? 'ring-2 ring-green-500' : ''
                  }`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center">
                        <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full text-lg font-bold ${
                          getScoreColor(rec.score)
                        }`}>
                          {rec.score}
                        </span>
                        <div className="ml-4">
                          <h4 className="text-lg font-semibold text-gray-900">
                            {rec.vesselType}
                            {idx === 0 && (
                              <span className="ml-2 text-xs bg-green-500 text-white px-2 py-1 rounded-full">
                                BEST MATCH
                              </span>
                            )}
                          </h4>
                          <p className="text-sm text-gray-500">
                            Typical: {rec.typicalDwt.toLocaleString()} DWT | Draft: {rec.typicalDraft}m
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-gray-900">
                          ${rec.costPerTon}/ton
                        </p>
                        <p className="text-sm text-gray-500">
                          ~${rec.estimatedCost.toLocaleString()} total
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                      {/* Advantages */}
                      {rec.advantages.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-green-700 mb-2">Advantages</p>
                          <ul className="space-y-1">
                            {rec.advantages.map((adv, i) => (
                              <li key={i} className="flex items-start text-sm text-gray-600">
                                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                                {adv}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Issues */}
                      {rec.issues.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-red-700 mb-2">Constraints</p>
                          <ul className="space-y-1">
                            {rec.issues.map((issue, i) => (
                              <li key={i} className="flex items-start text-sm text-gray-600">
                                <XCircleIcon className="h-4 w-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                                {issue}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Utilization Bar */}
                    <div className="mt-4">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-500">Capacity Utilization</span>
                        <span className="font-medium">{rec.utilization}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            parseInt(rec.utilization) >= 80 ? 'bg-green-500' :
                            parseInt(rec.utilization) >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${Math.min(rec.utilization, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {!optimization && !error && (
            <div className="card text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900">Optimize Your Vessel Selection</h3>
              <p className="mt-1 text-sm text-gray-500">
                Enter cargo details to get vessel recommendations based on port constraints.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
