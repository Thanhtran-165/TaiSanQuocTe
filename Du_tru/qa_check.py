import pandas as pd

df = pd.read_csv("reserves_gold_split_wdi.csv")

# 1) kiểu dữ liệu
df["year"] = df["year"].astype(int)

num_cols = ["total_reserves_usd", "non_gold_reserves_usd", "gold_reserves_value_usd_inferred"]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

print("="*80)
print("QA CHECK #1: NULL VALUES IN NUMERIC COLUMNS")
print("="*80)
print("Nulls in numeric cols:")
print(df[num_cols].isna().sum())
print()

# 2) kiểm tra phép trừ
diff = df["total_reserves_usd"] - df["non_gold_reserves_usd"]
print("="*80)
print("QA CHECK #2: VALIDATE SUBTRACTION (gold = total - non_gold)")
print("="*80)
max_diff = (df["gold_reserves_value_usd_inferred"] - diff).abs().max()
print(f"Max abs(gold - (total-non_gold)): {max_diff}")
if max_diff < 0.01:
    print("✅ PASS: All gold values match total - non_gold")
else:
    print("❌ FAIL: Mismatch detected!")
print()

# 3) kiểm tra negative/zero
print("="*80)
print("QA CHECK #3: NEGATIVE AND ZERO GOLD VALUES")
print("="*80)
negative_count = (df["gold_reserves_value_usd_inferred"] < 0).sum()
zero_with_total = ((df["gold_reserves_value_usd_inferred"] == 0) & (df["total_reserves_usd"] > 0)).sum()
zero_with_null_total = ((df["gold_reserves_value_usd_inferred"] == 0) & (df["total_reserves_usd"].isna())).sum()

print(f"Negative gold records (< 0): {negative_count}")
if negative_count == 0:
    print("✅ PASS: No negative gold values")
else:
    print(f"❌ FAIL: {negative_count} negative records found!")

print(f"\nZero gold with total > 0: {zero_with_total}")
print(f"Zero gold with total = NaN: {zero_with_null_total}")
print(f"Total zero gold: {zero_with_total + zero_with_null_total}")
print()

# 4) quality flag consistency
print("="*80)
print("QA CHECK #4: QUALITY FLAG DISTRIBUTION")
print("="*80)
quality_counts = df["quality_flag"].value_counts()
print(quality_counts)
print()
for flag, count in quality_counts.items():
    pct = count / len(df) * 100
    print(f"  {flag}: {count:,} ({pct:.1f}%)")
print()

# 5) coverage theo economy
print("="*80)
print("QA CHECK #5: ECONOMY-LEVEL COVERAGE (PRE-MERGE LOGIC)")
print("="*80)

# Tách data thành 2 datasets riêng biệt để tính coverage ĐÚNG
df_total = df[df["total_reserves_usd"].notna()][["iso2", "country_name", "year"]].copy()
df_non_gold = df[df["non_gold_reserves_usd"].notna()][["iso2", "country_name", "year"]].copy()

print(f"Total records with total_reserves: {len(df_total)}")
print(f"Total records with non_gold_reserves: {len(df_non_gold)}")
print()

# Coverage theo economy
cov_total = df_total.groupby("iso2")["year"].nunique()
cov_non_gold = df_non_gold.groupby("iso2")["year"].nunique()

all_iso2 = set(df["iso2"].dropna().unique())
cov_data = []

for iso2 in sorted(all_iso2):
    country_subset = df[df["iso2"] == iso2]
    if country_subset.empty:
        continue
    country = country_subset["country_name"].iloc[0]

    # Get years for each indicator
    years_total = set(df_total[df_total["iso2"] == iso2]["year"]) if iso2 in df_total["iso2"].values else set()
    years_non_gold = set(df_non_gold[df_non_gold["iso2"] == iso2]["year"]) if iso2 in df_non_gold["iso2"].values else set()

    has_total = len(years_total) > 0
    has_non_gold = len(years_non_gold) > 0

    # Intersection years (both indicators available)
    years_both = years_total & years_non_gold
    has_both = len(years_both) > 0

    if has_total or has_non_gold:
        all_years = years_total | years_non_gold
        first_year = min(all_years) if all_years else None
        last_year = max(all_years) if all_years else None
        n_years_total = len(years_total)
        n_years_non_gold = len(years_non_gold)
        n_years_both = len(years_both)

        cov_data.append({
            "iso2": iso2,
            "country_name": country,
            "has_total": has_total,
            "has_non_gold": has_non_gold,
            "has_both": has_both,
            "first_year": first_year,
            "last_year": last_year,
            "n_years_total": n_years_total,
            "n_years_non_gold": n_years_non_gold,
            "n_years_both": n_years_both,
            "n_years_total_span": last_year - first_year + 1 if first_year and last_year else 0
        })

