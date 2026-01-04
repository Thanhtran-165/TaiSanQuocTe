#!/usr/bin/env python3
"""
World Bank Reserves vs Gold Dataset Builder

Fetches "Total reserves (includes gold), current US$" and "Total reserves minus gold, current US$"
from World Bank WDI API and calculates inferred gold value by economy and year.

Indicators:
- TOTAL: FI.RES.TOTL.CD
- NON_GOLD: FI.RES.XGLD.CD

Author: Auto-generated for GLM executor
Date: 2026-01-03
"""

import requests
import pandas as pd
import time
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://api.worldbank.org/v2"
INDICATOR_TOTAL = "FI.RES.TOTL.CD"
INDICATOR_NON_GOLD = "FI.RES.XGLD.CD"
PER_PAGE = 20000  # Max records per page
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds between retries
REQUEST_DELAY = 0.2  # seconds between requests (rate limiting)

# Output files
OUTPUT_CSV = "reserves_gold_by_country_year.csv"
COVERAGE_REPORT_CSV = "coverage_report.csv"
README_FILE = "README_reserves_gold.md"
SQL_SCHEMA_FILE = "schema_reserves_gold.sql"


class WorldBankAPIError(Exception):
    """Custom exception for World Bank API errors."""
    pass


def fetch_with_retry(url: str, params: Optional[Dict] = None, max_retries: int = MAX_RETRIES) -> Optional[Dict]:
    """
    Fetch data from URL with retry logic for network errors and 5xx status codes.

    Args:
        url: API endpoint URL
        params: Query parameters
        max_retries: Maximum number of retry attempts

    Returns:
        JSON response data or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching: {url}")
            response = requests.get(url, params=params, timeout=30)

            # Check for server errors (5xx)
            if response.status_code >= 500:
                logger.warning(f"Server error {response.status_code} on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    raise WorldBankAPIError(f"Server error {response.status_code} after {max_retries} attempts")

            # Check for client errors (4xx)
            if response.status_code >= 400:
                logger.error(f"Client error {response.status_code}: {response.text}")
                raise WorldBankAPIError(f"Client error {response.status_code}")

            # Success
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                return None

    return None


def fetch_countries() -> List[Dict]:
    """
    Fetch all countries/economies from World Bank API with pagination.
    Filter out aggregates based on region, income level, and lending type.

    Returns:
        List of country dictionaries
    """
    logger.info("Fetching countries/economies from World Bank API...")

    all_countries = []
    page = 1
    while True:
        params = {
            "format": "json",
            "per_page": PER_PAGE,
            "page": page
        }

        data = fetch_with_retry(f"{BASE_URL}/country", params=params)
        if not data or not isinstance(data, list) or len(data) < 2:
            logger.error(f"Failed to fetch page {page} of countries")
            break

        metadata = data[0]
        countries_page = data[1]

        # Process and filter countries
        for country in countries_page:
            # Extract relevant fields
            region = country.get("region", {})
            income_level = country.get("incomeLevel", {})
            lending_type = country.get("lendingType", {})

            # Filter out aggregates
            region_id = region.get("id", "")
            income_id = income_level.get("id", "")
            lending_id = lending_type.get("id", "")

            # Skip if any of these are "NA" (aggregate)
            if region_id == "NA" or income_id == "NA" or lending_id == "NA":
                continue

            # Ensure valid ISO2 code
            iso2 = country.get("iso2Code", "")
            if not iso2 or len(iso2) != 2:
                continue

            # Add to list
            all_countries.append({
                "iso2": iso2,
                "iso3": country.get("id", ""),
                "country_name": country.get("name", ""),
                "region_id": region_id,
                "region_name": region.get("value", ""),
                "income_level_id": income_id,
                "income_level_name": income_level.get("value", ""),
                "lending_type_id": lending_id,
                "lending_type_name": lending_type.get("value", "")
            })

        logger.info(f"Fetched page {page}: {len(countries_page)} countries (kept {len(all_countries)} after filtering)")

        # Check if there are more pages
        total_pages = metadata.get("pages", 1)
        if page >= total_pages:
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    logger.info(f"Total countries after filtering aggregates: {len(all_countries)}")
    return all_countries


def fetch_indicator_data(indicator_id: str, countries: List[Dict]) -> pd.DataFrame:
    """
    Fetch indicator data for all countries with pagination.

    Args:
        indicator_id: World Bank indicator code
        countries: List of country dictionaries

    Returns:
        DataFrame with columns: iso2, iso3, country_name, year, value, indicator_id
    """
    logger.info(f"Fetching indicator {indicator_id}...")

    # Create a set of valid ISO3 codes for quick lookup
    valid_iso3_codes = {c["iso3"]: c for c in countries}
    logger.info(f"Filtering for {len(valid_iso3_codes)} valid countries")

    all_records = []
    page = 1
    total_records = 0

    while True:
        params = {
            "format": "json",
            "per_page": PER_PAGE,
            "page": page
        }

        url = f"{BASE_URL}/country/all/indicator/{indicator_id}"
        data = fetch_with_retry(url, params=params)

        if not data or not isinstance(data, list) or len(data) < 2:
            logger.error(f"Failed to fetch page {page} for indicator {indicator_id}")
            break

        metadata = data[0]
        records_page = data[1]

        # Process records
        for record in records_page:
            country_iso3 = record.get("countryiso3code", "")
            value = record.get("value")

            # Skip null values first
            if value is None:
                continue

            # Skip if not a valid country (not in our filtered list)
            if country_iso3 not in valid_iso3_codes:
                continue

            # Get country info from lookup
            country_info = valid_iso3_codes[country_iso3]
            iso2 = country_info["iso2"]
            country_name = country_info["country_name"]

            year = int(record.get("date", 0))

            all_records.append({
                "iso2": iso2,
                "iso3": country_iso3,
                "country_name": country_name,
                "year": year,
                "value": float(value),
                "indicator_id": indicator_id
            })

        total_records += len(records_page)
        logger.info(f"Page {page}: {len(records_page)} records (processed: {len(all_records)} with non-null values for valid countries)")

        # Check pagination
        total_pages = metadata.get("pages", 1)
        if page >= total_pages:
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    logger.info(f"Total valid records for {indicator_id}: {len(all_records)}")

    if not all_records:
        return pd.DataFrame()

    return pd.DataFrame(all_records)


def calculate_gold_inference(df_total: pd.DataFrame, df_non_gold: pd.DataFrame) -> pd.DataFrame:
    """
    Join total and non-gold reserves, then calculate inferred gold value.

    Args:
        df_total: DataFrame with total reserves data
        df_non_gold: DataFrame with non-gold reserves data

    Returns:
        DataFrame with calculated gold value and quality flags
    """
    logger.info("Calculating gold inference by merging TOTAL and NON_GOLD data...")

    # Merge on iso2 and year
    merged = pd.merge(
        df_total,
        df_non_gold,
        on=["iso2", "country_name", "year"],
        how="outer",
        suffixes=("_total", "_non_gold")
    )

    # Calculate inferred gold value
    merged["gold_value_usd_inferred"] = merged["value_total"] - merged["value_non_gold"]

    # Add quality flags
    merged["quality_flag"] = merged.apply(
        lambda row: "NEGATIVE_GOLD_INFERRED" if row["gold_value_usd_inferred"] < 0 else "OK",
        axis=1
    )

    # Rename columns for clarity
    merged.rename(columns={
        "value_total": "total_reserves_usd",
        "value_non_gold": "non_gold_reserves_usd"
    }, inplace=True)

    # Filter to only records with at least one value
    merged = merged[
        merged["total_reserves_usd"].notna() |
        merged["non_gold_reserves_usd"].notna()
    ]

    # Reorder columns
    columns = [
        "iso2", "country_name", "year",
        "total_reserves_usd", "non_gold_reserves_usd", "gold_value_usd_inferred",
        "quality_flag"
    ]
    merged = merged[columns]

    # Count negative gold values
    negative_count = (merged["quality_flag"] == "NEGATIVE_GOLD_INFERRED").sum()
    if negative_count > 0:
        logger.warning(f"Found {negative_count} records with negative inferred gold value")

    return merged


def generate_coverage_report(df_total: pd.DataFrame, df_non_gold: pd.DataFrame, df_merged: pd.DataFrame) -> pd.DataFrame:
    """
    Generate coverage report by country.

    Args:
        df_total: DataFrame with total reserves data
        df_non_gold: DataFrame with non-gold reserves data
        df_merged: Merged DataFrame

    Returns:
        DataFrame with coverage statistics by country
    """
    logger.info("Generating coverage report...")

    # Get unique countries
    all_iso2 = set(df_total["iso2"].unique()) | set(df_non_gold["iso2"].unique())

    coverage_data = []

    for iso2 in sorted(all_iso2):
        # Get country name from merged data
        country_rows = df_merged[df_merged["iso2"] == iso2]
        if country_rows.empty:
            continue
        country_name = country_rows["country_name"].iloc[0]

        # Check availability
        has_total = iso2 in df_total["iso2"].values
        has_non_gold = iso2 in df_non_gold["iso2"].values
        has_both = has_total and has_non_gold

        # Get year range
        country_data = df_merged[df_merged["iso2"] == iso2]
        country_data = country_data[
            (country_data["total_reserves_usd"].notna()) |
            (country_data["non_gold_reserves_usd"].notna())
        ]

        if not country_data.empty:
            first_year = int(country_data["year"].min())
            last_year = int(country_data["year"].max())
            n_years = len(country_data["year"].unique())
        else:
            first_year = None
            last_year = None
            n_years = 0

        coverage_data.append({
            "iso2": iso2,
            "country_name": country_name,
            "has_total": has_total,
            "has_non_gold": has_non_gold,
            "has_both": has_both,
            "first_year": first_year,
            "last_year": last_year,
            "n_years": n_years
        })

    df_coverage = pd.DataFrame(coverage_data)
    return df_coverage


def print_summary_statistics(df_total: pd.DataFrame, df_non_gold: pd.DataFrame,
                            df_merged: pd.DataFrame, df_coverage: pd.DataFrame):
    """
    Print summary statistics to console.

    Args:
        df_total: DataFrame with total reserves data
        df_non_gold: DataFrame with non-gold reserves data
        df_merged: Merged DataFrame
        df_coverage: Coverage report DataFrame
    """
    logger.info("\n" + "="*80)
    logger.info("SUMMARY STATISTICS")
    logger.info("="*80)

    # Count unique economies
    total_economies = df_coverage.shape[0]
    economies_with_total = df_coverage["has_total"].sum()
    economies_with_non_gold = df_coverage["has_non_gold"].sum()
    economies_with_both = df_coverage["has_both"].sum()

    logger.info(f"\nTotal economies (after filtering aggregates): {total_economies}")
    logger.info(f"Economies with TOTAL reserves data: {economies_with_total} ({economies_with_total/total_economies*100:.1f}%)")
    logger.info(f"Economies with NON_GOLD reserves data: {economies_with_non_gold} ({economies_with_non_gold/total_economies*100:.1f}%)")
    logger.info(f"Economies with BOTH indicators: {economies_with_both} ({economies_with_both/total_economies*100:.1f}%)")

    # Record counts
    logger.info(f"\nTotal records:")
    logger.info(f"  TOTAL reserves: {len(df_total):,}")
    logger.info(f"  NON_GOLD reserves: {len(df_non_gold):,}")
    logger.info(f"  Merged (with at least one value): {len(df_merged):,}")

    # Gold value statistics
    gold_data = df_merged[
        df_merged["gold_value_usd_inferred"].notna()
    ]["gold_value_usd_inferred"]

    if not gold_data.empty:
        logger.info(f"\nInferred gold value statistics:")
        logger.info(f"  Records with calculated gold value: {len(gold_data):,}")
        logger.info(f"  Mean: ${gold_data.mean():,.0f}")
        logger.info(f"  Median: ${gold_data.median():,.0f}")
        logger.info(f"  Std Dev: ${gold_data.std():,.0f}")

        # Top countries by average gold value
        top_gold = df_merged[
            df_merged["gold_value_usd_inferred"].notna()
        ].groupby("iso2")["gold_value_usd_inferred"].mean().sort_values(ascending=False).head(20)

        logger.info(f"\nTop 20 economies by average inferred gold value:")
        for iso2, avg_gold in top_gold.items():
            country_name = df_coverage[df_coverage["iso2"] == iso2]["country_name"].iloc[0]
            logger.info(f"  {iso2} - {country_name}: ${avg_gold:,.0f}")

    # Missing data
    logger.info(f"\nTop 20 economies missing one or both indicators:")
    missing = df_coverage[~df_coverage["has_both"]].sort_values("country_name")
    for _, row in missing.head(20).iterrows():
        missing_indicators = []
        if not row["has_total"]:
            missing_indicators.append("TOTAL")
        if not row["has_non_gold"]:
            missing_indicators.append("NON_GOLD")
        logger.info(f"  {row['iso2']} - {row['country_name']}: missing {', '.join(missing_indicators)}")

    logger.info("\n" + "="*80 + "\n")


def export_data(df_merged: pd.DataFrame, df_coverage: pd.DataFrame):
    """
    Export data to CSV and optionally Parquet.

    Args:
        df_merged: Merged DataFrame with reserves data
        df_coverage: Coverage report DataFrame
    """
    logger.info("Exporting data...")

    # Export main dataset
    df_merged.to_csv(OUTPUT_CSV, index=False)
    logger.info(f"Exported {len(df_merged):,} records to {OUTPUT_CSV}")

    # Export coverage report
    df_coverage.to_csv(COVERAGE_REPORT_CSV, index=False)
    logger.info(f"Exported coverage report to {COVERAGE_REPORT_CSV}")

    # Try to export Parquet if pyarrow is available
    try:
        df_merged.to_parquet(OUTPUT_CSV.replace(".csv", ".parquet"), index=False)
        df_coverage.to_parquet(COVERAGE_REPORT_CSV.replace(".csv", ".parquet"), index=False)
        logger.info("Also exported to Parquet format")
    except ImportError:
        logger.info("Parquet export skipped (pyarrow not installed)")


def generate_readme():
    """Generate README file with project documentation."""
    readme_content = """# World Bank Reserves vs Gold Dataset

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

