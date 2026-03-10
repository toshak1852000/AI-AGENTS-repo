# PortfolioQ Setup Guide

This document provides step-by-step instructions for setting up the PortfolioQ project.

## CI (GitHub Actions)

CI runs on push/PR to `main` or `master`: backend pytest and ruff lint, frontend Jest tests and `next lint`. Optional: Docker image build. **Merge is blocked until tests and lint pass** (configure branch protection in GitHub to require status checks).

## Initial Setup

### 1. Copy Configuration Files

```bash
cd /home/himanshu/projects/portfolioq

# Copy Docker Compose template
cp docker-compose.example.yml docker-compose.yml

# Copy environment variables template
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and fill in the following:

**Required:**
- `POSTGRES_PASSWORD`: Database password
- `SECRET_KEY`: Generate a secure secret key (e.g., `openssl rand -hex 32`)
- `ALPHA_VANTAGE_API_KEY`: Get from https://www.alphavantage.co/support/#api-key
- `FRED_API_KEY`: Get from https://fred.stlouisfed.org/docs/api/api_key.html

**Optional but Recommended:**
- `YAHOO_FINANCE_API_KEY`: If using Yahoo Finance API
- `LANGSMITH_API_KEY`: If using LangSmith for workflow monitoring

### 3. Start Services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- MLflow (port 5003)
- Backend API (port 8000)
- Celery Worker and Celery Beat
- Prometheus (port 9090) and Grafana (port 3001)

All required environment variables are documented in `.env.example`. For Docker, ensure `POSTGRES_PASSWORD` and `SECRET_KEY` are set; optional: `ALPHA_VANTAGE_API_KEY`, `FRED_API_KEY`, `OPENAI_API_KEY`, `GRAFANA_USER`, `GRAFANA_PASSWORD`.

### 4. Set Up Backend (Local Development)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (when database models are implemented)
# alembic upgrade head

# Run the server
uvicorn main:app --reload
```

Backend API will be available at: http://localhost:8000
API Documentation: http://localhost:8000/api/docs

### 5. Set Up Frontend (Local Development)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## Project Structure

```
portfolioq/
├── backend/              # FastAPI backend
│   ├── src/
│   │   ├── config/      # Configuration (settings.py, constants.py)
│   │   ├── models/      # Database models (SQLAlchemy)
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
│   │   ├── app/         # Next.js app router pages
│   │   ├── components/ # React components
│   │   └── lib/         # API clients, hooks, types
│   └── package.json     # Node.js dependencies
├── docker-compose.yml   # Docker Compose (gitignored)
├── .env                 # Environment variables (gitignored)
└── README.md            # Project documentation
```

## Next Steps

1. **Database Setup**: Implement database models and run migrations
2. **API Implementation**: Complete the endpoint implementations
3. **Service Layer**: Implement business logic in services
4. **Workflow Implementation**: Build LangGraph workflows
5. **Frontend Components**: Build React components and pages
6. **Testing**: Add unit and integration tests

## Troubleshooting

### Backend won't start
- Check that PostgreSQL and Redis are running
- Verify DATABASE_URL and REDIS_URL in .env
- Check logs: `docker-compose logs backend`

### Frontend won't connect to backend
- Verify NEXT_PUBLIC_API_URL in .env or .env.local
- Check CORS settings in backend/src/config/settings.py
- Ensure backend is running on the correct port

### Database connection errors
- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check DATABASE_URL format: `postgresql://user:password@host:port/dbname`
- Verify credentials in .env match docker-compose.yml

## Development Workflow

1. Make changes to code
2. Backend auto-reloads with `--reload` flag
3. Frontend hot-reloads automatically
4. Run tests before committing
5. Check API docs at http://localhost:8000/api/docs

## Useful Commands

```bash
# Backend
cd backend
uvicorn main:app --reload          # Run server
pytest                              # Run tests
alembic upgrade head                # Run migrations
black src/                          # Format code
ruff check src/                     # Lint code

# Frontend
cd frontend
npm run dev                         # Run dev server
npm run build                       # Build for production
npm test                            # Run tests
npm run lint                        # Lint code

# Docker
docker-compose up -d                # Start services
docker-compose down                  # Stop services
docker-compose logs -f backend       # View logs
docker-compose restart backend       # Restart service
```