cov_df = pd.DataFrame(cov_data)

print(f"Total economies: {len(cov_df)}")
print(f"Economies with TOTAL: {cov_df['has_total'].sum()} ({cov_df['has_total'].sum()/len(cov_df)*100:.1f}%)")
print(f"Economies with NON_GOLD: {cov_df['has_non_gold'].sum()} ({cov_df['has_non_gold'].sum()/len(cov_df)*100:.1f}%)")
print(f"Economies with BOTH (intersection): {cov_df['has_both'].sum()} ({cov_df['has_both'].sum()/len(cov_df)*100:.1f}%)")
print()

# 6) Top economies missing one indicator
print("="*80)
print("QA CHECK #6: ECONOMIES MISSING ONE INDICATOR")
print("="*80)
missing = cov_df[~cov_df["has_both"]]
print(f"Economies missing one indicator: {len(missing)}")
if len(missing) > 0:
    print("\nTop 20 economies missing one or both indicators:")
    for idx, row in missing.head(20).iterrows():
        missing_list = []
        if not row["has_total"]:
            missing_list.append("TOTAL")
        if not row["has_non_gold"]:
            missing_list.append("NON_GOLD")
        print(f"  {row['iso2']} - {row['country_name']}: missing {', '.join(missing_list)} " +
              f"(total_years={row['n_years_total']}, non_gold_years={row['n_years_non_gold']})")
else:
    print("✅ PASS: All economies have both indicators!")
print()

# 7) Year span analysis
print("="*80)
print("QA CHECK #7: YEAR SPAN ANALYSIS")
print("="*80)
print(f"Earliest year: {df['year'].min()}")
print(f"Latest year: {df['year'].max()}")
print(f"Total year span: {df['year'].max() - df['year'].min() + 1} years")
print()

print("Top 10 economies with SHORTEST history (by total years):")
shortest = cov_df.sort_values("n_years_total_span").head(10)
for idx, row in shortest.iterrows():
    print(f"  {row['iso2']} - {row['country_name']}: " +
          f"{row['n_years_total']} total years, {row['n_years_both']} both years " +
          f"({row['first_year']}-{row['last_year']})")
print()

print("Top 10 economies with LONGEST history:")
longest = cov_df.sort_values("n_years_total_span", ascending=False).head(10)
for idx, row in longest.iterrows():
    print(f"  {row['iso2']} - {row['country_name']}: " +
          f"{row['n_years_total']} total years, {row['n_years_both']} both years " +
          f"({row['first_year']}-{row['last_year']})")
print()

# 8) CSV format check
print("="*80)
print("QA CHECK #8: CSV FORMAT VALIDATION")
print("="*80)
# Read raw CSV as text to check for comma separators
import csv
with open("reserves_gold_split_wdi.csv", "r") as f:
    reader = csv.reader(f)
    header = next(reader)
    print(f"Columns: {len(header)}")
    print(f"Column names: {header}")
    print()

    # Check first 5 data rows
    print("Sample raw data (first 5 rows):")
    for i, row in enumerate(reader):
        if i >= 5:
            break
        print(f"Row {i+1}: {row}")
print()

# 9) Gold value statistics by quality flag
print("="*80)
print("QA CHECK #9: GOLD VALUE BY QUALITY FLAG")
print("="*80)
for flag in df["quality_flag"].unique():
    subset = df[df["quality_flag"] == flag]["gold_reserves_value_usd_inferred"]
    print(f"\nFlag: {flag}")
    print(f"  Count: {len(subset):,}")
    print(f"  Mean: ${subset.mean():,.0f}" if subset.mean() == subset.mean() else "  Mean: NaN")
    print(f"  Median: ${subset.median():,.0f}" if subset.median() == subset.median() else "  Median: NaN")
    print(f"  Min: ${subset.min():,.0f}" if subset.min() == subset.min() else "  Min: NaN")
    print(f"  Max: ${subset.max():,.0f}" if subset.max() == subset.max() else "  Max: NaN")
    print(f"  Negative count: {(subset < 0).sum()}")
    print(f"  Zero count: {(subset == 0).sum()}")
print()

print("="*80)
print("QA CHECK COMPLETE")
print("="*80)
