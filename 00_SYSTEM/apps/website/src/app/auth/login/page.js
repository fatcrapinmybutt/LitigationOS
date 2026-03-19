'use client';

import { useState } from 'react';
import Link from 'next/link';
import { signIn } from 'next-auth/react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await signIn('credentials', {
        email,
        password,
        redirect: false,
      });

      if (res?.error) {
        setError('Invalid email or password.');
      } else {
        window.location.href = '/dashboard';
      }
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-omega-bg flex flex-col">
      {/* Nav */}
      <nav className="border-b border-omega-border/40 bg-omega-bg/80 backdrop-blur">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
          <Link href="/" className="text-xl font-bold text-omega-text">
            Litigation<span className="text-omega-accent">OS</span>
          </Link>
          <Link href="/auth/signup" className="text-sm text-omega-muted hover:text-omega-text transition-colors">
            Create account
          </Link>
        </div>
      </nav>

      {/* Form */}
      <main className="flex-1 flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm">
          <h1 className="text-2xl font-bold text-omega-text text-center mb-2">Welcome back</h1>
          <p className="text-omega-muted text-sm text-center mb-8">Sign in to your LitigationOS account</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-omega-muted mb-1">Email</label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-omega-surface border border-omega-border text-omega-text placeholder:text-omega-muted/50 focus:outline-none focus:border-omega-accent transition-colors"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-omega-muted mb-1">Password</label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-omega-surface border border-omega-border text-omega-text placeholder:text-omega-muted/50 focus:outline-none focus:border-omega-accent transition-colors"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p className="text-omega-critical text-sm text-center">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-omega-accent text-white font-medium text-sm hover:bg-indigo-500 transition-colors disabled:opacity-50"
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-omega-muted">
            Don&apos;t have an account?{' '}
            <Link href="/auth/signup" className="text-omega-accent hover:underline">Sign up</Link>
          </p>
        </div>
      </main>
    </div>
  );
}
