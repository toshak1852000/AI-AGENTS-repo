export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-4">PortfolioQ</h1>
        <p className="text-xl mb-8">
          Autonomous Market & Portfolio Scenario Analyst
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <div className="p-4 border rounded">
            <h2 className="text-lg font-semibold mb-2">Portfolios</h2>
            <p>Manage your investment portfolios</p>
          </div>
          <div className="p-4 border rounded">
            <h2 className="text-lg font-semibold mb-2">Scenarios</h2>
            <p>Analyze market scenarios and impacts</p>
          </div>
          <div className="p-4 border rounded">
            <h2 className="text-lg font-semibold mb-2">Reports</h2>
            <p>Generate board-ready reports</p>
          </div>
        </div>
      </div>
    </main>
  )
}
