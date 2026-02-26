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

## Fake data (development)

Generate fake portfolios, holdings, market data, commodities, and scenarios for local testing.

### Generate files

From the `backend/` directory:

```bash
python scripts/generate_fake_data.py [--output-dir data/fake] [--symbols AAPL,MSFT,...] [--days 30]
```

**Output files** (in `--output-dir`, default `data/fake`):

| File | Format | Content |
|------|--------|---------|
| `portfolios_holdings.csv` | CSV | Portfolio blocks (name, description + holdings). Compatible with import API. |
| `market_data.csv` | CSV | symbol, date, open, high, low, close, volume (5–10 symbols × N days). |
| `commodity_prices.csv` | CSV | commodity_type, date, price, unit. |
| `scenarios.json` | JSON | Scenario definitions (name, type, parameters). |

### Load portfolios

Use the Import API with the generated CSV:

```bash
curl -X POST http://localhost:8000/api/v1/portfolios/import -F "file=@data/fake/portfolios_holdings.csv"
```

Or in Swagger UI: **POST /api/v1/portfolios/import**, upload `portfolios_holdings.csv`.  
Note: only the first portfolio block in the CSV is imported; the file may contain multiple blocks.

### Use fake market data in the workflow

Set `FAKE_MARKET_DATA_CSV` to the path of `market_data.csv`, then start the server. The data collection node will use this data when running a scenario (symbols are resolved from portfolio holdings).

```bash
export FAKE_MARKET_DATA_CSV=data/fake/market_data.csv
uvicorn main:app --reload
```

Or generate and load in one go (in-process; data is in memory for that process only):

```bash
python scripts/generate_fake_data.py --output-dir data/fake --load
```

Then start the server in the same environment if you need the loaded data there; otherwise start the server in a separate terminal with `FAKE_MARKET_DATA_CSV=data/fake/market_data.csv` set.

## API Endpoints

- `/api/v1/portfolios`: Portfolio management
- `/api/v1/scenarios`: Scenario management
- `/api/v1/exposure`: Exposure analysis
- `/api/v1/reports`: Report generation
- `/api/v1/alerts`: Alert management

See `/api/docs` for full API documentation.
