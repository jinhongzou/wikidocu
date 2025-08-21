-- 高价值用户报表（消费 > 1000 且订单数 >= 2）
CREATE TABLE IF NOT EXISTS ads_top_customers AS
SELECT
    user_name,
    region,
    total_spent,
    order_count,
    'High Value' AS customer_level
FROM dws_user_spending_summary
WHERE total_spent > 1000 AND order_count >= 2;

-- 地区销售排名报表
CREATE TABLE IF NOT EXISTS ads_region_sales_rank AS
SELECT
    region,
    total_amount,
    order_count,
    RANK() OVER (ORDER BY total_amount DESC) AS sales_rank
FROM dws_region_order_summary;