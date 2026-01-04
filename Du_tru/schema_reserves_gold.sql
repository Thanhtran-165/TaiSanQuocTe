-- World Bank Reserves vs Gold Dataset - SQL Schema
-- Generated: 2026-01-03 21:56:29

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
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS
-- (iso2, country_name, year, total_reserves_usd, non_gold_reserves_usd, gold_value_usd_inferred, quality_flag);
