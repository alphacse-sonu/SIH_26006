import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';
import { Shield, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

export default function DecisionPanel({ decision }) {
  if (!decision) return <p className="text-navy-400">No decision data available.</p>;

  const {
    decision: rec, confidence, reasoning, proposed_charter_rate,
    breakeven_rate, contract_months, npv_comparison, monte_carlo,
    monthly_forecast, risk_metrics, operational_insights,
  } = decision;

  const decisionColor = rec === 'CHARTER' ? '#10b981' : rec === 'SPOT' ? '#f59e0b' : '#627d98';
  const DecisionIcon = rec === 'CHARTER' ? CheckCircle : rec === 'SPOT' ? TrendingUp : AlertTriangle;

  // NPV comparison data
  const npvData = [
    { name: 'Charter NPV', value: npv_comparison?.charter_npv || 0, fill: '#10b981' },
    { name: 'Spot NPV (Mean)', value: npv_comparison?.spot_npv_mean || 0, fill: '#f59e0b' },
  ];

  // Monte Carlo histogram
  const histData = monte_carlo?.histogram?.counts?.map((count, i) => ({
    bin: `$${(monte_carlo.histogram.bin_edges[i] / 1000000).toFixed(1)}M`,
    count,
    binStart: monte_carlo.histogram.bin_edges[i],
    binEnd: monte_carlo.histogram.bin_edges[i + 1],
  })) || [];

  // Monthly forecast data
  const monthlyData = monthly_forecast?.rates?.map((rate, i) => ({
    month: `M${i + 1}`,
    rate,
    lower: monthly_forecast.ci_lower[i],
    upper: monthly_forecast.ci_upper[i],
    charter: proposed_charter_rate,
  })) || [];

  return (
    <div className="space-y-4">
      {/* Decision Banner */}
      <div className="card glow-green" style={{ borderColor: `${decisionColor}40` }}>
        <div className="flex items-center gap-4">
          <div className="p-4 rounded-xl" style={{ backgroundColor: `${decisionColor}15` }}>
            <DecisionIcon className="w-10 h-10" style={{ color: decisionColor }} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold" style={{ color: decisionColor }}>
                {rec === 'CHARTER' ? 'LOCK IN CHARTER' : rec === 'SPOT' ? 'STAY IN SPOT MARKET' : 'NEUTRAL'}
              </h2>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                confidence === 'HIGH' ? 'bg-accent-green/20 text-accent-green' :
                confidence === 'MODERATE' ? 'bg-accent-yellow/20 text-accent-yellow' :
                'bg-navy-600 text-navy-300'
              }`}>
                {confidence} Confidence
              </span>
            </div>
            <p className="text-navy-300 text-sm mt-2">{reasoning}</p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="card">
          <p className="text-xs text-navy-400">Charter Rate</p>
          <p className="text-lg font-bold text-white">${proposed_charter_rate?.toFixed(2)}</p>
          <p className="text-xs text-navy-500">per tonne</p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">Breakeven Rate</p>
          <p className="text-lg font-bold text-ocean-400">${breakeven_rate?.toFixed(2)}</p>
          <p className="text-xs text-navy-500">per tonne</p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">P(Charter Wins)</p>
          <p className="text-lg font-bold" style={{ color: decisionColor }}>
            {(risk_metrics?.probability_charter_cheaper * 100)?.toFixed(1)}%
          </p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">Expected Savings</p>
          <p className={`text-lg font-bold ${monte_carlo?.expected_savings_usd > 0 ? 'text-accent-green' : 'text-accent-red'}`}>
            ${Math.abs(monte_carlo?.expected_savings_usd || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-navy-500">{monte_carlo?.expected_savings_usd > 0 ? 'charter saves' : 'spot saves'}</p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">VaR (95%)</p>
          <p className="text-lg font-bold text-accent-red">
            ${Math.abs(risk_metrics?.var_95 || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-navy-500">worst case</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  
      {/* Market Timing + Idle Scenario */}
      {operational_insights && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card">
            <h3 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-ocean-400" />
              Optimal Market Entry Timing
            </h3>
            <p className="text-xs text-navy-400 mb-2">
              Signal: <span className="text-white font-semibold">{operational_insights.market_timing?.status?.replaceAll('_', ' ')}</span>
            </p>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <Metric label="Next 7-Day Avg" value={`$${operational_insights.market_timing?.next_7_day_average?.toFixed(2)}/t`} />
              <Metric label="Best 7-Day Avg" value={`$${operational_insights.market_timing?.best_7_day_average_rate?.toFixed(2)}/t`} />
              <Metric label="Best Window" value={`Day ${operational_insights.market_timing?.best_7_day_window_start}–${operational_insights.market_timing?.best_7_day_window_end}`} />
              <Metric label="Lower Quartile" value={`$${operational_insights.market_timing?.lower_quartile_threshold?.toFixed(2)}/t`} />
            </div>
            <p className="text-xs text-navy-300 mt-3">{operational_insights.market_timing?.guidance}</p>
          </div>

          <div className="card">
            <h3 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-accent-yellow" />
              Idle Scenario Management
            </h3>
            <p className="text-sm text-navy-300">
              {operational_insights.idle_management?.strategy}
            </p>
            {operational_insights.idle_management?.low_demand_windows?.length > 0 && (
              <div className="mt-3 space-y-1">
                {operational_insights.idle_management.low_demand_windows.map((w, i) => (
                  <div key={i} className="flex justify-between text-xs bg-navy-800/60 rounded px-2 py-1.5">
                    <span className="text-navy-400">Low-demand window</span>
                    <span className="text-white">Day {w.start_day}–{w.end_day} · ${w.avg_rate}/t</span>
                  </div>
                ))}
              </div>
            )}
            <p className="text-xs text-navy-500 mt-3">
              Trigger: {operational_insights.idle_management?.trigger}
            </p>
          </div>
        </div>
      )}

      {/* NPV Comparison */}
        <div className="card">
          <h3 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
            <Shield className="w-4 h-4 text-ocean-400" />
            NPV Comparison
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={npvData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d0d5dd" />
              <XAxis dataKey="name" stroke="#627d98" tick={{ fontSize: 11 }} />
              <YAxis stroke="#627d98" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`} />
              <Tooltip
                contentStyle={{ background: '#ffffff', border: '1px solid #d0d5dd', borderRadius: '8px' }}
                formatter={(v) => [`$${v.toLocaleString()}`, 'NPV']}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {npvData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-navy-400 mt-2">
            NPV Difference: <span className={npv_comparison?.npv_difference > 0 ? 'text-accent-green' : 'text-accent-red'}>
              ${Math.abs(npv_comparison?.npv_difference || 0).toLocaleString()}
            </span>
            {npv_comparison?.npv_difference > 0 ? ' (charter cheaper)' : ' (spot cheaper)'}
          </p>
        </div>

        {/* Monte Carlo Distribution */}
        <div className="card">
          <h3 className="text-white font-semibold text-sm mb-3">Monte Carlo Simulation ({monte_carlo?.n_simulations} paths)</h3>
          {histData.length > 0 && (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={histData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#d0d5dd" />
                <XAxis dataKey="bin" stroke="#627d98" tick={{ fontSize: 9 }} interval={2} />
                <YAxis stroke="#627d98" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: '#ffffff', border: '1px solid #d0d5dd', borderRadius: '8px' }}
                  formatter={(v) => [v, 'Simulations']}
                />
                <Bar dataKey="count" fill="#0ea5e9" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
          <p className="text-xs text-navy-400 mt-2">
            Spot cost distribution | Charter total: ${monte_carlo?.charter_total_cost?.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Monthly Rate Forecast vs Charter */}
      {monthlyData.length > 0 && (
        <div className="card">
          <h3 className="text-white font-semibold text-sm mb-3">Monthly Rate Forecast vs Charter Rate</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-navy-400 text-xs">
                  <th className="text-left py-2">Month</th>
                  <th className="text-right py-2">Forecast Rate</th>
                  <th className="text-right py-2">95% CI Lower</th>
                  <th className="text-right py-2">95% CI Upper</th>
                  <th className="text-right py-2">Charter Rate</th>
                  <th className="text-right py-2">Difference</th>
                </tr>
              </thead>
              <tbody>
                {monthlyData.map((m, i) => {
                  const diff = m.rate - proposed_charter_rate;
                  return (
                    <tr key={i} className="border-t border-navy-700">
                      <td className="py-2 text-navy-200">{m.month}</td>
                      <td className="py-2 text-right text-white">${m.rate?.toFixed(2)}</td>
                      <td className="py-2 text-right text-navy-400">${m.lower?.toFixed(2)}</td>
                      <td className="py-2 text-right text-navy-400">${m.upper?.toFixed(2)}</td>
                      <td className="py-2 text-right text-accent-green">${proposed_charter_rate?.toFixed(2)}</td>
                      <td className={`py-2 text-right font-medium ${diff > 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                        {diff > 0 ? '+' : ''}{diff?.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}


function Metric({ label, value }) {
  return (
    <div className="bg-navy-800/60 rounded-lg p-2">
      <p className="text-xs text-navy-400">{label}</p>
      <p className="text-sm font-semibold text-white mt-1">{value}</p>
    </div>
  );
}
