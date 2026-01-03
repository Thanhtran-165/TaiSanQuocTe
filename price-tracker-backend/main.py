"""
Price Tracker FastAPI Backend
REST API for Gold and Silver price tracking
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional
import sys
import os

# Add ui directory to path to import data_fetcher
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
ui_dir = os.path.join(parent_dir, 'ui')
sys.path.insert(0, ui_dir)

from data_fetcher import PriceDataFetcher

# Initialize FastAPI app
app = FastAPI(
    title="Price Tracker API",
    description="Gold and Silver price tracking API for Vietnam and International markets",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",  # Added for current session
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize data fetcher
fetcher = PriceDataFetcher()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Price Tracker API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/prices/today")
async def get_today_prices():
    """
    Get today's prices for all metals
    Returns SJC gold, Phu Quy silver, and international prices
    """
    try:
        data = fetcher.get_formatted_data()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/history")
async def get_price_history(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to fetch")
):
    """
    Get price history for the specified number of days
    """
    try:
        # Day-by-day history (1 point/day) for UI readability.
        if hasattr(fetcher, "get_history_daily"):
            df = fetcher.get_history_daily(days_back=days)
        else:
            df = fetcher.get_history(days_back=days)
        if df is None or df.empty:
            return {
                "success": True,
                "data": [],
                "message": "No history data available"
            }

        # Convert DataFrame to dict
        return {
            "success": True,
            "data": df.to_dict(orient="records"),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/sjc-items")
async def get_sjc_items():
    """Get latest SJC items with detailed prices"""
    try:
        items = fetcher.get_sjc_items_latest()
        if items is None or items.empty:
            # Warm-up: ensure DB has per-item rows by fetching today's snapshot once.
            try:
                fetcher.get_formatted_data()
            except Exception:
                pass
            items = fetcher.get_sjc_items_latest()
        if items is None or items.empty:
            return {
                "success": True,
                "data": [],
                "message": "No SJC items available"
            }

        return {
            "success": True,
            "data": items.to_dict(orient="records"),
            "count": len(items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/sjc-item-history")
async def get_sjc_item_history(
    name: str = Query(..., description="Product name"),
    branch: Optional[str] = Query(None, description="Branch name"),
    days: int = Query(default=365, ge=1, le=365)
):
    """Get history for a specific SJC item"""
    try:
        df = fetcher.get_sjc_item_history(name=name, branch=branch, days_back=days)
        if df is None or df.empty:
            return {
                "success": True,
                "data": [],
                "message": "No history available for this item"
            }

        return {
            "success": True,
            "data": df.to_dict(orient="records"),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/phuquy-items")
async def get_phuquy_items():
    """Get latest Phu Quy silver items"""
    try:
        items = fetcher.get_phuquy_items_latest()
        if items is None or items.empty:
            # Warm-up: ensure DB has per-item rows by fetching today's snapshot once.
            try:
                fetcher.get_formatted_data()
            except Exception:
                pass
            items = fetcher.get_phuquy_items_latest()
        if items is None or items.empty:
            return {
                "success": True,
                "data": [],
                "message": "No Phu Quy items available"
            }

        return {
            "success": True,
            "data": items.to_dict(orient="records"),
            "count": len(items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/phuquy-item-history")
async def get_phuquy_item_history(
    product: str = Query(..., description="Product name"),
    days: int = Query(default=365, ge=1, le=365)
):
    """Get history for a specific Phu Quy item"""
    try:
        df = fetcher.get_phuquy_item_history(product=product, days_back=days)
        if df is None or df.empty:
            return {
                "success": True,
                "data": [],
                "message": "No history available for this product"
            }

        return {
            "success": True,
            "data": df.to_dict(orient="records"),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
