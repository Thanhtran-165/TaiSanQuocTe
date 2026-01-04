# World Bank Reserves vs Gold Dataset

This project builds an annual panel dataset of **gold vs non-gold reserves by economy** from the World Bank World Development Indicators (WDI) API.

## Data Source

- **Source**: World Bank World Development Indicators (WDI)
- **API Endpoint**: https://api.worldbank.org/v2/
- **No API key required**

## Indicators

| Indicator ID | Description |
|--------------|-------------|
| `FI.RES.TOTL.CD` | Total reserves (includes gold), current US$ |
| `FI.RES.XGLD.CD` | Total reserves minus gold, current US$ |

## Methodology

The inferred gold value is calculated as:

```
GOLD_VALUE_USD_INFERRED = TOTAL_RESERVES_USD - NON_GOLD_RESERVES_USD
```

**Important Notes:**
- This is an **inferred annual USD value**, not physical tonnes
- Values are in current US dollars (not inflation-adjusted)
- Data is annual, available from 1960–present for most economies
- Negative inferred gold values are flagged with `quality_flag="NEGATIVE_GOLD_INFERRED"`

## How to Run

```bash
python build_reserves_gold_dataset.py
```

**Requirements:**
- Python 3.7+
- `requests`
- `pandas`

Optional:
- `pyarrow` (for Parquet export)

## Output Files

| File | Description |
|------|-------------|
| `reserves_gold_by_country_year.csv` | Main dataset with inferred gold values |
| `coverage_report.csv` | Coverage statistics by country |
| `schema_reserves_gold.sql` | Suggested SQL schema for database import |

## Coverage Summary

The pipeline automatically:
- Fetches data for all economies (excluding aggregates like "World", "income groups", etc.)
- Handles pagination for large datasets
- Implements retry logic for network errors
- Respects rate limits (0.2s delay between requests)
- Generates coverage reports showing data availability by country

## Schema

See `schema_reserves_gold.sql` for suggested database schema.

## Date Generated

2026-01-03 21:56:29