import { Link } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { useCurrentUser } from '@/hooks/useCurrentUser';
import { LogOut, Zap, ChevronRight } from 'lucide-react';

export function Header() {
  const { logout } = useAuthStore();
  const { data: user } = useCurrentUser();

  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-800 bg-gray-900 px-6">
      <div />
      <div className="flex items-center gap-3">
        {/* Credits badge — links to upgrade if low */}
        <Link
          to="/account"
          className="flex items-center gap-1.5 rounded-full border border-indigo-700/40 bg-indigo-700/10 px-3 py-1.5 text-sm transition hover:border-indigo-500/60 hover:bg-indigo-700/20"
        >
          <Zap size={13} className="text-indigo-400" />
          <span className="text-indigo-300 font-medium">
            {user ? `${user.credits_remaining} credits` : 'Credits'}
          </span>
          {user && user.credits_remaining < 5 && (
            <>
              <span className="mx-1 text-indigo-700">·</span>
              <span className="text-xs text-indigo-400/70 flex items-center gap-0.5">
                Upgrade <ChevronRight size={10} />
              </span>
            </>
          )}
        </Link>

        {/* User badge */}
        {user && (
          <span className="hidden sm:block text-xs text-gray-500 truncate max-w-[140px]">
            {user.email}
          </span>
        )}

        {/* Sign out */}
        <button
          onClick={logout}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-gray-400 transition hover:bg-gray-800 hover:text-gray-100"
          title="Sign out"
        >
          <LogOut size={15} />
          <span className="hidden sm:inline">Sign out</span>
        </button>
      </div>
    </header>
  );
}
