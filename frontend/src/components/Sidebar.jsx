import { NavLink } from 'react-router-dom'
import {
  HomeIcon,
  ChartBarIcon,
  ClockIcon,
  TruckIcon,
  MapPinIcon,
  ShieldExclamationIcon,
  PresentationChartLineIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Freight Forecast', href: '/forecast', icon: ChartBarIcon },
  { name: 'Market Entry', href: '/market-entry', icon: ClockIcon },
  { name: 'Vessel Optimization', href: '/vessel-optimization', icon: TruckIcon },
  { name: 'Port Analysis', href: '/ports', icon: MapPinIcon },
  { name: 'Risk Assessment', href: '/risk', icon: ShieldExclamationIcon },
  { name: 'Analytics', href: '/analytics', icon: PresentationChartLineIcon },
]

export default function Sidebar({ onClose }) {
  return (
    <div className="flex h-full flex-col bg-primary-900">
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4">
        <div className="flex items-center">
          <svg className="h-8 w-8 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3.5 18.5l.5 1.5h16l.5-1.5-8.5-3-8.5 3zM21 19H3l-1-3 10-3.5L22 16l-1 3z"/>
            <path d="M12 3l-4 9h8l-4-9zm0 2.5l2 4.5h-4l2-4.5z"/>
            <path d="M6 12h12v1H6z"/>
          </svg>
          <span className="ml-2 text-xl font-bold text-white">FreightCast</span>
        </div>
        {onClose && (
          <button onClick={onClose} className="lg:hidden text-white">
            <XMarkIcon className="h-6 w-6" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${
                isActive
                  ? 'bg-primary-800 text-white'
                  : 'text-primary-100 hover:bg-primary-800 hover:text-white'
              }`
            }
          >
            <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-primary-800 p-4">
        <div className="text-xs text-primary-300">
          <p>SIH 2026 - Problem ID: 26006</p>
          <p className="mt-1">Freight Forecasting Model</p>
        </div>
      </div>
    </div>
  )
}
