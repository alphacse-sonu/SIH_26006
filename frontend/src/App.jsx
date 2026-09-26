import React, { useState, useEffect } from 'react';
import { getRoutes, getHealth } from './api';
import Dashboard from './components/Dashboard';
import { Ship, Anchor, Activity } from 'lucide-react';

export default function App() {
  const [routes, setRoutes] = useState([]);
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    const init = async () => {
      try {
        const healthRes = await getHealth();
        setBackendStatus(healthRes.data.data_generated ? 'ready' : 'no-data');
        const routesRes = await getRoutes();
        setRoutes(routesRes.data);
      } catch (err) {
        setBackendStatus('offline');
        console.error('Backend connection failed:', err);
      }
    };
    init();
  }, []);

  return (
    <div className="min-h-screen bg-navy-950">
      {/* Header */}
      <header className="border-b border-navy-700 bg-navy-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-ocean-600/20 rounded-lg">
              <Ship className="w-6 h-6 text-ocean-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">
                Maritime Chartering Decision Platform
              </h1>
              <p className="text-xs text-navy-400">SIH 2026 | SAIL Voyage Planning Engine</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <Anchor className="w-4 h-4 text-navy-400" />
              <span className="text-navy-300">{routes.length} Trade Lanes</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                backendStatus === 'ready' ? 'bg-accent-green' :
                backendStatus === 'no-data' ? 'bg-accent-yellow' :
                backendStatus === 'checking' ? 'bg-accent-yellow animate-pulse' :
                'bg-accent-red'
              }`} />
              <span className="text-xs text-navy-400">
                {backendStatus === 'ready' ? 'Engine Ready' :
                 backendStatus === 'no-data' ? 'Generate Data First' :
                 backendStatus === 'checking' ? 'Connecting...' :
                 'Backend Offline'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Backend offline warning */}
      {backendStatus === 'offline' && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          <div className="card border-accent-red/50 bg-accent-red/10">
            <p className="text-accent-red font-medium">Backend is offline</p>
            <p className="text-navy-300 text-sm mt-1">
              Start the backend server: <code className="bg-navy-800 px-2 py-0.5 rounded text-ocean-400">cd backend && uvicorn main:app --reload</code>
            </p>
          </div>
        </div>
      )}

      {backendStatus === 'no-data' && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          <div className="card border-accent-yellow/50 bg-accent-yellow/10">
            <p className="text-accent-yellow font-medium">Training data not generated</p>
            <p className="text-navy-300 text-sm mt-1">
              Run: <code className="bg-navy-800 px-2 py-0.5 rounded text-ocean-400">cd backend && python data/generate_synthetic_data.py</code>
            </p>
          </div>
        </div>
      )}

      {/* Main Dashboard */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Dashboard routes={routes} />
      </main>

      {/* Footer */}
      <footer className="border-t border-navy-800 mt-12 py-4">
        <div className="max-w-7xl mx-auto px-4 flex items-center justify-between text-xs text-navy-500">
          <span>Maritime Chartering Decision Platform v1.0</span>
          <span>SIH 2026 | Team IIT ISM Dhanbad</span>
        </div>
      </footer>
    </div>
  );
}
