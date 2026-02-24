export default function PortfolioDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Portfolio Detail</h1>
      <p>Portfolio ID: {params.id}</p>
      <p>Portfolio detail page - Coming soon</p>
    </div>
  )
}
