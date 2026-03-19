'use client';

import { useState } from 'react';
import Link from 'next/link';

/* ─── Tier data (mirrors src/lib/stripe.js) ─── */
const TIERS = [
  {
    id: 'free',
    name: 'Free',
    monthly: 0,
    annual: 0,
    tag: null,
    limits: { cases: '1 case', storage: '500 MB' },
    features: [
      'Single case management',
      'Basic timeline view',
      'Document upload (500 MB)',
      'Community support',
    ],
    cta: 'Get Started',
    highlight: false,
  },
  {
    id: 'lite',
    name: 'Lite',
    monthly: 29,
    annual: 23.20,
    tag: null,
    limits: { cases: '1 case', storage: '5 GB' },
    features: [
      'Single case management',
      'OMEGA credibility scoring',
      'Evidence contradiction detection',
      'Document upload (5 GB)',
      'Email support',
    ],
    cta: 'Start Lite',
    highlight: false,
  },
  {
    id: 'pro',
    name: 'Pro',
    monthly: 99,
    annual: 79.20,
    tag: 'Most Popular',
    limits: { cases: '5 cases', storage: '25 GB' },
    features: [
      'Up to 5 cases',
      'Full AI analysis suite',
      'Relationship graph visualization',
      'Multi-forum filing support',
      'Court document generation',
      'Priority support',
    ],
    cta: 'Start Pro',
    highlight: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    monthly: 299,
    annual: 239.20,
    tag: null,
    limits: { cases: 'Unlimited', storage: '100 GB' },
    features: [
      'Unlimited cases',
      'Full REST API access',
      'White-label branding',
      'Custom integrations',
      'Dedicated account manager',
      'SSO & team management',
      '99.9 % SLA',
    ],
    cta: 'Contact Sales',
    highlight: false,
  },
];

/* ─── Feature comparison rows ─── */
const COMPARISON = [
  { label: 'Cases',                free: '1',      lite: '1',      pro: '5',      enterprise: 'Unlimited' },
  { label: 'Storage',              free: '500 MB',  lite: '5 GB',   pro: '25 GB',  enterprise: '100 GB' },
  { label: 'OMEGA Scoring',        free: false,     lite: true,     pro: true,     enterprise: true },
  { label: 'AI Analysis',          free: false,     lite: false,    pro: true,     enterprise: true },
  { label: 'Graph Visualization',  free: false,     lite: false,    pro: true,     enterprise: true },
  { label: 'Multi-forum Filing',   free: false,     lite: false,    pro: true,     enterprise: true },
  { label: 'Document Generation',  free: false,     lite: false,    pro: true,     enterprise: true },
  { label: 'REST API Access',      free: false,     lite: false,    pro: false,    enterprise: true },
  { label: 'White-label',          free: false,     lite: false,    pro: false,    enterprise: true },
  { label: 'SSO & Teams',          free: false,     lite: false,    pro: false,    enterprise: true },
  { label: 'Support',              free: 'Community', lite: 'Email', pro: 'Priority', enterprise: 'Dedicated' },
  { label: 'SLA',                  free: '—',       lite: '—',      pro: '—',      enterprise: '99.9 %' },
];

/* ─── FAQ ─── */
const FAQS = [
  {
    q: 'Can I switch plans later?',
    a: 'Yes. Upgrade or downgrade at any time from your dashboard. Changes take effect immediately and billing is prorated.',
  },
  {
    q: 'Is there a free trial?',
    a: 'The Free tier is available forever with no credit card required. Paid plans include a 14-day money-back guarantee.',
  },
  {
    q: 'What payment methods do you accept?',
    a: 'We accept all major credit and debit cards through Stripe. Enterprise customers can also pay via invoice.',
  },
  {
    q: 'How does annual billing work?',
    a: 'Annual plans are billed once per year at a 20 % discount compared to monthly pricing. You can switch to annual billing at any time.',
  },
  {
    q: 'Is my data secure?',
    a: 'All data is encrypted at rest and in transit. We never share case data with third parties. Enterprise plans support single sign-on and custom data retention policies.',
  },
  {
    q: 'Can I cancel anytime?',
    a: 'Absolutely. Cancel from your dashboard and keep access until the end of your billing period. No cancellation fees.',
  },
];

