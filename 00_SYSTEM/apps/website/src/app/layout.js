import './globals.css';

export const metadata = {
  title: 'LitigationOS — AI-Powered Litigation Intelligence',
  description: 'Production-ready litigation management platform with OMEGA scoring, evidence analysis, and multi-forum filing support. Built for pro se litigants.',
  keywords: ['litigation', 'legal tech', 'pro se', 'family law', 'court filings', 'AI legal'],
};

// Security headers
export const headers = () => [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-XSS-Protection', value: '1; mode=block' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
];

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
