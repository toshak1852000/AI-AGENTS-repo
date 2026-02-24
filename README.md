# PortfolioQ

**Autonomous Market & Portfolio Scenario Analyst**

Enterprise-grade autonomous workflow designed to evaluate the impact of market events, commodity fluctuations, and regulatory changes on portfolio holdings. Provides scenario-driven insights for investment teams and board-level decision-making.

## Features

- **Portfolio Management**: Manage multiple portfolios with detailed holdings tracking
- **Scenario Analysis**: Evaluate portfolio sensitivity to market, commodity, and regulatory changes
- **Exposure Analysis**: Identify company- and sector-level impacts
- **Risk Assessment**: Automated risk scoring and prioritization
- **Real-time Monitoring**: Continuous monitoring with real-time alerts
- **Report Generation**: Board-ready reports in PDF, Excel, and JSON formats
- **Autonomous Workflows**: Automated scenario analysis using LangGraph

## Architecture

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Next.js 14 (React, TypeScript)
- **Database**: PostgreSQL
- **Cache/Task Queue**: Redis + Celery
- **Workflow Engine**: LangGraph

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+

### Setup

1. **Clone the repository**
   ```bash
   cd /home/himanshu/projects/portfolioq
   ```

2. **Copy configuration files**
   ```bash
   cp docker-compose.example.yml docker-compose.yml
   cp .env.example .env
   ```

3. **Configure environment variables**
   Edit `.env` and fill in:
   - Database credentials
   - Redis configuration
   - API keys for market data providers (Alpha Vantage, Yahoo Finance, FRED)
   - Secret keys

4. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

5. **Set up backend (if running locally)**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

6. **Set up frontend (if running locally)**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Project Structure

```
portfolioq/
├── backend/              # FastAPI backend
│   ├── src/             # Application source code
│   │   ├── config/      # Configuration
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   ├── workflows/   # LangGraph workflows
│   │   ├── api/         # API endpoints
│   │   ├── tasks/       # Celery tasks
│   │   └── integrations/# External API integrations
│   ├── main.py          # FastAPI entry point
│   └── requirements.txt # Python dependencies
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/         # Next.js app router
│   │   ├── components/  # React components
│   │   └── lib/         # Utilities and API clients
│   └── package.json     # Node.js dependencies
├── docker-compose.yml   # Docker Compose (gitignored)
├── .env                 # Environment variables (gitignored)
└── README.md            # This file
```

## Development

### Backend

```bash
cd backend
uvicorn main:app --reload
```

API docs available at: http://localhost:8000/api/docs

### Frontend

```bash
cd frontend
npm run dev
```

Frontend available at: http://localhost:3000

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Environment Variables

See `.env.example` for all required environment variables. Key variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key
- `SECRET_KEY`: Application secret key

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Contributing

1. Create a feature branch
2. Make your changes
3. Ensure tests pass
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on the repository.
