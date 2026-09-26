import React, { useEffect, useMemo, useState } from 'react';
import { fullAnalysis } from '../api';
import ForecastChart from './ForecastChart';
import CostBreakdown from './CostBreakdown';
import LighteringAnalysis from './LighteringAnalysis';
import DecisionPanel from './DecisionPanel';
import RiskIndicators from './RiskIndicators';
import VesselRecommendation from './VesselRecommendation';
import { Search, Loader2, BarChart3, TrendingUp, Anchor, AlertTriangle } from 'lucide-react';

export default function Dashboard({ routes }) {
  const [form, setForm] = useState({
    cargo_quantity_tonnes: 120000,
    cargo_material: 'Coal',
    origin_region: 'Australia',
    destination_port: 'Paradip',
    route_code: 'AUS_PAR',
    contract_months: 6,
    loading_date_month: new Date().getMonth() + 1,
    cargo_value_per_tonne: 120,
    bunker_price_per_tonne: 580,
    proposed_charter_rate: '',
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('forecast');

  const origins = useMemo(
    () => [...new Set(routes.map((r) => r.origin_region))],
    [routes]
  );

  const destinations = useMemo(
    () => [...new Set(
      routes
        .filter((r) => r.origin_region === form.origin_region)
        .map((r) => r.destination)
    )],
    [routes, form.origin_region]
  );

  const selectedRoute = useMemo(
    () => routes.find(
      (r) =>
        r.origin_region === form.origin_region &&
        r.destination === form.destination_port
    ),
    [routes, form.origin_region, form.destination_port]
  );

  useEffect(() => {
    if (!routes.length) return;
    const first = routes[0];
    setForm((prev) => ({
      ...prev,
      origin_region: prev.origin_region && routes.some((r) => r.origin_region === prev.origin_region)
        ? prev.origin_region
        : first.origin_region,
    }));
  }, [routes]);

  useEffect(() => {
    if (!destinations.length) return;
    const valid = destinations.includes(form.destination_port);
    if (!valid) {
      const firstDest = destinations[0];
      const route = routes.find(
        (r) => r.origin_region === form.origin_region && r.destination === firstDest
      );
      setForm((prev) => ({
        ...prev,
        destination_port: firstDest,
        route_code: route?.route_code || prev.route_code,
      }));
    } else if (selectedRoute?.route_code && selectedRoute.route_code !== form.route_code) {
      setForm((prev) => ({ ...prev, route_code: selectedRoute.route_code }));
    }
  }, [destinations, form.destination_port, form.origin_region, selectedRoute, routes, form.route_code]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleOriginChange = (e) => {
    const origin = e.target.value;
    const firstDest = routes.find((r) => r.origin_region === origin)?.destination || '';
    const route = routes.find(
      (r) => r.origin_region === origin && r.destination === firstDest
    );
    setForm((prev) => ({
      ...prev,
      origin_region: origin,
      destination_port: firstDest,
      route_code: route?.route_code || '',
    }));
  };

  const handleDestinationChange = (e) => {
    const destination = e.target.value;
    const route = routes.find(
      (r) => r.origin_region === form.origin_region && r.destination === destination
    );
    setForm((prev) => ({
      ...prev,
      destination_port: destination,
      route_code: route?.route_code || prev.route_code,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const route = routes.find(
        (r) => r.origin_region === form.origin_region && r.destination === form.destination_port
      );
      if (!route) throw new Error('Please select a valid PS-26006 trade lane.');

      const payload = {
        cargo_quantity_tonnes: parseFloat(form.cargo_quantity_tonnes),
        cargo_material: form.cargo_material,
        route_code: route.route_code,
        contract_months: parseInt(form.contract_months),
        loading_date_month: parseInt(form.loading_date_month),
        cargo_value_per_tonne: parseFloat(form.cargo_value_per_tonne),
        bunker_price_per_tonne: parseFloat(form.bunker_price_per_tonne),
        proposed_charter_rate: form.proposed_charter_rate
          ? parseFloat(form.proposed_charter_rate)
          : null,
      };

      const res = await fullAnalysis(payload);
      setResults(res.data);
      setActiveTab('forecast');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
  ];

  const tabs = [
    { id: 'forecast', label: 'Rate Forecast', icon: TrendingUp },
    { id: 'cost', label: 'Cost Analysis', icon: BarChart3 },
    { id: 'lightering', label: 'Port / Lightering', icon: Anchor },
    { id: 'decision', label: 'Charter Decision', icon: AlertTriangle },
  ];

  return (
    <div>
      <form onSubmit={handleSubmit} className="card glow-blue mb-6">
        <h2 className="text-white font-semibold text-base mb-4 flex items-center gap-2">
          <Search className="w-5 h-5 text-ocean-400" />
          Voyage Analysis Parameters
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Field label="Cargo Quantity (tonnes)">
            <input
              type="number"
              name="cargo_quantity_tonnes"
              value={form.cargo_quantity_tonnes}
              onChange={handleChange}
              className={inputClass}
              min="1000"
              required
            />
          </Field>

          <Field label="Cargo Material">
            <select name="cargo_material" value={form.cargo_material} onChange={handleChange} className={inputClass}>
              <option value="Coal">Coal</option>
              <option value="Steel">Steel</option>
            </select>
          </Field>

          <Field label="Origin Region">
            <select name="origin_region" value={form.origin_region} onChange={handleOriginChange} className={inputClass}>
              {origins.map((origin) => (
                <option key={origin} value={origin}>{origin}</option>
              ))}
            </select>
          </Field>

          <Field label="East Coast Discharge Port">
            <select name="destination_port" value={form.destination_port} onChange={handleDestinationChange} className={inputClass}>
              {destinations.map((destination) => (
                <option key={destination} value={destination}>{destination}</option>
              ))}
            </select>
          </Field>

          <Field label="Contract Period (months)">
            <input type="number" name="contract_months" value={form.contract_months} onChange={handleChange} className={inputClass} min="1" max="24" />
          </Field>

          <Field label="Loading Month">
            <select name="loading_date_month" value={form.loading_date_month} onChange={handleChange} className={inputClass}>
              {months.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
            </select>
          </Field>

          <Field label="Cargo Value ($/tonne)">
            <input type="number" name="cargo_value_per_tonne" value={form.cargo_value_per_tonne} onChange={handleChange} className={inputClass} min="1" />
          </Field>

          <Field label="Bunker Price ($/tonne)">
            <input type="number" name="bunker_price_per_tonne" value={form.bunker_price_per_tonne} onChange={handleChange} className={inputClass} min="100" />
          </Field>
        </div>

        <div className="mt-4 flex items-end gap-4">
          <div className="flex-1 max-w-xs">
            <label className="block text-xs text-navy-400 mb-1">Proposed Charter Rate ($/tonne, optional)</label>
            <input
              type="number"
              name="proposed_charter_rate"
              value={form.proposed_charter_rate}
              onChange={handleChange}
              placeholder="Leave blank for auto-calculation"
              className={`${inputClass} placeholder-navy-500`}
              step="0.01"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !selectedRoute}
            className="px-8 py-2.5 bg-ocean-600 hover:bg-ocean-500 disabled:bg-navy-600 text-white font-medium rounded-lg transition-colors flex items-center gap-2 text-sm"
          >
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" />Analyzing...</> : <><Search className="w-4 h-4" />Run Full Analysis</>}
          </button>
        </div>

        {selectedRoute && (
          <p className="text-xs text-navy-500 mt-3">
            Trade lane: <span className="text-navy-300">{selectedRoute.name}</span> ·
            forecast uses the fixed synthetic historical series for <span className="text-navy-300">{selectedRoute.route_code}</span>.
          </p>
        )}
      </form>

      {error && (
        <div className="card border-accent-red/50 bg-accent-red/10 mb-6">
          <p className="text-accent-red font-medium text-sm">Analysis Error</p>
          <p className="text-navy-300 text-xs mt-1">{error}</p>
        </div>
      )}

      {loading && (
        <div className="card mb-6 text-center py-12">
          <Loader2 className="w-10 h-10 text-ocean-400 animate-spin mx-auto mb-4" />
          <p className="text-white font-medium">Running Analysis Engine</p>
          <p className="text-navy-400 text-sm mt-1">
            Selecting the vessel, training the forecast model and checking port constraints...
          </p>
        </div>
      )}

      {results && !loading && (
        <div>
          {results.vessel_recommendation && (
            <VesselRecommendation recommendation={results.vessel_recommendation} />
          )}

          {results.risk_summary && <RiskIndicators riskSummary={results.risk_summary} />}

          <div className="flex gap-1 mb-4 bg-navy-900 rounded-lg p-1 border border-navy-700">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-md text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-ocean-600 text-white shadow-lg'
                      : 'text-navy-400 hover:text-white hover:bg-navy-800'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          <div className="mt-4">
            {activeTab === 'forecast' && results.forecast && <ForecastChart forecast={results.forecast} />}
            {activeTab === 'cost' && (
              <CostBreakdown
                costAnalysis={results.cost_analysis}
                vesselComparison={results.vessel_comparison}
              />
            )}
            {activeTab === 'lightering' && results.lightering && <LighteringAnalysis lightering={results.lightering} />}
            {activeTab === 'decision' && results.charter_decision && <DecisionPanel decision={results.charter_decision} />}
          </div>

          {results.warnings && results.warnings.length > 0 && (
            <div className="card border-accent-yellow/30 mt-4">
              <p className="text-accent-yellow text-xs font-medium mb-1">Warnings</p>
              {results.warnings.map((w, i) => <p key={i} className="text-navy-400 text-xs">{w}</p>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const inputClass =
  'w-full bg-navy-800 border border-navy-600 rounded-lg px-3 py-2 text-white text-sm focus:border-ocean-500 focus:outline-none transition-colors';

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs text-navy-400 mb-1">{label}</label>
      {children}
    </div>
  );
}
