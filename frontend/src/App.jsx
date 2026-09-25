import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import FreightForecast from './pages/FreightForecast'
import MarketEntry from './pages/MarketEntry'
import VesselOptimization from './pages/VesselOptimization'
import PortAnalysis from './pages/PortAnalysis'
import RiskAssessment from './pages/RiskAssessment'
import Analytics from './pages/Analytics'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/forecast" element={<FreightForecast />} />
        <Route path="/market-entry" element={<MarketEntry />} />
        <Route path="/vessel-optimization" element={<VesselOptimization />} />
        <Route path="/ports" element={<PortAnalysis />} />
        <Route path="/risk" element={<RiskAssessment />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </Layout>
  )
}

export default App
