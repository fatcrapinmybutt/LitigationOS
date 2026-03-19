import '../styles/globals.css';

export default function App({ Component, pageProps }) {
  return (
    <div className="dark min-h-screen bg-omega-bg">
      <Component {...pageProps} />
    </div>
  );
}
