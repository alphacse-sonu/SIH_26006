import React from 'react';
import { AlertTriangle, CloudRain, Clock, Activity } from 'lucide-react';

export default function RiskIndicators({ riskSummary }) {
  if (!riskSummary) return null;

  const { overall_score, overall_level, overall_color, dimensions } = riskSummary;

  const colorMap = {
    green: { bg: 'bg-accent-green/10', text: 'text-accent-green', bar: 'bg-accent-green' },
    yellow: { bg: 'bg-accent-yellow/10', text: 'text-accent-yellow', bar: 'bg-accent-yellow' },
    orange: { bg: 'bg-accent-orange/10', text: 'text-accent-orange', bar: 'bg-accent-orange' },
    red: { bg: 'bg-accent-red/10', text: 'text-accent-red', bar: 'bg-accent-red' },
  };

  const colors = colorMap[overall_color] || colorMap.yellow;

  const getScoreColor = (score) => {
    if (score < 30) return colorMap.green;
    if (score < 55) return colorMap.yellow;
    if (score < 75) return colorMap.orange;
    return colorMap.red;
  };

  const dimensionIcons = {
    weather: CloudRain,
    congestion: Clock,
    volatility: Activity,
  };

  return (
    <div className={`card ${colors.bg} border-${overall_color === 'green' ? 'accent-green' : overall_color === 'yellow' ? 'accent-yellow' : overall_color === 'orange' ? 'accent-orange' : 'accent-red'}/30 mb-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertTriangle className={`w-5 h-5 ${colors.text}`} />
          <div>
            <span className="text-xs text-navy-400">Overall Risk</span>
            <div className="flex items-center gap-2">
              <span className={`text-lg font-bold ${colors.text}`}>{overall_level}</span>
              <span className="text-navy-400 text-sm">({overall_score}/100)</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {Object.entries(dimensions).map(([key, dim]) => {
            const Icon = dimensionIcons[key] || Activity;
            const sc = getScoreColor(dim.score);
            return (
              <div key={key} className="flex items-center gap-2">
                <Icon className={`w-4 h-4 ${sc.text}`} />
                <div>
                  <p className="text-xs text-navy-400">{dim.label}</p>
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-navy-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${sc.bar}`}
                        style={{ width: `${dim.score}%` }}
                      />
                    </div>
                    <span className={`text-xs font-medium ${sc.text}`}>{dim.score}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
