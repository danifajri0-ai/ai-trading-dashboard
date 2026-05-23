import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Trading Dashboard - Cockpit Frontend",
  description: "Next.js mirror frontend for AI trading cockpit."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <div className="container">
            <header className="topbar">
              <div>
                <h1 className="title">AI Trading Dashboard</h1>
                <p className="subtitle">Next.js cockpit mirror for production frontend.</p>
              </div>
              <nav className="nav">
                <Link href="/dashboard">Dashboard</Link>
                <Link href="/market/BTCUSD">Market</Link>
                <Link href="/watchlist">Watchlist</Link>
                <Link href="/history">History</Link>
                <Link href="/settings">Settings</Link>
              </nav>
            </header>
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
