-- PanganWatch: reviewable SQLite analytics on prepared prices.
-- Prices contain one positive observation per province/commodity/month.
-- Missing months stay NULL. This is not a real-time or transaction database.

DROP VIEW IF EXISTS monthly_price_changes;
CREATE VIEW monthly_price_changes AS
SELECT
    p.province_code,
    p.province,
    p.commodity,
    p.date,
    p.price,
    p.unit,
    previous.price AS previous_price,
    CASE WHEN previous.price > 0
        THEN (p.price * 1.0 / previous.price - 1.0) * 100.0 END AS mom_pct,
    last_year.price AS year_ago_price,
    CASE WHEN last_year.price > 0
        THEN (p.price * 1.0 / last_year.price - 1.0) * 100.0 END AS yoy_pct
FROM prices AS p
LEFT JOIN prices AS previous
    ON previous.province_code = p.province_code
    AND previous.commodity = p.commodity
    AND previous.date = date(p.date, '-1 month')
LEFT JOIN prices AS last_year
    ON last_year.province_code = p.province_code
    AND last_year.commodity = p.commodity
    AND last_year.date = date(p.date, '-1 year');

DROP VIEW IF EXISTS series_coverage;
CREATE VIEW series_coverage AS
WITH span AS (
    SELECT
        province_code, province, commodity,
        MIN(date) AS first_month,
        MAX(date) AS last_month,
        COUNT(*) AS observations
    FROM prices
    GROUP BY province_code, province, commodity
), expected AS (
    SELECT *,
        (CAST(strftime('%Y', last_month) AS INTEGER) - CAST(strftime('%Y', first_month) AS INTEGER)) * 12
        + CAST(strftime('%m', last_month) AS INTEGER) - CAST(strftime('%m', first_month) AS INTEGER) + 1 AS expected_months
    FROM span
)
SELECT *, observations * 100.0 / expected_months AS coverage_pct
FROM expected;

-- Coverage in this view uses each series' first/last observed month.
-- The dashboard's selected-window coverage also counts missing endpoint months.

DROP VIEW IF EXISTS province_commodity_summary;
CREATE VIEW province_commodity_summary AS
SELECT
    province_code, province, commodity, unit,
    COUNT(*) AS observations,
    AVG(price) AS mean_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    CASE WHEN COUNT(*) >= 3 THEN
        MAX(0.0, (SUM(price * price) - SUM(price) * 1.0 * SUM(price) / COUNT(*)) / (COUNT(*) - 1))
    END AS sample_variance
FROM prices
GROUP BY province_code, province, commodity, unit;