/* ─── Helpers ─── */
function Check() {
  return (
    <svg className="w-5 h-5 text-omega-success flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}
function Cross() {
  return (
    <svg className="w-5 h-5 text-omega-muted/40 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

function CellValue({ value }) {
  if (value === true) return <Check />;
  if (value === false) return <Cross />;
  return <span className="text-omega-text text-sm">{value}</span>;
}

/* ─── Page ─── */
export default function PricingPage() {
  const [annual, setAnnual] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);

  async function handleCheckout(tierId) {
    if (tierId === 'free') {
      window.location.href = '/auth/signup?plan=free';
      return;
    }
    if (tierId === 'enterprise') {
      window.location.href = 'mailto:sales@litigationos.com?subject=Enterprise%20Inquiry';
      return;
    }
    try {
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: tierId, billing: annual ? 'annual' : 'monthly' }),
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
    } catch (err) {
      console.error('Checkout error', err);
    }
  }

  return (
    <div className="min-h-screen bg-omega-bg">
      {/* ── Nav ── */}
      <nav className="border-b border-omega-border/40 bg-omega-bg/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
          <Link href="/" className="text-xl font-bold text-omega-text">
            Litigation<span className="text-omega-accent">OS</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="text-sm text-omega-muted hover:text-omega-text transition-colors">
              Log in
            </Link>
            <Link href="/auth/signup" className="text-sm px-4 py-2 rounded-lg bg-omega-accent text-white hover:bg-indigo-500 transition-colors">
              Sign up
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Header ── */}
      <header className="text-center pt-20 pb-12 px-6">
        <h1 className="text-4xl md:text-5xl font-extrabold text-omega-text mb-4">
          Simple, transparent pricing
        </h1>
        <p className="text-omega-muted text-lg max-w-2xl mx-auto mb-8">
          Start free. Upgrade when you need more power. Every plan includes core litigation management.
        </p>

        {/* Toggle */}
        <div className="flex items-center justify-center gap-3">
          <span className={`text-sm ${!annual ? 'text-omega-text' : 'text-omega-muted'}`}>Monthly</span>
          <button
            onClick={() => setAnnual(!annual)}
            className={`relative w-14 h-7 rounded-full transition-colors ${annual ? 'bg-omega-accent' : 'bg-omega-border'}`}
            aria-label="Toggle annual billing"
          >
            <span className={`absolute top-0.5 left-0.5 w-6 h-6 rounded-full bg-white shadow transition-transform ${annual ? 'translate-x-7' : ''}`} />
          </button>
          <span className={`text-sm ${annual ? 'text-omega-text' : 'text-omega-muted'}`}>
            Annual <span className="text-omega-success font-medium">(-20 %)</span>
          </span>
        </div>
      </header>

      {/* ── Cards ── */}
      <section className="max-w-7xl mx-auto px-6 pb-20 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {TIERS.map((t) => {
          const price = annual ? t.annual : t.monthly;
          return (
            <div
              key={t.id}
              className={`relative flex flex-col rounded-2xl border p-6 transition-shadow hover:shadow-xl ${
                t.highlight
                  ? 'border-omega-accent bg-omega-surface shadow-lg shadow-omega-accent/10'
                  : 'border-omega-border bg-omega-card'
              }`}
            >
              {t.tag && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-omega-accent text-white text-xs font-semibold px-3 py-1 rounded-full">
                  {t.tag}
                </span>
              )}

              <h3 className="text-lg font-semibold text-omega-text">{t.name}</h3>
              <p className="text-omega-muted text-sm mt-1">{t.limits.cases} · {t.limits.storage}</p>

              <div className="mt-4 mb-6">
                <span className="text-4xl font-extrabold text-omega-text">
                  ${price === 0 ? '0' : price % 1 === 0 ? price : price.toFixed(2)}
                </span>
                {t.monthly > 0 && <span className="text-omega-muted text-sm ml-1">/ mo</span>}
              </div>

              <ul className="flex-1 space-y-3 mb-8">
                {t.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-omega-muted">
                    <Check /> {f}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleCheckout(t.id)}
                className={`w-full py-3 rounded-lg font-medium text-sm transition-colors ${
                  t.highlight
                    ? 'bg-omega-accent text-white hover:bg-indigo-500'
                    : 'bg-omega-surface text-omega-text border border-omega-border hover:border-omega-accent hover:text-omega-accent'
                }`}
              >
                {t.cta}
              </button>
            </div>
          );
        })}
      </section>

      {/* ── Comparison Table ── */}
      <section className="max-w-5xl mx-auto px-6 pb-20">
        <h2 className="text-2xl font-bold text-omega-text text-center mb-8">Feature comparison</h2>
        <div className="overflow-x-auto rounded-xl border border-omega-border">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-omega-surface">
                <th className="px-4 py-3 text-sm font-semibold text-omega-muted">Feature</th>
                {TIERS.map((t) => (
                  <th key={t.id} className="px-4 py-3 text-sm font-semibold text-omega-text text-center">{t.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {COMPARISON.map((row, i) => (
                <tr key={row.label} className={i % 2 ? 'bg-omega-card/50' : ''}>
                  <td className="px-4 py-3 text-sm text-omega-muted">{row.label}</td>
                  {['free', 'lite', 'pro', 'enterprise'].map((tier) => (
                    <td key={tier} className="px-4 py-3 text-center">
                      <span className="inline-flex justify-center">
                        <CellValue value={row[tier]} />
                      </span>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="max-w-3xl mx-auto px-6 pb-24">
        <h2 className="text-2xl font-bold text-omega-text text-center mb-8">Frequently asked questions</h2>
        <div className="space-y-3">
          {FAQS.map((faq, i) => (
            <div key={i} className="border border-omega-border rounded-xl overflow-hidden">
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                className="w-full flex items-center justify-between px-5 py-4 text-left text-omega-text hover:bg-omega-surface/50 transition-colors"
              >
                <span className="font-medium text-sm">{faq.q}</span>
                <svg
                  className={`w-5 h-5 text-omega-muted transition-transform ${openFaq === i ? 'rotate-180' : ''}`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {openFaq === i && (
                <div className="px-5 pb-4 text-sm text-omega-muted">{faq.a}</div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-omega-border/40 py-8 text-center text-omega-muted text-xs">
        © {new Date().getFullYear()} LitigationOS. All rights reserved.
      </footer>
    </div>
  );
}
