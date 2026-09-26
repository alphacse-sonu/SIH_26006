import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, ComposedChart, Legend,
} from 'recharts';
import { TrendingUp, Info } from 'lucide-react';

export default function ForecastChart({ forecast }) {
  if (!forecast) return null;

  const { forecasts, confidence_intervals, historical_rates, last_known_rate, training_metrics, model_info } = forecast;
  const ci80 = confidence_intervals?.ci_80;
  const ci95 = confidence_intervals?.ci_95;

  // Build chart data: historical + forecast
  const chartData = [];

  // Last 60 days of historical
  const histSlice = historical_rates.slice(-60);
  histSlice.forEach((rate, i) => {
    chartData.push({
      day: i - histSlice.length,
      label: `Day ${i - histSlice.length}`,
      historical: rate,
      type: 'historical',
    });
  });

  // Forecasts
  forecasts.forEach((rate, i) => {
    chartData.push({
      day: i + 1,
      label: `Day +${i + 1}`,
      forecast: rate,
      ci80_lower: ci80?.lower?.[i],
      ci80_upper: ci80?.upper?.[i],
      ci95_lower: ci95?.lower?.[i],
      ci95_upper: ci95?.upper?.[i],
      type: 'forecast',
    });
  });

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const data = payload[0]?.payload;
    return (
      <div className="bg-navy-800 border border-navy-600 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-navy-400 mb-1">{data.label}</p>
        {data.historical !== undefined && (
          <p className="text-sm text-ocean-400">Rate: <span className="font-bold">${data.historical?.toFixed(2)}</span></p>
        )}
        {data.forecast !== undefined && (
          <>
            <p className="text-sm text-accent-green">Forecast: <span className="font-bold">${data.forecast?.toFixed(2)}</span></p>
            {data.ci80_lower !== undefined && (
              <p className="text-xs text-navy-400 mt-1">80% CI: ${data.ci80_lower?.toFixed(2)} - ${data.ci80_upper?.toFixed(2)}</p>
            )}
            {data.ci95_lower !== undefined && (
              <p className="text-xs text-navy-400">95% CI: ${data.ci95_lower?.toFixed(2)} - ${data.ci95_upper?.toFixed(2)}</p>
            )}
          </>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card">
          <p className="text-xs text-navy-400">Current Rate</p>
          <p className="text-xl font-bold text-white">${last_known_rate}</p>
          <p className="text-xs text-navy-500">per tonne</p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">30-Day Forecast</p>
          <p className="text-xl font-bold text-accent-green">
            ${forecasts[Math.min(29, forecasts.length - 1)]?.toFixed(2)}
          </p>
          <p className="text-xs text-navy-500">
            {forecasts[29] > last_known_rate ? '↑' : '↓'}
            {Math.abs(((forecasts[Math.min(29, forecasts.length - 1)] - last_known_rate) / last_known_rate) * 100).toFixed(1)}%
          </p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">Model MAE</p>
          <p className="text-xl font-bold text-ocean-400">{training_metrics?.mae?.toFixed(3)}</p>
          <p className="text-xs text-navy-500">Mean Absolute Error</p>
        </div>
        <div className="card">
          <p className="text-xs text-navy-400">Model MAPE</p>
          <p className="text-xl font-bold text-ocean-400">{training_metrics?.mape?.toFixed(2)}%</p>
          <p className="text-xs text-navy-500">Mean Abs % Error</p>
        </div>
      </div>

      {/* Chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-ocean-400" />
            Freight Rate Forecast
          </h3>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-ocean-400 inline-block"></span> Historical
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-accent-green inline-block"></span> Forecast
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-accent-green/20 inline-block rounded"></span> 80% CI
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-accent-green/10 inline-block rounded"></span> 95% CI
            </span>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d0d5dd" />
            <XAxis
              dataKey="day"
              stroke="#64748b"
              tick={{ fontSize: 11 }}
              tickFormatter={(v) => v === 0 ? 'Today' : v > 0 ? `+${v}d` : `${v}d`}
            />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
            <Tooltip content={<CustomTooltip />} />

            {/* 95% CI band */}
            <Area
              dataKey="ci95_upper"
              stroke="none"
              fill="#10b981"
              fillOpacity={0.05}
              connectNulls={false}
            />
            <Area
              dataKey="ci95_lower"
              stroke="none"
              fill="#ffffff"
              fillOpacity={1}
              connectNulls={false}
            />

            {/* 80% CI band */}
            <Area
              dataKey="ci80_upper"
              stroke="none"
              fill="#10b981"
              fillOpacity={0.1}
              connectNulls={false}
            />
            <Area
              dataKey="ci80_lower"
              stroke="none"
              fill="#ffffff"
              fillOpacity={1}
              connectNulls={false}
            />

            {/* Historical line */}
            <Line
              dataKey="historical"
              stroke="#38bdf8"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
            />

            {/* Forecast line */}
            <Line
              dataKey="forecast"
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="5 3"
              dot={false}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Model Info */}
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <Info className="w-4 h-4 text-navy-400" />
          <h4 className="text-sm text-navy-300 font-medium">Model Details</h4>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div>
            <span className="text-navy-500">Ensemble:</span>
            <span className="text-navy-200 ml-1">{model_info?.ensemble}</span>
          </div>
          <div>
            <span className="text-navy-500">Features:</span>
            <span className="text-navy-200 ml-1">{model_info?.features_used}</span>
          </div>
          <div>
            <span className="text-navy-500">CI Method:</span>
            <span className="text-navy-200 ml-1">{model_info?.confidence_method}</span>
          </div>
          <div>
            <span className="text-navy-500">Training Samples:</span>
            <span className="text-navy-200 ml-1">{training_metrics?.train_samples?.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
