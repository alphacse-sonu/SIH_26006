import { useState, useEffect } from 'react'
import LoadingSpinner from '../components/LoadingSpinner'
import { MapPinIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'

const mockPorts = {
  indian: [
    { id: 1, name: 'Paradip', code: 'INPRT', maxDraft: 14.5, maxDwt: 150000, maxVessel: 'Capesize', congestion: 0.45, waitingVessels: 8, avgWaitHours: 24 },
    { id: 2, name: 'Vizag', code: 'INVTZ', maxDraft: 17.1, maxDwt: 180000, maxVessel: 'Capesize', congestion: 0.62, waitingVessels: 12, avgWaitHours: 36 },
    { id: 3, name: 'Gangavaram', code: 'INGVP', maxDraft: 21.0, maxDwt: 200000, maxVessel: 'Capesize', congestion: 0.35, waitingVessels: 5, avgWaitHours: 18 },
    { id: 4, name: 'Gopalpur', code: 'INGOP', maxDraft: 14.0, maxDwt: 80000, maxVessel: 'Panamax', congestion: 0.28, waitingVessels: 3, avgWaitHours: 12 },
    { id: 5, name: 'Dhamra', code: 'INDHA', maxDraft: 18.0, maxDwt: 180000, maxVessel: 'Capesize', congestion: 0.52, waitingVessels: 9, avgWaitHours: 28 },
    { id: 6, name: 'Haldia', code: 'INHAL', maxDraft: 8.5, maxDwt: 60000, maxVessel: 'Supramax', congestion: 0.78, waitingVessels: 15, avgWaitHours: 48 },
    { id: 7, name: 'Sagar-Sandheads', code: 'INSAG', maxDraft: 12.5, maxDwt: 100000, maxVessel: 'Panamax', congestion: 0.41, waitingVessels: 6, avgWaitHours: 20 },
  ],
  origin: [
    { id: 8, name: 'Newcastle', country: 'Australia', code: 'AUNTL', maxDraft: 15.2, maxDwt: 185000, loadingRate: 80000 },
    { id: 9, name: 'Hay Point', country: 'Australia', code: 'AUHPT', maxDraft: 18.5, maxDwt: 220000, loadingRate: 100000 },
    { id: 10, name: 'Gladstone', country: 'Australia', code: 'AUGLT', maxDraft: 16.5, maxDwt: 200000, loadingRate: 85000 },
    { id: 11, name: 'Hampton Roads', country: 'USA', code: 'USHRP', maxDraft: 15.0, maxDwt: 180000, loadingRate: 70000 },
    { id: 13, name: 'Nacala', country: 'Mozambique', code: 'MZNAC', maxDraft: 14.5, maxDwt: 120000, loadingRate: 40000 },
    { id: 15, name: 'Samarinda', country: 'Indonesia', code: 'IDSRI', maxDraft: 12.0, maxDwt: 90000, loadingRate: 35000 },
  ],
}

export default function PortAnalysis() {
  const [selectedTab, setSelectedTab] = useState('indian')
  const [selectedPort, setSelectedPort] = useState(null)

  const getCongestionColor = (level) => {
    if (level >= 0.7) return 'bg-red-500'
    if (level >= 0.4) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getCongestionStatus = (level) => {
    if (level >= 0.7) return { text: 'High', color: 'text-red-600 bg-red-100' }
    if (level >= 0.4) return { text: 'Medium', color: 'text-yellow-600 bg-yellow-100' }
    return { text: 'Low', color: 'text-green-600 bg-green-100' }
  }

  const ports = selectedTab === 'indian' ? mockPorts.indian : mockPorts.origin

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Port Analysis</h2>
        <p className="mt-1 text-sm text-gray-500">
          View port infrastructure constraints and current congestion levels
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setSelectedTab('indian')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'indian'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Indian East Coast Ports
          </button>
          <button
            onClick={() => setSelectedTab('origin')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'origin'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Origin Ports
          </button>
        </nav>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Port List */}
        <div className="lg:col-span-2">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {selectedTab === 'indian' ? 'Indian East Coast Ports' : 'Loading Ports'}
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Port</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Max Draft</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Max DWT</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      {selectedTab === 'indian' ? 'Congestion' : 'Loading Rate'}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {ports.map((port) => {
                    const congestionStatus = selectedTab === 'indian' ? getCongestionStatus(port.congestion) : null
                    return (
                      <tr key={port.id} className="hover:bg-gray-50">
                        <td className="px-4 py-4">
                          <div className="flex items-center">
                            <MapPinIcon className="h-5 w-5 text-gray-400 mr-2" />
                            <div>
                              <p className="font-medium text-gray-900">{port.name}</p>
                              <p className="text-sm text-gray-500">{port.code}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-900">{port.maxDraft}m</td>
                        <td className="px-4 py-4 text-sm text-gray-900">{port.maxDwt.toLocaleString()} MT</td>
                        <td className="px-4 py-4">
                          {selectedTab === 'indian' ? (
                            <div className="flex items-center">
                              <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                <div
                                  className={`h-2 rounded-full ${getCongestionColor(port.congestion)}`}
                                  style={{ width: `${port.congestion * 100}%` }}
                                />
                              </div>
                              <span className={`text-xs px-2 py-1 rounded-full ${congestionStatus.color}`}>
                                {congestionStatus.text}
                              </span>
                            </div>
                          ) : (
                            <span className="text-sm text-gray-900">
                              {port.loadingRate.toLocaleString()} MT/day
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-4">
                          <button
                            onClick={() => setSelectedPort(port)}
                            className="text-primary-600 hover:text-primary-800 text-sm font-medium"
                          >
                            Details
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Port Details */}
        <div className="lg:col-span-1">
          {selectedPort ? (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {selectedPort.name} Details
              </h3>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Port Code</p>
                  <p className="font-medium">{selectedPort.code}</p>
                </div>
                {selectedPort.country && (
                  <div>
                    <p className="text-sm text-gray-500">Country</p>
                    <p className="font-medium">{selectedPort.country}</p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-gray-500">Maximum Draft</p>
                  <p className="font-medium">{selectedPort.maxDraft} meters</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Maximum DWT</p>
                  <p className="font-medium">{selectedPort.maxDwt.toLocaleString()} MT</p>
                </div>
                {selectedPort.maxVessel && (
                  <div>
                    <p className="text-sm text-gray-500">Max Vessel Size</p>
                    <p className="font-medium">{selectedPort.maxVessel}</p>
                  </div>
                )}
                {selectedPort.loadingRate && (
                  <div>
                    <p className="text-sm text-gray-500">Loading Rate</p>
                    <p className="font-medium">{selectedPort.loadingRate.toLocaleString()} MT/day</p>
                  </div>
                )}
                {selectedPort.congestion !== undefined && (
                  <>
                    <div>
                      <p className="text-sm text-gray-500">Current Congestion</p>
                      <div className="mt-1">
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className={`h-3 rounded-full ${getCongestionColor(selectedPort.congestion)}`}
                            style={{ width: `${selectedPort.congestion * 100}%` }}
                          />
                        </div>
                        <p className="text-sm mt-1">{(selectedPort.congestion * 100).toFixed(0)}%</p>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Vessels Waiting</p>
                      <p className="font-medium">{selectedPort.waitingVessels} vessels</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Avg. Waiting Time</p>
                      <p className="font-medium">{selectedPort.avgWaitHours} hours</p>
                    </div>
                  </>
                )}

                {selectedPort.congestion >= 0.7 && (
                  <div className="mt-4 p-3 bg-red-50 rounded-lg">
                    <div className="flex items-start">
                      <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-2" />
                      <div>
                        <p className="text-sm font-medium text-red-800">High Congestion Alert</p>
                        <p className="text-xs text-red-600 mt-1">
                          Consider alternative ports or plan for extended waiting times.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card text-center py-12">
              <MapPinIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">Select a Port</h3>
              <p className="mt-1 text-sm text-gray-500">
                Click on a port to view detailed information.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
