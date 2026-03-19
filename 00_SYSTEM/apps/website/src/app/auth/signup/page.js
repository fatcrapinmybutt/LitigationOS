'use client';

import { useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { signIn } from 'next-auth/react';

const PLANS = [
  { id: 'free',       label: 'Free — $0 / mo' },
  { id: 'lite',       label: 'Lite — $29 / mo' },
  { id: 'pro',        label: 'Pro — $99 / mo' },
  { id: 'enterprise', label: 'Enterprise — $299 / mo' },
];

export default function SignupPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-omega-bg" />}>
      <SignupForm />
    </Suspense>
  );
}

function SignupForm() {
  const params = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [plan, setPlan] = useState(params.get('plan') || 'free');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // TODO: call a real signup API to create user in DB
      // For now, sign the user in via NextAuth credentials (skeleton)
      const res = await signIn('credentials', {
        email,
        password,
        redirect: false,
      });

      if (res?.error) {
        setError('Could not create account. Please try again.');
        setLoading(false);
        return;
      }

      // If paid plan, redirect to Stripe checkout
      if (plan !== 'free') {
        const checkout = await fetch('/api/checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tier: plan, email }),
        });
        const data = await checkout.json();
        if (data.url) {
          window.location.href = data.url;
          return;
        }
      }

      window.location.href = '/dashboard';
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
          <Link href="/auth/login" className="text-sm text-omega-muted hover:text-omega-text transition-colors">
            Log in
          </Link>
        </div>
      </nav>

      {/* Form */}
      <main className="flex-1 flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm">
          <h1 className="text-2xl font-bold text-omega-text text-center mb-2">Create your account</h1>
          <p className="text-omega-muted text-sm text-center mb-8">Get started with LitigationOS in seconds</p>

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
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-omega-surface border border-omega-border text-omega-text placeholder:text-omega-muted/50 focus:outline-none focus:border-omega-accent transition-colors"
                placeholder="Min 8 characters"
              />
            </div>

            <div>
              <label htmlFor="plan" className="block text-sm font-medium text-omega-muted mb-1">Plan</label>
              <select
                id="plan"
                value={plan}
                onChange={(e) => setPlan(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-omega-surface border border-omega-border text-omega-text focus:outline-none focus:border-omega-accent transition-colors"
              >
                {PLANS.map((p) => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>
            </div>

            {error && (
              <p className="text-omega-critical text-sm text-center">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-omega-accent text-white font-medium text-sm hover:bg-indigo-500 transition-colors disabled:opacity-50"
            >
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-omega-muted">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-omega-accent hover:underline">Log in</Link>
          </p>

          <p className="mt-4 text-center text-xs text-omega-muted/60">
            By signing up you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </main>
    </div>
  );
}
