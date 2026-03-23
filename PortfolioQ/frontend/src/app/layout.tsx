import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PortfolioQ - Autonomous Market & Portfolio Scenario Analyst',
  description: 'Enterprise-grade autonomous workflow for evaluating portfolio exposure to market events, commodity fluctuations, and regulatory changes',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
