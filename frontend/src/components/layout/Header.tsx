import { useAuthStore } from '@/stores/authStore';
import { LogOut, Zap } from 'lucide-react';

export function Header() {
  const { logout } = useAuthStore();
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-800 bg-gray-900 px-6">
      <div />
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-full border border-indigo-700/40 bg-indigo-700/10 px-3 py-1.5 text-sm">
          <Zap size={14} className="text-indigo-400" />
          <span className="text-indigo-300 font-medium">Credits</span>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-gray-400 transition hover:text-gray-100"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </header>
  );
}
