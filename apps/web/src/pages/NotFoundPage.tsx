import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-950 text-center">
      <h1 className="text-6xl font-bold text-white">404</h1>
      <p className="mt-4 text-gray-400">This page doesn&apos;t exist.</p>
      <Link to="/" className="btn-primary mt-8">Go home</Link>
    </div>
  );
}
