-- Run sql/analytics.sql first, e.g. via create_sql_views(connection).
-- These are worked analytical queries, not national official statistics.

-- 1. Largest observed MoM increases in the latest dataset month.
SELECT province, commodity, date, price, previous_price, ROUND(mom_pct, 2) AS mom_pct
FROM monthly_price_changes
WHERE date = (SELECT MAX(date) FROM prices) AND mom_pct IS NOT NULL
ORDER BY mom_pct DESC
LIMIT 15;

-- 2. Data coverage and missing calendar months by observed series span.
SELECT province, commodity, first_month, last_month,
       observations, expected_months,
       expected_months - observations AS missing_months,
       ROUND(coverage_pct, 2) AS coverage_pct
FROM series_coverage
ORDER BY coverage_pct, province, commodity;

-- 3. Monthly reference: unweighted mean of observed province prices for ONE
-- commodity. This is descriptive, not an official national price or CPI.
SELECT date, commodity,
       COUNT(DISTINCT province_code) AS observed_provinces,
       ROUND(AVG(price), 2) AS mean_observed_province_price,
       MIN(price) AS min_observed_province_price,
       MAX(price) AS max_observed_province_price
FROM prices
WHERE commodity = 'Beras Medium'
GROUP BY date, commodity
ORDER BY date;

-- 4. Exact-calendar YoY comparison. No previous-observation shortcut.
SELECT province, commodity, date, price, year_ago_price,
       ROUND(yoy_pct, 2) AS yoy_pct
FROM monthly_price_changes
WHERE province = 'Jawa Barat' AND commodity = 'Beras Medium'
ORDER BY date;
