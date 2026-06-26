import { Outlet } from 'react-router-dom';

export function AuthLayout() {
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