""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme_content)

    logger.info(f"Generated README: {README_FILE}")


def generate_sql_schema():
    """Generate SQL schema file for database import."""
    sql_content = """-- World Bank Reserves vs Gold Dataset - SQL Schema
-- Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """

-- Countries table (reference data)
CREATE TABLE IF NOT EXISTS countries (
    iso2 CHAR(2) PRIMARY KEY,
    iso3 CHAR(3) UNIQUE NOT NULL,
    country_name VARCHAR(255) NOT NULL,
    region_id VARCHAR(10),
    region_name VARCHAR(255),
    income_level_id VARCHAR(10),
    income_level_name VARCHAR(255),
    lending_type_id VARCHAR(10),
    lending_type_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Reserves yearly data (main fact table)
CREATE TABLE IF NOT EXISTS reserves_yearly (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    iso2 CHAR(2) NOT NULL,
    year INT NOT NULL,
    total_reserves_usd DECIMAL(20, 2),
    non_gold_reserves_usd DECIMAL(20, 2),
    gold_value_usd_inferred DECIMAL(20, 2),
    quality_flag VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (iso2) REFERENCES countries(iso2),
    UNIQUE KEY unique_country_year (iso2, year),
    INDEX idx_year (year),
    INDEX idx_iso2 (iso2),
    INDEX idx_gold_value (gold_value_usd_inferred)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Example import statements (adjust path to your CSV files):
-- LOAD DATA INFILE 'reserves_gold_by_country_year.csv'
-- INTO TABLE reserves_yearly
-- FIELDS TERMINATED BY ','
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\\n'
-- IGNORE 1 ROWS
-- (iso2, country_name, year, total_reserves_usd, non_gold_reserves_usd, gold_value_usd_inferred, quality_flag);
"""

    with open(SQL_SCHEMA_FILE, "w", encoding="utf-8") as f:
        f.write(sql_content)

    logger.info(f"Generated SQL schema: {SQL_SCHEMA_FILE}")


def main():
    """Main pipeline execution."""
    start_time = time.time()

    logger.info("="*80)
    logger.info("WORLD BANK RESERVES VS GOLD DATASET - PIPELINE START")
    logger.info("="*80 + "\n")

    try:
        # Step 1: Fetch countries (filter out aggregates)
        countries = fetch_countries()

        if not countries:
            logger.error("No countries found. Exiting.")
            return

        # Step 2: Fetch indicator data
        df_total = fetch_indicator_data(INDICATOR_TOTAL, countries)
        df_non_gold = fetch_indicator_data(INDICATOR_NON_GOLD, countries)

        if df_total.empty and df_non_gold.empty:
            logger.error("No indicator data found. Exiting.")
            return

        # Step 3: Calculate inferred gold value
        df_merged = calculate_gold_inference(df_total, df_non_gold)

        # Step 4: Generate coverage report
        df_coverage = generate_coverage_report(df_total, df_non_gold, df_merged)

        # Step 5: Print summary statistics
        print_summary_statistics(df_total, df_non_gold, df_merged, df_coverage)

        # Step 6: Export data
        export_data(df_merged, df_coverage)

        # Step 7: Generate documentation
        generate_readme()
        generate_sql_schema()

        elapsed = time.time() - start_time
        logger.info(f"\nPipeline completed successfully in {elapsed:.1f} seconds")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
