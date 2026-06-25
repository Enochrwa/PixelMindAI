import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, ScanText, Image, Sparkles,
  BarChart3, Sprout, Smile, CreditCard,
} from 'lucide-react';

const modules = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'OCR & Docs', to: '/tools?module=ocr', icon: ScanText },
  { label: 'Photo AI', to: '/tools?module=photo', icon: Image },
  { label: 'Creator Studio', to: '/tools?module=creator', icon: Sparkles },
  { label: 'Business Intel', to: '/tools?module=business', icon: BarChart3 },
  { label: 'Agriculture', to: '/tools?module=agriculture', icon: Sprout },
  { label: 'Entertainment', to: '/tools?module=entertainment', icon: Smile },
  { label: 'Billing', to: '/account', icon: CreditCard },
];

export function Sidebar() {
  return (
    <aside className="hidden w-64 flex-col border-r border-gray-800 bg-gray-900 lg:flex">
      <div className="flex h-16 items-center px-6">
        <span className="text-xl font-bold text-white">
          Pixel<span className="text-indigo-400">Mind</span>
        </span>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {modules.map(({ label, to, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-700/20 text-indigo-400'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
