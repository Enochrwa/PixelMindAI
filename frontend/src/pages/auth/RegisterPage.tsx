import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import type { AuthTokens } from '@/types';

export function RegisterPage() {
  const [form, setForm] = useState({ email: '', username: '', password: '', full_name: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setTokens } = useAuthStore();
  const navigate = useNavigate();

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post<AuthTokens>('/auth/register', form);
      setTokens(data.access_token, data.refresh_token);
      void navigate('/dashboard');
    } catch {
      setError('Registration failed. Email or username may already be taken.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card p-8">
      <h2 className="mb-6 text-2xl font-bold text-white">Create account</h2>
      <p className="mb-4 text-sm text-gray-400">30 free credits on signup — no card required.</p>
      {error && (
        <div className="mb-4 rounded-lg border border-red-800 bg-red-900/20 p-3 text-sm text-red-400">
          {error}
        </div>
      )}
      <form onSubmit={(e) => { void handleSubmit(e); }} className="space-y-4">
        {[
          { key: 'full_name', label: 'Full name', type: 'text', placeholder: 'Jane Doe' },
          { key: 'email', label: 'Email', type: 'email', placeholder: 'you@example.com' },
          { key: 'username', label: 'Username', type: 'text', placeholder: 'janedoe' },
          { key: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
        ].map(({ key, label, type, placeholder }) => (
          <div key={key}>
            <label className="mb-1.5 block text-sm text-gray-300">{label}</label>
            <input type={type} value={form[key as keyof typeof form]}
              onChange={set(key)} className="input" placeholder={placeholder} required />
          </div>
        ))}
        <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-3">
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-gray-400">
        Already have an account?{' '}
        <Link to="/login" className="text-indigo-400 hover:text-indigo-300">Sign in</Link>
      </p>
    </div>
  );
}
