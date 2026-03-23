# PortfolioQ Backend

FastAPI backend for PortfolioQ - Autonomous Market & Portfolio Scenario Analyst.

## Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Copy `.env.example` to `.env` in the project root and configure.

4. **Run database migrations** (when implemented)
   ```bash
   alembic upgrade head
   ```

5. **Run the server**
   ```bash
   uvicorn main:app --reload
   ```

## Project Structure

- `src/config/`: Configuration and settings
- `src/models/`: SQLAlchemy database models
- `src/schemas/`: Pydantic schemas for API
- `src/services/`: Business logic services
- `src/workflows/`: LangGraph workflow definitions
- `src/api/`: API endpoints
- `src/tasks/`: Celery task definitions
- `src/integrations/`: External API integrations
- `src/analytics/`: Analytics and calculation engines

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
ruff check src/
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## API Endpoints

- `/api/v1/portfolios`: Portfolio management
- `/api/v1/scenarios`: Scenario management
- `/api/v1/exposure`: Exposure analysis
- `/api/v1/reports`: Report generation
- `/api/v1/alerts`: Alert management

See `/api/docs` for full API documentation.
