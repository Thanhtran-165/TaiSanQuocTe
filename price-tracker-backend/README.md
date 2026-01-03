# Price Tracker Backend

FastAPI backend for Gold and Silver price tracking.

## Setup

1. **Install dependencies:**
```bash
cd price-tracker-backend
pip install -r requirements.txt
```

2. **Run the server:**
```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python main.py
```

3. **Access API docs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Prices
- `GET /api/prices/today` - Get today's prices
- `GET /api/prices/history?days=7` - Get price history
- `GET /api/prices/sjc-items` - Get SJC items
- `GET /api/prices/sjc-item-history?name=...&branch=...&days=365` - Get SJC item history
- `GET /api/prices/phuquy-items` - Get Phu Quy items
- `GET /api/prices/phuquy-item-history?product=...&days=365` - Get Phu Quy item history

### Health
- `GET /api/health` - Health check
- `GET /` - Root endpoint

## Development

The backend uses the existing `data_fetcher.py` from the `ui/` folder, so all data sources (SJC, Phu Quy, International) are already integrated.

## CORS

CORS is enabled for:
- http://localhost:3000 (Next.js dev server)
- http://localhost:3001

Add more origins in `main.py` if needed.
