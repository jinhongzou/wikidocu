-- 按地区汇总订单统计
CREATE TABLE IF NOT EXISTS dws_region_order_summary AS
SELECT
    region,
    COUNT(order_id) AS order_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MIN(order_date) AS first_order_date,
    MAX(order_date) AS last_order_date
FROM dwd_user_order_detail
GROUP BY region;

-- 按用户汇总消费情况
CREATE TABLE IF NOT EXISTS dws_user_spending_summary AS
SELECT
    user_id,
    user_name,
    region,
    COUNT(order_id) AS order_count,
    SUM(amount) AS total_spent,
    MAX(amount) AS max_single_order
FROM dwd_user_order_detail
GROUP BY user_id, user_name, region;