import Link from 'next/link';

const TIERS = [
  { name: 'Free', price: '$0', period: '/mo', features: ['1 case', 'Basic timeline', '500MB storage', 'Community support'], cta: 'Get Started Free', highlight: false },
  { name: 'Lite', price: '$29', period: '/mo', features: ['1 case', 'OMEGA scoring', 'Evidence analysis', '5GB storage', 'Email support'], cta: 'Start Lite', highlight: false },
  { name: 'Pro', price: '$99', period: '/mo', features: ['5 cases', 'Full AI analysis', 'Graph visualization', 'Filing builder', '25GB storage', 'Priority support'], cta: 'Go Pro', highlight: true },
  { name: 'Enterprise', price: '$299', period: '/mo', features: ['Unlimited cases', 'White-label', 'API access', 'Custom integrations', '100GB storage', 'Dedicated support'], cta: 'Contact Sales', highlight: false },
];

function Hero() {
  return (
    <section className="relative overflow-hidden py-24 px-6">
      <div className="absolute inset-0 bg-gradient-to-b from-omega-accent/5 to-transparent" />
      <div className="relative max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-omega-accent/10 border border-omega-accent/20 text-omega-accent text-sm mb-8">
          <span className="w-2 h-2 rounded-full bg-omega-accent animate-pulse" />
          Now in Public Beta
        </div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
          <span className="text-omega-accent">Litigation</span>OS
        </h1>
        <p className="text-xl md:text-2xl text-omega-muted max-w-3xl mx-auto mb-8">
          AI-powered litigation intelligence for pro se litigants.
          Score every action, analyze every document, win every case.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/dashboard"
            className="px-8 py-3 bg-omega-accent text-white rounded-lg font-semibold hover:bg-omega-accent/90 transition-colors shadow-lg shadow-omega-accent/20">
            Launch Dashboard →
          </Link>
          <Link href="#pricing"
            className="px-8 py-3 border border-omega-border text-omega-text rounded-lg font-semibold hover:border-omega-accent transition-colors">
            View Pricing
          </Link>
        </div>
      </div>
    </section>
  );
}

function Features() {
  const features = [
    { icon: '⚖️', title: 'OMEGA Scoring', desc: '10-axis scoring system rates every legal action from 0-100. Know exactly what to file and when.' },
    { icon: '🔍', title: 'Evidence Analysis', desc: 'AI-powered evidence mining. Cross-reference quotes, detect contradictions, build impeachment packages.' },
    { icon: '📊', title: 'Graph Intelligence', desc: 'Neo4j-powered knowledge graph connects evidence → claims → laws → actions → outcomes.' },
    { icon: '📄', title: 'Filing Builder', desc: 'WYSIWYG editor with MCR compliance checking. Generate court-ready documents in minutes.' },
    { icon: '⏱️', title: 'Timeline Tracker', desc: 'Master chronology with separation day counter, deadline alerts, and docket monitoring.' },
    { icon: '💰', title: 'Pro Se Toolkit', desc: 'Affordable tools designed for self-represented litigants. Level the playing field.' },
  ];

  return (
    <section className="py-20 px-6">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12">
          Everything You Need to <span className="text-omega-accent">Win</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <div key={i} className="p-6 bg-omega-card border border-omega-border rounded-xl hover:border-omega-accent/50 transition-colors">
              <span className="text-3xl mb-4 block">{f.icon}</span>
              <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
              <p className="text-omega-muted text-sm">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  return (
    <section id="pricing" className="py-20 px-6 bg-omega-surface/50">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-4">
          Simple, Transparent Pricing
        </h2>
        <p className="text-omega-muted text-center mb-12 max-w-2xl mx-auto">
          Start free. Upgrade when you need more power. 20% off annual plans.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {TIERS.map((tier, i) => (
            <div key={i} className={`p-6 rounded-xl border ${
              tier.highlight 
                ? 'bg-omega-accent/10 border-omega-accent shadow-lg shadow-omega-accent/10' 
                : 'bg-omega-card border-omega-border'
            }`}>
              {tier.highlight && (
                <div className="text-xs font-bold text-omega-accent uppercase tracking-wider mb-2">
                  Most Popular
                </div>
              )}
              <h3 className="text-xl font-bold">{tier.name}</h3>
              <div className="mt-2 mb-4">
                <span className="text-4xl font-bold">{tier.price}</span>
                <span className="text-omega-muted">{tier.period}</span>
              </div>
              <ul className="space-y-2 mb-6">
                {tier.features.map((f, j) => (
                  <li key={j} className="flex items-center gap-2 text-sm">
                    <span className="text-omega-success">✓</span> {f}
                  </li>
                ))}
              </ul>
              <button className={`w-full py-2.5 rounded-lg font-semibold transition-colors ${
                tier.highlight
                  ? 'bg-omega-accent text-white hover:bg-omega-accent/90'
                  : 'bg-omega-surface text-omega-text border border-omega-border hover:border-omega-accent'
              }`}>
                {tier.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="py-12 px-6 border-t border-omega-border">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
        <div>
          <span className="text-xl font-bold text-omega-accent">⚖️ LitigationOS</span>
          <p className="text-omega-muted text-sm mt-1">AI-powered litigation intelligence</p>
        </div>
        <div className="text-omega-muted text-sm">
          © {new Date().getFullYear()} LitigationOS. Built by a pro se father fighting for justice.
        </div>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen">
      <nav className="flex items-center justify-between px-6 py-4 border-b border-omega-border/50">
        <span className="text-lg font-bold">
          <span className="text-omega-accent">⚖️ Litigation</span>OS
        </span>
        <div className="flex items-center gap-4">
          <Link href="#pricing" className="text-omega-muted hover:text-omega-text text-sm">Pricing</Link>
          <Link href="/dashboard" className="px-4 py-1.5 bg-omega-accent text-white rounded-lg text-sm font-semibold hover:bg-omega-accent/90">
            Dashboard
          </Link>
        </div>
      </nav>
      <Hero />
      <Features />
      <Pricing />
      <Footer />
    </main>
  );
}
