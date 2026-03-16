/**
 * Top navigation bar with entity links.
 */
import { NavLink } from 'react-router-dom'
import { Database, Table } from 'lucide-react'
import type { EntityConfig } from '../types/config'

interface NavbarProps {
  entities: EntityConfig[]
}

export function Navbar({ entities }: NavbarProps) {
  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center gap-6">
          {/* Logo */}
          <div className="flex items-center gap-2 font-bold text-blue-600 text-lg shrink-0">
            <Database className="h-5 w-5" />
            <span>SheetManipulator</span>
          </div>

          {/* Entity links */}
          <div className="flex gap-1 overflow-x-auto">
            {entities.map((entity) => (
              <NavLink
                key={entity.name}
                to={`/entity/${entity.name}`}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`
                }
              >
                <Table className="h-4 w-4" />
                {entity.name}
              </NavLink>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}
