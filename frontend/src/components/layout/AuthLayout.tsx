import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

export function AuthLayout() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  // Already logged in — send to dashboard instead of showing auth forms
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-white">
            Pixel<span className="text-indigo-400">Mind</span> AI
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            The World&apos;s First Unified Visual Intelligence OS
          </p>
        </div>
        <Outlet />
      </div>
    </div>
  );
}
