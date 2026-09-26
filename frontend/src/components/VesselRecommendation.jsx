import React from 'react';
import { Ship, Ruler, PackageCheck, AlertTriangle } from 'lucide-react';

export default function VesselRecommendation({ recommendation }) {
  if (!recommendation) return null;

  if (!['FEASIBLE', 'FEASIBLE_SPLIT'].includes(recommendation.status) || !recommendation.recommended) {
    return (
      <div className="card border-accent-red/30 bg-accent-red/5 mb-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-accent-red mt-0.5" />
          <div>
            <h3 className="text-white font-semibold">No single-vessel solution found</h3>
            <p className="text-navy-300 text-sm mt-1">{recommendation.message}</p>
            <p className="text-navy-500 text-xs mt-2">
              Consider splitting the parcel into multiple voyages or selecting a different East Coast discharge port.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const v = recommendation.recommended;
  const origin = recommendation.port_constraints?.origin;
  const destination = recommendation.port_constraints?.destination;

  return (
    <div className="card glow-green border-accent-green/30 mb-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-start gap-3">
          <div className="p-3 rounded-xl bg-ocean-600/15">
            <Ship className="w-7 h-7 text-ocean-400" />
          </div>
          <div>
            <p className="text-xs text-navy-400">AI Vessel Recommendation</p>
            <h2 className="text-xl font-bold text-white">
              {v.class} <span className="text-ocean-400">({v.subtype})</span>
            </h2>
            <p className="text-sm text-navy-300 mt-1">{recommendation.explanation}</p>
            {recommendation.status === 'FEASIBLE_SPLIT' && (
              <p className="text-xs text-accent-yellow mt-2">
                Multi-voyage plan: {v.split_voyages} voyages × ~{v.per_voyage_cargo_tonnes?.toLocaleString()} tonnes.
              </p>
            )}
          </div>
        </div>
        <div className="px-3 py-2 rounded-lg bg-accent-green/10 border border-accent-green/20">
          <p className="text-xs text-navy-400">Suitability</p>
          <p className="text-lg font-bold text-accent-green">{v.feasibility_score}/100</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-4">
        <Metric icon={PackageCheck} label="Cargo" value={`${v.dwt?.toLocaleString()} DWT`} />
        <Metric icon={Ruler} label="Loaded Draft" value={`${v.estimated_loaded_draft_m} m`} />
        <Metric label="Route Draft Limit" value={`${v.route_draft_limit_m} m`} />
        <Metric label="Cargo Utilization" value={`${v.cargo_utilization_pct}%`} />
        <Metric label="Est. Turnaround" value={`${v.handling_days_est + v.expected_waiting_days} days`} />
      </div>

      <div className="mt-3 text-xs text-navy-500">
        Checked at both ports: {origin?.name} and {destination?.name} ·
        draft, LOA, beam and handling capability.
      </div>
    </div>
  );
}

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="bg-navy-800/60 rounded-lg p-2.5">
      <div className="flex items-center gap-1.5">
        {Icon && <Icon className="w-3.5 h-3.5 text-ocean-400" />}
        <p className="text-xs text-navy-400">{label}</p>
      </div>
      <p className="text-sm font-semibold text-white mt-1">{value}</p>
    </div>
  );
}
