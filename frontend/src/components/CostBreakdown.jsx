import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';
import { DollarSign, Ship } from 'lucide-react';

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

export default function CostBreakdown({ costAnalysis, vesselComparison }) {
  if (!costAnalysis) return <p className="text-navy-400">No cost data available.</p>;

  const { breakdown, total_cost_usd, cost_per_tonne_usd, route_info, vessel_info, voyage_plan } = costAnalysis;

  // Pie chart data
  const pieData = [
    { name: 'Freight', value: breakdown.freight_cost },
    { name: 'Port Charges', value: breakdown.port_charges.total },
    { name: 'Waiting Cost', value: breakdown.waiting_cost.cost },
    { name: 'Demurrage', value: breakdown.demurrage.cost },
    { name: 'Weather Risk', value: breakdown.weather_disruption.cost },
    { name: 'Canal Fees', value: breakdown.canal_fees.cost },
    { name: 'Insurance', value: breakdown.insurance.cost },
    { name: 'Bunker', value: breakdown.bunker.cost },
  ].filter((d) => d.value > 0);

  // Vessel comparison bar chart data
  const vesselBarData = vesselComparison?.options?.slice(0, 5).map((opt) => ({
    name: opt.vessel,
    total: opt.cost_per_tonne_usd,
    freight: opt.breakdown.freight_cost / vesselComparison.cargo_quantity,
    port: opt.breakdown.port_charges.total / vesselComparison.cargo_quantity,
    waiting: opt.breakdown.waiting_cost.cost / vesselComparison.cargo_quantity,
    bunker: opt.breakdown.bunker.cost / vesselComparison.cargo_quantity,
    other: (
      (opt.breakdown.demurrage.cost +
        opt.breakdown.weather_disruption.cost +
        opt.breakdown.canal_fees.cost +
        opt.breakdown.insurance.cost) /
      vesselComparison.cargo_quantity
    ),
  })) || [];

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="bg-navy-800 border border-navy-600 rounded-lg p-3 shadow-xl">
        {payload.map((p, i) => (
          <p key={i} className="text-xs" style={{ color: p.color }}>
            {p.name}: ${p.value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card glow-blue">
          <p className="text-xs text-navy-400">Total Delivered Cost</p>
          <p className="text-xl font-bold text-white">${total_cost_usd?.toLocaleString()}</p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">Cost Per Tonne</p>
          <p className="text-xl font-bold text-ocean-400">${cost_per_tonne_usd?.toFixed(2)}</p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">Route</p>
          <p className="text-sm font-bold text-white">{route_info?.origin} → {route_info?.destination}</p>
          <p className="text-xs text-navy-500">{route_info?.distance_nm} nm | {route_info?.voyage_days} days</p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">Vessel</p>
          <p className="text-sm font-bold text-white">{vessel_info?.class} ({vessel_info?.subtype})</p>
          <p className="text-xs text-navy-500">{vessel_info?.dwt?.toLocaleString()} DWT</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Cost Breakdown Pie */}
        <div className="card">
          <h3 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-ocean-400" />
            Cost Component Breakdown
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
                contentStyle={{ background: '#ffffff', border: '1px solid #d0d5dd', borderRadius: '8px' }}
                itemStyle={{ color: '#d9e2ec' }}
              />
              <Legend
                wrapperStyle={{ fontSize: '11px', color: '#9fb3c8' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Detailed Breakdown Table */}
        <div className="card">
          <h3 className="text-white font-semibold text-sm mb-1">Detailed Breakdown</h3>
          {voyage_plan?.voyages > 1 && (
            <p className="text-xs text-navy-500 mb-3">
              Cost total covers {voyage_plan.voyages} voyages; component rows below are shown per voyage.
            </p>
          )}
          <div className="space-y-2 text-sm">
            <Row label="Freight Cost" value={breakdown.freight_cost} />
            <Row label="Loading Port Charges" value={breakdown.port_charges.loading} sub />
            <Row label="Discharge Port Charges" value={breakdown.port_charges.discharge} sub />
            <Row label={`Waiting Time (${breakdown.waiting_cost.total_wait_days}d)`} value={breakdown.waiting_cost.cost} />
            <Row label={`Demurrage (${breakdown.demurrage.demurrage_days}d)`} value={breakdown.demurrage.cost} />
            <Row label={`Weather Disruption (${breakdown.weather_disruption.expected_delay_days}d exp.)`} value={breakdown.weather_disruption.cost} />
            {breakdown.canal_fees.cost > 0 && (
              <Row label={`Canal Fees (${breakdown.canal_fees.canal})`} value={breakdown.canal_fees.cost} />
            )}
            <Row label="Insurance" value={breakdown.insurance.cost} />
            <Row label={`Bunker (${breakdown.bunker.fuel_consumption_mt}MT)`} value={breakdown.bunker.cost} />
            <div className="border-t border-navy-600 pt-2 mt-2">
              <Row label="TOTAL" value={total_cost_usd} bold />
            </div>
          </div>
        </div>
      </div>

      {/* Vessel Comparison */}
      {vesselBarData.length > 0 && (
        <div className="card">
          <h3 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
            <Ship className="w-4 h-4 text-ocean-400" />
            Vessel Option Comparison (Cost per Tonne)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={vesselBarData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d0d5dd" />
              <XAxis dataKey="name" stroke="#627d98" tick={{ fontSize: 10 }} />
              <YAxis stroke="#627d98" tick={{ fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="freight" stackId="a" fill="#0ea5e9" name="Freight" />
              <Bar dataKey="port" stackId="a" fill="#10b981" name="Port" />
              <Bar dataKey="waiting" stackId="a" fill="#f59e0b" name="Waiting" />
              <Bar dataKey="bunker" stackId="a" fill="#8b5cf6" name="Bunker" />
              <Bar dataKey="other" stackId="a" fill="#ef4444" name="Other" />
            </BarChart>
          </ResponsiveContainer>
          {vesselComparison?.recommended && (
            <p className="text-xs text-accent-green mt-2">
              ✓ Recommended: {vesselComparison.recommended.vessel} at ${vesselComparison.recommended.cost_per_tonne_usd?.toFixed(2)}/tonne
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Row({ label, value, bold, sub }) {
  return (
    <div className={`flex justify-between ${sub ? 'pl-4' : ''} ${bold ? 'font-bold text-white' : 'text-navy-200'}`}>
      <span className={sub ? 'text-navy-400 text-xs' : ''}>{label}</span>
      <span className={bold ? 'text-ocean-400' : ''}>
        ${value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </span>
    </div>
  );
}
