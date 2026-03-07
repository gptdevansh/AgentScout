/* ── App shell: sidebar + content area ────────────────────────────────── */

import { clsx } from 'clsx';
import {
  LayoutDashboard,
  MessageSquareText,
  Newspaper,
  History,
  Rocket,
  Search,
} from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/pipeline', label: 'Pipeline', icon: Rocket },
  { to: '/pipeline/runs', label: 'Run History', icon: History },
  { to: '/posts', label: 'Posts', icon: Newspaper },
];

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* ── Sidebar ──────────────────────────────────────────────────── */}
      <aside className="flex w-64 flex-col border-r border-gray-200 bg-white">
        {/* Brand */}
        <div className="flex h-16 items-center gap-3 border-b border-gray-100 px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
            <Search className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-bold text-gray-900">AgentScout</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                )
              }
            >
              <Icon className="h-5 w-5" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-gray-100 px-5 py-3 text-xs text-gray-400">
          <div className="flex items-center gap-1.5">
            <MessageSquareText className="h-3.5 w-3.5" />
            <span>AI-powered comment generation</span>
          </div>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <Outlet />
      </main>
    </div>
  );
}
