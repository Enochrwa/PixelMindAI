import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Receipt,
  FileText,
  CreditCard,
  User,
  ChevronDown,
  Zap,
} from 'lucide-react';
import { useState } from 'react';
import { clsx } from 'clsx';

interface NavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
}

interface NavGroup {
  label: string;
  icon: React.ReactNode;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Document Intelligence',
    icon: <FileText size={14} />,
    items: [
      { label: 'Receipt Scanner', to: '/tools/receipt-scanner', icon: <Receipt size={14} /> },
      { label: 'Invoice Reader', to: '/tools/invoice-reader', icon: <FileText size={14} /> },
      { label: 'Business Card Scanner', to: '/tools/business-card-scanner', icon: <CreditCard size={14} /> },
    ],
  },
];

const TOP_LINKS: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: <LayoutDashboard size={14} /> },
];

const BOTTOM_LINKS: NavItem[] = [
  { label: 'Account', to: '/account', icon: <User size={14} /> },
];

function NavLinkItem({ to, icon, label }: NavItem) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors',
          isActive
            ? 'bg-indigo-500/15 font-medium text-indigo-300'
            : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
        )
      }
    >
      <span className="shrink-0">{icon}</span>
      {label}
    </NavLink>
  );
}

function NavGroupSection({ group }: { group: NavGroup }) {
  const [open, setOpen] = useState(true);
  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-gray-500 hover:text-gray-400"
      >
        <span className="flex items-center gap-1.5">
          {group.icon}
          {group.label}
        </span>
        <ChevronDown
          size={12}
          className={clsx('transition-transform', open ? 'rotate-0' : '-rotate-90')}
        />
      </button>
      {open && (
        <div className="mt-1 space-y-0.5 pl-1">
          {group.items.map((item) => (
            <NavLinkItem key={item.to} {...item} />
          ))}
        </div>
      )}
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="flex h-full w-56 flex-col border-r border-gray-800 bg-gray-900 px-2 py-4">
      {/* Logo */}
      <div className="mb-4 px-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600">
            <Zap size={14} className="text-white" />
          </div>
          <span className="text-sm font-bold text-white">PixelMind AI</span>
        </div>
      </div>

      {/* Top nav */}
      <nav className="space-y-0.5">
        {TOP_LINKS.map((link) => (
          <NavLinkItem key={link.to} {...link} />
        ))}
      </nav>

      <div className="my-3 border-t border-gray-800" />

      {/* Tool groups */}
      <nav className="flex-1 space-y-4 overflow-y-auto">
        {NAV_GROUPS.map((group) => (
          <NavGroupSection key={group.label} group={group} />
        ))}
      </nav>

      <div className="border-t border-gray-800 pt-3">
        {BOTTOM_LINKS.map((link) => (
          <NavLinkItem key={link.to} {...link} />
        ))}
      </div>
    </aside>
  );
}
