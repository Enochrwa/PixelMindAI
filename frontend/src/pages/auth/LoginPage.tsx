import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import type { AuthTokens } from '@/types';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setTokens } = useAuthStore();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post<AuthTokens>('/auth/login', { email, password });
      setTokens(data.access_token, data.refresh_token);
      void navigate('/dashboard');
    } catch {
      setError('Invalid email or password');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card p-8">
      <h2 className="mb-6 text-2xl font-bold text-white">Sign in</h2>
      {error && (
        <div className="mb-4 rounded-lg border border-red-800 bg-red-900/20 p-3 text-sm text-red-400">
          {error}
        </div>
      )}
      <form
        onSubmit={(e) => {
          void handleSubmit(e);
        }}
        className="space-y-4"
      >
        <div>
          <label className="mb-1.5 block text-sm text-gray-300">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input"
            placeholder="you@example.com"
            required
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm text-gray-300">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
            placeholder="••••••••"
            required
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-3">
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-gray-400">
        No account?{' '}
        <Link to="/register" className="text-indigo-400 hover:text-indigo-300">
          Create one free
        </Link>
      </p>
    </div>
  );
}
