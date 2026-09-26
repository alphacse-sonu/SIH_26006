import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line,
} from 'recharts';
import { Anchor, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

export default function LighteringAnalysis({ lightering }) {
  if (!lightering) return <p className="text-navy-400">No lightering data available.</p>;

  const { vessel, port, lightering_calculation, lightering_cost, direct_berthing_cost, weather_risk, recommendation, reason } = lightering;

  // TPC curve visualization data
  const tpcData = lightering_calculation?.tpc_profile?.map((p) => ({
    draft: p.draft_m,
    tpc: p.tpc,
  })) || [];

  // Cost comparison data
  const costCompare = [];
  if (lightering_calculation?.lightering_required) {
    costCompare.push({
      option: 'Lightering',
      cost: lightering_cost?.total_cost_usd || 0,
    });
    costCompare.push({
      option: 'Reduce Cargo',
      cost: direct_berthing_cost || 0,
    });
  }

  const recColor = recommendation === 'DIRECT_BERTH' ? 'accent-green' :
    recommendation === 'LIGHTER' ? 'ocean-400' : 'accent-yellow';

  const RecIcon = recommendation === 'DIRECT_BERTH' ? CheckCircle :
    recommendation === 'REDUCE_CARGO' ? AlertTriangle : Anchor;

  return (
    <div className="space-y-4">
      {/* Recommendation Banner */}
      <div className={`card glow-${recommendation === 'DIRECT_BERTH' ? 'green' : 'blue'} border-${recColor}/30`}>
        <div className="flex items-start gap-3">
          <RecIcon className={`w-6 h-6 text-${recColor} mt-0.5 shrink-0`} />
          <div>
            <h3 className={`text-lg font-bold text-${recColor}`}>
              {recommendation === 'DIRECT_BERTH' ? 'Direct Berthing' :
               recommendation === 'LIGHTER' ? 'Lightering Recommended' :
               'Reduce Cargo Recommended'}
            </h3>
            <p className="text-navy-300 text-sm mt-1">{reason}</p>
          </div>
        </div>
      </div>

      {/* Vessel & Port Info */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card">
          <p className="text-xs text-navy-400">Vessel Draft (Loaded)</p>
          <p className="text-xl font-bold text-white">{vessel?.estimated_loaded_draft_m}m</p>
          <p className="text-xs text-navy-500">{vessel?.class} ({vessel?.subtype})</p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">Port Max Draft</p>
          <p className="text-xl font-bold text-white">{port?.max_draft_m}m</p>
          <p className="text-xs text-navy-500">{port?.name}, {port?.country}</p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">Draft Excess</p>
          <p className={`text-xl font-bold ${lightering_calculation?.lightering_required ? 'text-accent-red' : 'text-accent-green'}`}>
            {lightering_calculation?.lightering_required
              ? `+${lightering_calculation?.draft_excess_m}m`
              : 'None'}
          </p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">Cargo to Lighter</p>
          <p className="text-xl font-bold text-ocean-400">
            {lightering_calculation?.cargo_to_lighter_tonnes?.toLocaleString() || 0}
          </p>
          <p className="text-xs text-navy-500">tonnes</p>
        </div>
      </div>

      {lightering_calculation?.lightering_required && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* TPC Curve */}
          {tpcData.length > 0 && (
            <div className="card">
              <h3 className="text-white font-semibold text-sm mb-3">TPC Curve (Draft Range)</h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={tpcData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d0d5dd" />
                  <XAxis
                    dataKey="draft"
                    stroke="#627d98"
                    tick={{ fontSize: 11 }}
                    label={{ value: 'Draft (m)', position: 'insideBottom', offset: -5, style: { fill: '#627d98', fontSize: 11 } }}
                  />
                  <YAxis
                    stroke="#627d98"
                    tick={{ fontSize: 11 }}
                    label={{ value: 'TPC (t/cm)', angle: -90, position: 'insideLeft', style: { fill: '#627d98', fontSize: 11 } }}
                  />
                  <Tooltip
                    contentStyle={{ background: '#ffffff', border: '1px solid #d0d5dd', borderRadius: '8px' }}
                    itemStyle={{ color: '#d9e2ec' }}
                    formatter={(v) => [`${v} t/cm`, 'TPC']}
                  />
                  <Line type="monotone" dataKey="tpc" stroke="#0ea5e9" strokeWidth={2} dot={{ fill: '#0ea5e9', r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
              <p className="text-xs text-navy-500 mt-2">
                Average TPC: {lightering_calculation?.avg_tpc_tonnes_per_cm} t/cm over {lightering_calculation?.draft_reduction_cm}cm reduction
              </p>
            </div>
          )}

          {/* Cost Comparison */}
          <div className="card">
            <h3 className="text-white font-semibold text-sm mb-3">Cost Comparison</h3>
            {costCompare.length > 0 && (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={costCompare} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d0d5dd" />
                  <XAxis dataKey="option" stroke="#627d98" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#627d98" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: '#ffffff', border: '1px solid #d0d5dd', borderRadius: '8px' }}
                    formatter={(v) => [`$${v.toLocaleString()}`, 'Cost']}
                  />
                  <Bar dataKey="cost" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}

            {/* Lightering Cost Breakdown */}
            {lightering_cost && (
              <div className="mt-4 space-y-1 text-sm">
                <div className="flex justify-between text-navy-300">
                  <span>Feeder Vessel Hire</span>
                  <span>${lightering_cost.breakdown.feeder_vessel_hire?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-navy-300">
                  <span>STS Operation Cost</span>
                  <span>${lightering_cost.breakdown.sts_fixed_cost?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-navy-300">
                  <span>Cargo Loss Risk</span>
                  <span>${lightering_cost.breakdown.cargo_loss_cost?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-navy-300">
                  <span>STS Insurance</span>
                  <span>${lightering_cost.breakdown.sts_insurance?.toLocaleString()}</span>
                </div>
                <div className="border-t border-navy-600 pt-1 flex justify-between font-bold text-white">
                  <span>Total Lightering Cost</span>
                  <span className="text-ocean-400">${lightering_cost.total_cost_usd?.toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Weather Risk */}
      {weather_risk && (
        <div className="card">
          <h3 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-accent-yellow" />
            STS Weather Risk Assessment
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <p className="text-xs text-navy-400">Risk Level</p>
              <p className={`text-lg font-bold`} style={{ color: weather_risk.risk_color === 'green' ? '#10b981' : weather_risk.risk_color === 'yellow' ? '#f59e0b' : weather_risk.risk_color === 'orange' ? '#f97316' : '#ef4444' }}>
                {weather_risk.risk_level}
              </p>
            </div>
            <div>
              <p className="text-xs text-navy-400">Delay Probability</p>
              <p className="text-lg font-bold text-white">{(weather_risk.weather_delay_probability * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-navy-400">Available Days/Month</p>
              <p className="text-lg font-bold text-white">{weather_risk.estimated_available_days}</p>
            </div>
            <div>
              <p className="text-xs text-navy-400">Wave Threshold</p>
              <p className="text-lg font-bold text-white">{weather_risk.wave_height_threshold_m}m Hs</p>
            </div>
          </div>
          <p className="text-sm text-navy-300 mt-3">{weather_risk.recommendation}</p>
        </div>
      )}
    </div>
  );
}
