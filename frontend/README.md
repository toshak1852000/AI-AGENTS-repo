# PortfolioQ Frontend

Next.js frontend for PortfolioQ - Autonomous Market & Portfolio Scenario Analyst.

## Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Set up environment variables**
   Create `.env.local` with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

## Project Structure

- `src/app/`: Next.js app router pages
- `src/components/`: React components
- `src/lib/`: Utilities, API clients, hooks, types
- `src/styles/`: Global styles

## Development

### Running Tests

```bash
npm test
```

### Building for Production

```bash
npm run build
npm start
```

## Pages

- `/`: Dashboard
- `/portfolios`: Portfolio list
- `/portfolios/[id]`: Portfolio detail
- `/scenarios`: Scenario list
- `/scenarios/create`: Create scenario
- `/scenarios/[id]`: Scenario detail
- `/exposure`: Exposure dashboard
- `/reports`: Report library
- `/alerts`: Alert center

## API Integration

API clients are located in `src/lib/api/`:
- `portfolios.ts`: Portfolio API
- `scenarios.ts`: Scenario API
- `exposure.ts`: Exposure API
- `reports.ts`: Report API
