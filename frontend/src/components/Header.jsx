import { Bars3Icon, BellIcon, UserCircleIcon } from '@heroicons/react/24/outline'

export default function Header({ onMenuClick }) {
  return (
    <header className="sticky top-0 z-10 bg-white shadow-sm">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center">
          <button
            type="button"
            className="lg:hidden -m-2.5 p-2.5 text-gray-700"
            onClick={onMenuClick}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
          <h1 className="ml-4 lg:ml-0 text-lg font-semibold text-gray-900">
            Freight Forecasting Dashboard
          </h1>
        </div>

        <div className="flex items-center gap-4">
          {/* Notifications */}
          <button className="relative p-2 text-gray-500 hover:text-gray-700">
            <BellIcon className="h-6 w-6" />
            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500" />
          </button>

          {/* User menu */}
          <div className="flex items-center gap-2">
            <UserCircleIcon className="h-8 w-8 text-gray-400" />
            <span className="hidden sm:block text-sm font-medium text-gray-700">
              Logistics Manager
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
